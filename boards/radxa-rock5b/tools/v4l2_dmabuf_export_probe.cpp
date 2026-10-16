// ROCK 5B V4L2 camera MMAP-buffer -> DMA-BUF FD export preflight.
// This is a capability probe: it does NOT capture frames or bind any fd to RGA/NPU.
// V4L2 exporter: VIDIOC_REQBUFS(memory=MMAP) + VIDIOC_EXPBUF.
// This is DIFFERENT from V4L2_MEMORY_DMABUF (importing externally allocated buffers).
// Build: g++ -std=c++17 -Wall -Wextra -Werror -O2 v4l2_dmabuf_export_probe.cpp -o v4l2_dma_probe
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
class File {
public:
    explicit File(int fd=-1):fd_(fd){}
    ~File(){if(fd_>=0)::close(fd_);}
    File(const File&)=delete;File& operator=(const File&)=delete;
    int get()const{return fd_;}
private:
    int fd_;
};
void request(int fd,unsigned long command,void* arg,const char* name) {
    int result;
    do{result=::ioctl(fd,command,arg);}while(result<0&&errno==EINTR);
    if(result<0)throw std::runtime_error(std::string(name)+": "+std::strerror(errno));
}
struct Buffers {
    int fd=-1;
    bool active=false;
    std::vector<int> exported;
    ~Buffers(){
        for(int handle:exported)if(handle>=0)::close(handle);
        if(active){
            v4l2_requestbuffers req{};
            req.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            req.memory=V4L2_MEMORY_MMAP;
            req.count=0;
            // Release failure is a diagnostic, not a reason to leak file descriptors.
            ::ioctl(fd,VIDIOC_REQBUFS,&req);
        }
    }
};
std::string fourcc(uint32_t code){
    char text[5]={char(code&0xff),char((code>>8)&0xff),
                  char((code>>16)&0xff),char((code>>24)&0xff),0};
    return std::string(text);
}
} // namespace

int main(int argc,char** argv){
    if(argc!=2){
        std::cerr<<"Usage: "<<argv[0]<<" /dev/videoX\n"
                 <<"Checks whether a single-planar VIDEO_CAPTURE device can export "
                   "MMAP capture buffers as DMA-BUF FDs. No frames are captured.\n";
        return argc==2?0:2;
    }
    if(std::string(argv[1])=="--help"){
        std::cout<<"Usage: "<<argv[0]<<" /dev/videoX\n"
                   "Uses VIDIOC_REQBUFS(MMAP), VIDIOC_EXPBUF, then closes FDs. "
                   "No streaming and no end-to-end zero-copy.\n";
        return 0;
    }
    try{
        File dev(::open(argv[1],O_RDWR|O_NONBLOCK|O_CLOEXEC));
        if(dev.get()<0)throw std::runtime_error(
                std::string("Cannot open camera: ")+std::strerror(errno));
        v4l2_capability capability{};
        request(dev.get(),VIDIOC_QUERYCAP,&capability,"VIDIOC_QUERYCAP");
        const auto caps=(capability.capabilities&V4L2_CAP_DEVICE_CAPS)
                        ?capability.device_caps:capability.capabilities;
        if(!(caps&V4L2_CAP_VIDEO_CAPTURE)||!(caps&V4L2_CAP_STREAMING))
            throw std::runtime_error("Requires single-planar capture and streaming; "
                                     "not VIDEO_CAPTURE_MPLANE or codec-only node");
        v4l2_format format{};
        format.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        request(dev.get(),VIDIOC_G_FMT,&format,"VIDIOC_G_FMT");
        Buffers bufs;
        bufs.fd=dev.get();
        v4l2_requestbuffers req{};
        req.count=2;
        req.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        req.memory=V4L2_MEMORY_MMAP;
        request(dev.get(),VIDIOC_REQBUFS,&req,"VIDIOC_REQBUFS(MMAP)");
        bufs.active=true;
        if(req.count<1)
            throw std::runtime_error("Camera did not allocate any MMAP buffers");
        for(uint32_t i=0;i<req.count;++i){
            v4l2_buffer buf{};
            buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory=V4L2_MEMORY_MMAP;
            buf.index=i;
            request(dev.get(),VIDIOC_QUERYBUF,&buf,"VIDIOC_QUERYBUF");
            v4l2_exportbuffer export_buffer{};
            export_buffer.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            export_buffer.index=i;
            export_buffer.plane=0;
            export_buffer.flags=O_CLOEXEC;
            request(dev.get(),VIDIOC_EXPBUF,&export_buffer,"VIDIOC_EXPBUF");
            if(export_buffer.fd<0)
                throw std::runtime_error("VIDIOC_EXPBUF returned invalid fd");
            bufs.exported.push_back(export_buffer.fd);
        }
        std::cout<<"{\"status\":\"dmabuf-export-supported\","
                 <<"\"device\":\""<<argv[1]<<"\","
                 <<"\"fourcc\":\""<<fourcc(format.fmt.pix.pixelformat)<<"\","
                 <<"\"width\":"<<format.fmt.pix.width<<","
                 <<"\"height\":"<<format.fmt.pix.height<<","
                 <<"\"bytesperline\":"<<format.fmt.pix.bytesperline<<","
                 <<"\"buffer_count\":"<<bufs.exported.size()<<","
                 <<"\"frames_captured\":0,"
                 <<"\"npu_inference_executed\":false,"
                 <<"\"rga_processing_executed\":false}\n";
        // All exported FDs are closed before exit; no cross-process file descriptor promise.
        return 0;
    }catch(const std::exception& exc){
        std::cerr<<"ERROR: "<<exc.what()<<"\n";
        return 1;
    }
}
