// ROCK 5B: real RKNPU2 C API -> optimized YOLOv8 NCHW 6/9 outputs -> C++ DFL/NMS.
// Input is preprocessed 640x640 RGB uint8 packed HWC RAW (not JPG/BGR).
// No camera import, RGA or DMA-BUF zero-copy: this tests model -> NPU -> C++ result.
// CLI: ./rknn_yolov8_raw yolov8.rknn letterboxed640.rgb source_width source_height [conf] [runs]
#include "rknn_api.h"
#include "yolov8_postprocess.hpp"
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <cmath>

namespace {
void ensure(int result,const char* operation){
    if(result!=RKNN_SUCC)
        throw std::runtime_error(std::string(operation)+" returned "+std::to_string(result));
}
std::vector<uint8_t> read_file(const char* filename){
    std::ifstream file(filename,std::ios::binary|std::ios::ate);
    if(!file)throw std::runtime_error(std::string("Cannot open ")+filename);
    const auto size=file.tellg();
    if(size<=0 || static_cast<uint64_t>(size)>UINT32_MAX)
        throw std::runtime_error(std::string("Invalid file size ")+filename);
    std::vector<uint8_t> content(static_cast<std::size_t>(size));
    file.seekg(0);
    if(!file.read(reinterpret_cast<char*>(content.data()),size))
        throw std::runtime_error("Failed to read input");
    return content;
}
struct Runtime {
    rknn_context context=0;
    explicit Runtime(std::vector<uint8_t>& model){
        ensure(rknn_init(&context,model.data(),uint32_t(model.size()),0,nullptr),"rknn_init");
    }
    ~Runtime(){if(context)rknn_destroy(context);}
    Runtime(const Runtime&)=delete;
    Runtime& operator=(const Runtime&)=delete;
};
struct Outputs {
    rknn_context ctx;
    std::vector<rknn_output> array;
    bool obtained=false;
    explicit Outputs(rknn_context context,int n):ctx(context),array(std::size_t(n)){
        for(int i=0;i<n;++i){array[std::size_t(i)].index=uint32_t(i);array[std::size_t(i)].want_float=1;}
    }
    void receive(){
        ensure(rknn_outputs_get(ctx,uint32_t(array.size()),array.data(),nullptr),
               "rknn_outputs_get");
        obtained=true;
    }
    ~Outputs(){if(obtained)rknn_outputs_release(ctx,uint32_t(array.size()),array.data());}
    Outputs(const Outputs&)=delete;Outputs& operator=(const Outputs&)=delete;
};
struct Head {
    rknn_tensor_attr attr{};
};
std::vector<Head> validate_model(rknn_context ctx){
    rknn_input_output_num num{};
    ensure(rknn_query(ctx,RKNN_QUERY_IN_OUT_NUM,&num,sizeof(num)),"query counts");
    if(num.n_input!=1 || (num.n_output!=9 && num.n_output!=6))
        throw std::runtime_error("Only 1 input / 6 or 9 output optimized YOLOv8 model is supported");
    rknn_tensor_attr input{};
    input.index=0;
    ensure(rknn_query(ctx,RKNN_QUERY_INPUT_ATTR,&input,sizeof(input)),"query input");
    if(input.n_elems!=640u*640u*3u || input.type!=RKNN_TENSOR_UINT8)
        throw std::runtime_error("Expected uint8 640x640 RGB input model (check RKNN conversion)");
    // Conversion is explicit: rknn_inputs_set supplies NHWC; output buffers queried in NCHW.
    std::vector<Head> heads(num.n_output);
    const int spacing=int(num.n_output/3);
    for(unsigned i=0;i<num.n_output;++i){
        auto& attr=heads[i].attr;
        attr.index=i;
        ensure(rknn_query(ctx,RKNN_QUERY_OUTPUT_ATTR,&attr,sizeof(attr)),"query output");
        const int grid=i<static_cast<unsigned>(spacing)?80:
                       (i<static_cast<unsigned>(2*spacing)?40:20);
        const int kind=int(i)%spacing;
        const int channel=kind==0?64:(kind==1?80:1);
        if(attr.n_dims!=4 || attr.fmt!=RKNN_TENSOR_NCHW ||
           attr.dims[0]!=1 || attr.dims[1]!=uint32_t(channel) ||
           attr.dims[2]!=uint32_t(grid) || attr.dims[3]!=uint32_t(grid))
            throw std::runtime_error("Output tensor "+std::to_string(i)+
                                     " format/shape is NOT Model Zoo optimized NCHW; "
                                     "do not guess tensor order");
    }
    return heads;
}
int parse_int(const char* text,int lo,int hi){
    const int number=std::stoi(text);
    if(number<lo||number>hi)throw std::invalid_argument("Invalid integer argument");
    return number;
}
void print_json(const std::vector<rk_yolo::Detection>& detections,
                int runs,double mean_ms){
    std::cout<<std::fixed<<std::setprecision(7);
    std::cout<<"{\"backend\":\"rknpu2-c-api\",\"runs\":"<<runs
             <<",\"mean_inference_and_fetch_ms\":"<<mean_ms
             <<",\"detections\":[";
    for(std::size_t i=0;i<detections.size();++i){
        const auto& d=detections[i];
        if(i)std::cout<<",";
        std::cout<<"{\"class_id\":"<<d.class_id<<",\"score\":"<<d.score
                 <<",\"xyxy\":["<<d.x1<<","<<d.y1<<","<<d.x2<<","<<d.y2<<"]}";
    }
    std::cout<<"]}\n";
}
} // namespace

