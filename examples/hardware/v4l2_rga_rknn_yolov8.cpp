// ROCK 5B: actual YUYV V4L2 camera DMA-BUF export -> RGA fd import
// -> RGB conversion + resize -> CPU black-letterbox -> rknn_inputs_set
// -> real RKNPU2 optimized YOLOv8 NCHW 9-output DFL/NMS.
// IMPORTANT: CPU letterbox memcpy and rknn_inputs_set remain. NOT NPU zero-copy.
// Only single-planar YUYV, tightly packed stride, 640x640 RGB input model.
// CLI: ./v4l2_rga_rknn_yolov8 model.rknn /dev/video0 640 480 30 [conf=.25]
#include <cstddef>
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include "rknn_api.h"
#include "im2d.hpp"
#include "yolov8_postprocess.hpp"

namespace {
using Clock=std::chrono::steady_clock;
double ms(Clock::time_point a,Clock::time_point b){
    return std::chrono::duration<double,std::milli>(b-a).count();
}
int parse(const char* word,int lo,int hi) {
    int v=std::stoi(word);
    if(v<lo||v>hi)throw std::invalid_argument("Numeric argument out of bounds");
    return v;
}
void sdk(int rc,const char* op){
    if(rc!=RKNN_SUCC)throw std::runtime_error(std::string(op)+" returned "+std::to_string(rc));
}
void ioctl_checked(int fd,unsigned long command,void* arg,const char* action){
    int rc;
    do{rc=::ioctl(fd,command,arg);}while(rc<0&&errno==EINTR);
    if(rc<0)throw std::runtime_error(std::string(action)+": "+std::strerror(errno));
}
void rga_checked(IM_STATUS rc,const char* action){
    if(rc!=IM_STATUS_SUCCESS && rc!=IM_STATUS_NOERROR)
        throw std::runtime_error(std::string(action)+": "+imStrError(rc));
}
std::vector<uint8_t> read_model(const char* filename){
    std::ifstream file(filename,std::ios::binary|std::ios::ate);
    if(!file)throw std::runtime_error("Cannot open RKNN model");
    auto length=file.tellg();
    if(length<=0||uint64_t(length)>UINT32_MAX)
        throw std::runtime_error("Invalid RKNN model file size");
    std::vector<uint8_t> data(std::size_t(length),uint8_t{0});
    file.seekg(0);
    if(!file.read(reinterpret_cast<char*>(data.data()),length))
        throw std::runtime_error("Cannot read model");
    return data;
}
struct RgaHandle {
    rga_buffer_handle_t handle=0;
    RgaHandle()=default;
    explicit RgaHandle(rga_buffer_handle_t h):handle(h){
        if(!h)throw std::runtime_error("RGA buffer import failed");
    }
    ~RgaHandle(){if(handle)releasebuffer_handle(handle);}
    RgaHandle(const RgaHandle&)=delete;
    RgaHandle& operator=(const RgaHandle&)=delete;
};
struct Slot {
    void* ptr=MAP_FAILED;
    std::size_t length=0;
    int dma_fd=-1;
    std::unique_ptr<RgaHandle> rga;
    ~Slot(){
        rga.reset();
        if(dma_fd>=0)::close(dma_fd);
        if(ptr!=MAP_FAILED)::munmap(ptr,length);
    }
};
struct Capture {
    int fd=-1;
    bool streaming=false;
    bool allocated=false;
    int width=0, height=0;
    std::vector<std::unique_ptr<Slot>> slots;
    Capture(const char* path,int requested_width,int requested_height){
        fd=::open(path,O_RDWR|O_NONBLOCK|O_CLOEXEC);
        if(fd<0)throw std::runtime_error(std::string("Cannot open camera: ")+std::strerror(errno));
        try{
            v4l2_capability cap{};
            ioctl_checked(fd,VIDIOC_QUERYCAP,&cap,"VIDIOC_QUERYCAP");
            const auto flags=(cap.capabilities&V4L2_CAP_DEVICE_CAPS)
                             ?cap.device_caps:cap.capabilities;
            if(!(flags&V4L2_CAP_VIDEO_CAPTURE) || !(flags&V4L2_CAP_STREAMING))
                throw std::runtime_error("Camera must support single-planar streaming capture");
            v4l2_format fmt{};
            fmt.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            fmt.fmt.pix.width=requested_width;
            fmt.fmt.pix.height=requested_height;
            fmt.fmt.pix.pixelformat=V4L2_PIX_FMT_YUYV;
            fmt.fmt.pix.field=V4L2_FIELD_ANY;
            ioctl_checked(fd,VIDIOC_S_FMT,&fmt,"VIDIOC_S_FMT(YUYV)");
            width=int(fmt.fmt.pix.width);height=int(fmt.fmt.pix.height);
            if(fmt.fmt.pix.pixelformat!=V4L2_PIX_FMT_YUYV ||
               width!=requested_width||height!=requested_height||
               width%2 || fmt.fmt.pix.bytesperline!=uint32_t(width*2) ||
               fmt.fmt.pix.sizeimage<uint32_t(width*height*2))
                throw std::runtime_error("Driver did not negotiate tight single-planar YUYV; "
                                         "MJPG, stride padding and alternate resolutions not supported");
            v4l2_requestbuffers count{};
            count.count=3;count.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            count.memory=V4L2_MEMORY_MMAP;
            ioctl_checked(fd,VIDIOC_REQBUFS,&count,"VIDIOC_REQBUFS");
            allocated=true;
            if(count.count<2)throw std::runtime_error("Need at least 2 capture buffers");
            for(uint32_t k=0;k<count.count;++k){
                auto slot=std::make_unique<Slot>();
                v4l2_buffer buffer{};
                buffer.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
                buffer.memory=V4L2_MEMORY_MMAP;buffer.index=k;
                ioctl_checked(fd,VIDIOC_QUERYBUF,&buffer,"VIDIOC_QUERYBUF");
                slot->length=buffer.length;
                if(slot->length<uint32_t(width*height*2))
                    throw std::runtime_error("Capture buffer too small");
                slot->ptr=::mmap(nullptr,slot->length,PROT_READ|PROT_WRITE,
                                 MAP_SHARED,fd,buffer.m.offset);
                if(slot->ptr==MAP_FAILED)
                    throw std::runtime_error("V4L2 mmap failed");
                v4l2_exportbuffer export_buf{};
                export_buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
                export_buf.index=k;export_buf.plane=0;export_buf.flags=O_CLOEXEC;
                ioctl_checked(fd,VIDIOC_EXPBUF,&export_buf,"VIDIOC_EXPBUF");
                slot->dma_fd=export_buf.fd;
                slot->rga=std::make_unique<RgaHandle>(
                    importbuffer_fd(slot->dma_fd,int(slot->length)));
                slots.push_back(std::move(slot));
            }
            for(uint32_t k=0;k<count.count;++k)queue(k);
            auto type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            ioctl_checked(fd,VIDIOC_STREAMON,&type,"VIDIOC_STREAMON");
            streaming=true;
        }catch(...){cleanup();throw;}
    }
    void queue(uint32_t index){
        v4l2_buffer buffer{};
        buffer.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buffer.memory=V4L2_MEMORY_MMAP;buffer.index=index;
        ioctl_checked(fd,VIDIOC_QBUF,&buffer,"VIDIOC_QBUF");
    }
    v4l2_buffer next(){
        pollfd descriptor{};
        descriptor.fd=fd;descriptor.events=POLLIN;
        int rc;
        do{rc=::poll(&descriptor,1,3000);}while(rc<0&&errno==EINTR);
        if(rc<=0||!(descriptor.revents&POLLIN))
            throw std::runtime_error("V4L2 frame timeout or poll error");
        v4l2_buffer buffer{};
        buffer.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buffer.memory=V4L2_MEMORY_MMAP;
        ioctl_checked(fd,VIDIOC_DQBUF,&buffer,"VIDIOC_DQBUF");
        if(buffer.index>=slots.size() ||
           buffer.bytesused<uint32_t(width*height*2))
            throw std::runtime_error("Invalid dequeued frame/index/bytesused");
        return buffer;
    }
    void cleanup(){
        if(fd<0)return;
        if(streaming){
            auto type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            ::ioctl(fd,VIDIOC_STREAMOFF,&type);
            streaming=false;
        }
        slots.clear(); // release RGA handles, dma-fds and mmap before REQBUFS(0)
        if(allocated){
            v4l2_requestbuffers zero{};
            zero.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            zero.memory=V4L2_MEMORY_MMAP;
            zero.count=0;
            ::ioctl(fd,VIDIOC_REQBUFS,&zero);
            allocated=false;
        }
        ::close(fd);fd=-1;
    }
    ~Capture(){cleanup();}
    Capture(const Capture&)=delete;
    Capture& operator=(const Capture&)=delete;
};
struct Runtime {
    rknn_context ctx=0;
    unsigned count=0;
    Runtime(std::vector<uint8_t>& model){
        sdk(rknn_init(&ctx,model.data(),uint32_t(model.size()),0,nullptr),"rknn_init");
        try{
        rknn_input_output_num n{};
        sdk(rknn_query(ctx,RKNN_QUERY_IN_OUT_NUM,&n,sizeof(n)),"query counts");
        if(n.n_input!=1||(n.n_output!=9 && n.n_output!=6))
            throw std::runtime_error("Optimized YOLOv8 must have 1 input, 6 or 9 outputs");
        count=n.n_output;
        rknn_tensor_attr input{};input.index=0;
        sdk(rknn_query(ctx,RKNN_QUERY_INPUT_ATTR,&input,sizeof(input)),"query input");
        if(input.type!=RKNN_TENSOR_UINT8 || input.n_elems!=640u*640u*3u)
            throw std::runtime_error("Expected uint8 640x640x3 model");
        const unsigned stride=count/3;
        for(unsigned k=0;k<count;++k){
            rknn_tensor_attr attr{};attr.index=k;
            sdk(rknn_query(ctx,RKNN_QUERY_OUTPUT_ATTR,&attr,sizeof(attr)),"query output");
            const int grid=k/stride==0?80:k/stride==1?40:20;
            const int channels=k%stride==0?64:k%stride==1?80:1;
            if(attr.fmt!=RKNN_TENSOR_NCHW || attr.n_dims!=4 ||
               attr.dims[0]!=1 || attr.dims[1]!=uint32_t(channels) ||
               attr.dims[2]!=uint32_t(grid)||attr.dims[3]!=uint32_t(grid))
                throw std::runtime_error("Unsupported output shape/layout at "+std::to_string(k));
        }
        }catch(...){
            // A failed constructor never calls Runtime::~Runtime; clean context explicitly.
            if(ctx){rknn_destroy(ctx);ctx=0;}
            throw;
        }
    }
    ~Runtime(){if(ctx)rknn_destroy(ctx);}
    Runtime(const Runtime&)=delete;Runtime& operator=(const Runtime&)=delete;
    std::vector<rk_yolo::Detection> run(std::vector<uint8_t>& input,
                                       const rk_yolo::ImageMapping& map,float conf){
        rknn_input arg{};
        arg.index=0;arg.buf=input.data();arg.size=uint32_t(input.size());
        arg.type=RKNN_TENSOR_UINT8;arg.fmt=RKNN_TENSOR_NHWC;arg.pass_through=0;
        sdk(rknn_inputs_set(ctx,1,&arg),"rknn_inputs_set");
        sdk(rknn_run(ctx,nullptr),"rknn_run");
        std::vector<rknn_output> outputs(count);
        for(unsigned k=0;k<count;++k){outputs[k].index=k;outputs[k].want_float=1;}
        sdk(rknn_outputs_get(ctx,count,outputs.data(),nullptr),"rknn_outputs_get");
        bool released=false;
        try{
            std::vector<rk_yolo::Tensor> tensors;
            tensors.reserve(count);
            for(unsigned k=0;k<count;++k){
                const int grid=k/(count/3)==0?80:k/(count/3)==1?40:20;
                const int channels=k%(count/3)==0?64:k%(count/3)==1?80:1;
                const auto expected=std::size_t(channels)*grid*grid;
                if(!outputs[k].buf||outputs[k].size!=expected*sizeof(float))
                    throw std::runtime_error("Unexpected dequantized output buffer length");
                tensors.push_back({static_cast<const float*>(outputs[k].buf),
                                   expected,channels,grid,grid});
            }
            rk_yolo::Options options{};
            options.conf_threshold=conf;
            auto result=rk_yolo::decode(tensors,map,options);
            // Release only once: a release failure must not trigger a second release.
            const int release_status=rknn_outputs_release(ctx,count,outputs.data());
            released=true;
            sdk(release_status,"rknn_outputs_release");
            return result;
        }catch(...){
            if(!released)rknn_outputs_release(ctx,count,outputs.data());
            throw;
        }
    }
};
struct RgaProcessor {
    std::vector<uint8_t> converted,resized,packed;
    std::unique_ptr<RgaHandle> converted_handle,resized_handle;
    int width,height,scaled_width,scaled_height,left,top;
    RgaProcessor(int w,int h):converted(std::size_t(w)*h*3),
        resized(1),packed(640u*640u*3u,0),width(w),height(h){
        const auto meta=rk_yolo::black_letterbox_mapping(w,h,640);
        scaled_width=int(std::nearbyint(w*meta.scale_x));
        scaled_height=int(std::nearbyint(h*meta.scale_y));
        left=meta.pad_x;top=meta.pad_y;
        resized.resize(std::size_t(scaled_width)*scaled_height*3);
        converted_handle=std::make_unique<RgaHandle>(
            importbuffer_virtualaddr(converted.data(),int(converted.size())));
        resized_handle=std::make_unique<RgaHandle>(
            importbuffer_virtualaddr(resized.data(),int(resized.size())));
    }
    std::vector<uint8_t>& transform(rga_buffer_handle_t camera_fd_handle){
        const auto yuv=wrapbuffer_handle(camera_fd_handle,width,height,RK_FORMAT_YUYV_422);
        const auto rgb=wrapbuffer_handle(converted_handle->handle,width,height,RK_FORMAT_RGB_888);
        // sync=1: wait for RGA before re-queuing source buffer to V4L2.
        rga_checked(imcvtcolor(yuv,rgb,RK_FORMAT_YUYV_422,RK_FORMAT_RGB_888),
                    "RGA YUYV->RGB");
        const auto dst=wrapbuffer_handle(resized_handle->handle,
                                         scaled_width,scaled_height,RK_FORMAT_RGB_888);
        rga_checked(imresize(rgb,dst),"RGA RGB resize");
        std::fill(packed.begin(),packed.end(),uint8_t{0});
        for(int y=0;y<scaled_height;++y){
            const auto* row=resized.data()+std::size_t(y)*scaled_width*3;
            auto* to=packed.data()+(std::size_t(y+top)*640+left)*3;
            std::memcpy(to,row,std::size_t(scaled_width)*3);
        }
        return packed;
    }
};
void print(std::size_t frame,double capture_ms,double prep_ms,double infer_ms,
           const std::vector<rk_yolo::Detection>& hits){
    std::cout<<std::fixed<<std::setprecision(5)
             <<"{\"frame\":"<<frame<<",\"capture_ms\":"<<capture_ms
             <<",\"rga_plus_cpu_letterbox_ms\":"<<prep_ms
             <<",\"inference_and_decode_ms\":"<<infer_ms
             <<",\"detections\":[";
    for(std::size_t i=0;i<hits.size();++i){
        if(i)std::cout<<",";
        const auto& d=hits[i];
        std::cout<<"{\"class_id\":"<<d.class_id<<",\"score\":"<<d.score
                 <<",\"xyxy\":["<<d.x1<<","<<d.y1<<","<<d.x2<<","<<d.y2<<"]}";
    }
    std::cout<<"]}\n";
}
} // namespace