int main(int argc,char** argv){
    if(argc<5||argc>7){
        std::cerr<<"Usage: "<<argv[0]
                 <<" model.rknn letterbox_rgb_640x640.raw source_width source_height"
                   " [confidence=.25] [runs=5]\n";
        return 2;
    }
    try{
        auto model=read_file(argv[1]);
        auto raw=read_file(argv[2]);
        if(raw.size()!=640u*640u*3u)
            throw std::runtime_error("Input must be packed RGB uint8 640x640x3 RAW");
        const int w=parse_int(argv[3],1,32768),h=parse_int(argv[4],1,32768);
        rk_yolo::Options options{};
        if(argc>5)options.conf_threshold=std::stof(argv[5]);
        const int runs=argc>6?parse_int(argv[6],1,10000):5;
        Runtime runtime(model);
        const auto attrs=validate_model(runtime.context);
        rknn_input input{};
        input.index=0;input.buf=raw.data();input.size=uint32_t(raw.size());
        input.type=RKNN_TENSOR_UINT8;input.fmt=RKNN_TENSOR_NHWC;
        input.pass_through=0;
        const auto mapping=rk_yolo::black_letterbox_mapping(w,h,640);
        double sum_ms=0;
        std::vector<rk_yolo::Detection> result;
        for(int n=0;n<runs;++n){
            ensure(rknn_inputs_set(runtime.context,1,&input),"rknn_inputs_set");
            const auto start=std::chrono::steady_clock::now();
            ensure(rknn_run(runtime.context,nullptr),"rknn_run");
            Outputs out(runtime.context,int(attrs.size()));
            out.receive();
            const auto end=std::chrono::steady_clock::now();
            sum_ms+=std::chrono::duration<double,std::milli>(end-start).count();
            std::vector<rk_yolo::Tensor> tensors;
            tensors.reserve(attrs.size());
            for(std::size_t k=0;k<attrs.size();++k){
                const auto& a=attrs[k].attr;
                if(out.array[k].buf==nullptr ||
                   out.array[k].size!=a.n_elems*sizeof(float))
                    throw std::runtime_error("Dequantized output buffer size mismatch at "+
                                             std::to_string(k));
                tensors.push_back({
                    static_cast<const float*>(out.array[k].buf),
                    a.n_elems,int(a.dims[1]),int(a.dims[2]),int(a.dims[3])});
            }
            result=rk_yolo::decode(tensors,mapping,options);
            // out destructor releases all SDK buffers after decoder returns.
        }
        print_json(result,runs,sum_ms/runs);
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"ERROR: "<<e.what()<<"\n";
        return 1;
    }
}