int main(int argc,char** argv){
    if(argc==2 && std::string(argv[1])=="--help"){
        std::cout<<"Usage: "<<argv[0]
                 <<" yolov8.rknn /dev/videoX width height frames [confidence=.25]\n"
                 <<"Requires V4L2 YUYV MMAP/EXPBUF, RGA fd import, RKNPU2 SDK.\n"
                 <<"RGA source DMA-BUF import is real; CPU pad and RKNN input copy remain.\n";
        return 0;
    }
    if(argc!=6&&argc!=7){
        std::cerr<<"Usage: "<<argv[0]
                 <<" yolov8.rknn /dev/videoX width height frames [confidence=.25]\n";
        return 2;
    }
    try{
        const int w=parse(argv[3],32,4096),h=parse(argv[4],32,4096);
        const int frames=parse(argv[5],1,100000);
        const float conf=argc==7?std::stof(argv[6]):.25f;
        if(!std::isfinite(conf)||conf<0||conf>1)
            throw std::invalid_argument("Confidence must be 0..1");
        auto model=read_model(argv[1]);
        Runtime npu(model);
        Capture camera(argv[2],w,h);
        RgaProcessor prep(w,h);
        const auto map=rk_yolo::black_letterbox_mapping(w,h,640);
        std::cerr<<"Camera "<<w<<"x"<<h<<" YUYV, MMAP DMA-BUF fd -> RGA, "
                 <<"CPU letterbox -> rknn_inputs_set (NOT zero-copy NPU)\n";
        const auto begin=Clock::now();
        for(int i=0;i<frames;++i){
            auto t0=Clock::now();
            auto frame=camera.next();
            auto t1=Clock::now();
            // RGA completes synchronously before buffer goes back into V4L2 queue.
            auto& rgb=prep.transform(camera.slots[frame.index]->rga->handle);
            auto t2=Clock::now();
            camera.queue(frame.index);
            auto results=npu.run(rgb,map,conf);
            auto t3=Clock::now();
            print(std::size_t(i+1),ms(t0,t1),ms(t1,t2),ms(t2,t3),results);
        }
        const double total=ms(begin,Clock::now())/1000;
        std::cerr<<std::fixed<<std::setprecision(3)<<"frames="<<frames
                 <<" elapsed_s="<<total
                 <<" loop_fps="<<(total>0?frames/total:0)<<"\n";
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"ERROR: "<<e.what()<<"\n";
        return 1;
    }
}
