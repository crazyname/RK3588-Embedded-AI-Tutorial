// 第26讲：RKNPU2 C API zero-copy memory binding and inference.
// Build with a matching RK3588 SDK. Input file: uint8 NHWC, pre-padded to
// native_input.size_with_stride according to SDK query, not an ordinary JPEG.
// RUN ON RK3588 ONLY.  See examples/notes/lesson_26.md.
#include "rknn_api.h"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::vector<unsigned char> read_file(const std::string& path) {
    std::ifstream stream(path,std::ios::binary|std::ios::ate);
    if(!stream) throw std::runtime_error("Cannot open: "+path);
    const std::streamoff bytes=stream.tellg();
    if(bytes<=0)throw std::runtime_error("Empty input file: "+path);
    std::vector<unsigned char> data(static_cast<size_t>(bytes));
    stream.seekg(0);
    if(!stream.read(reinterpret_cast<char*>(data.data()),bytes))
        throw std::runtime_error("Read failed: "+path);
    return data;
}

struct RknnResources {
    rknn_context ctx=0;
    rknn_tensor_mem* input=nullptr;
    rknn_tensor_mem* output=nullptr;
    ~RknnResources(){
        if(input) rknn_destroy_mem(ctx,input);
        if(output) rknn_destroy_mem(ctx,output);
        if(ctx) rknn_destroy(ctx);
    }
    RknnResources(const RknnResources&)=delete;
    RknnResources& operator=(const RknnResources&)=delete;
    RknnResources()=default;
};
static void ensure(int rc,const char* operation){
    if(rc != RKNN_SUCC) throw std::runtime_error(std::string(operation)+" error="+std::to_string(rc));
}
int main(int argc,char** argv){
    if(argc<3 || argc>4){
        std::cerr << "Usage: "<<argv[0]<<" model.rknn padded_uint8_nhwc.raw [runs=5]\n";
        return 2;
    }
    try{
        int runs=argc==4?std::stoi(argv[3]):5;
        if(runs<1 || runs>10000)throw std::runtime_error("runs must be 1..10000");
        auto model_bytes=read_file(argv[1]);
        auto raw=read_file(argv[2]);
        RknnResources resource;
        ensure(rknn_init(&resource.ctx,model_bytes.data(),
               static_cast<uint32_t>(model_bytes.size()),0,nullptr),"rknn_init");
        rknn_input_output_num num{};
        ensure(rknn_query(resource.ctx,RKNN_QUERY_IN_OUT_NUM,&num,sizeof(num)),"query_io");
        if(num.n_input!=1 || num.n_output!=1)
            throw std::runtime_error("This tutorial requires exactly one input and one output");
        rknn_tensor_attr inp{};
        inp.index=0;
        ensure(rknn_query(resource.ctx,RKNN_QUERY_INPUT_ATTR,&inp,sizeof(inp)),"query input");
        rknn_tensor_attr native{};
        native.index=0;
        ensure(rknn_query(resource.ctx,RKNN_QUERY_NATIVE_INPUT_ATTR,&native,sizeof(native)),
               "query native input");
        rknn_tensor_attr out{};
        out.index=0;
        ensure(rknn_query(resource.ctx,RKNN_QUERY_OUTPUT_ATTR,&out,sizeof(out)),"query output");
        if(inp.n_dims!=4 || inp.n_elems==0 || out.n_elems==0)
            throw std::runtime_error("Expected 4D image classifier input and nonempty output");
        // Restrict to 8-bit RGB NHWC input so bytes are meaningful and unambiguous.
        const auto aligned_size=native.size_with_stride?native.size_with_stride:native.size;
        if(!aligned_size || raw.size()!=aligned_size)
            throw std::runtime_error("raw tensor size != native size_with_stride="+
                                     std::to_string(aligned_size));
        inp.type=RKNN_TENSOR_UINT8;
        inp.fmt=RKNN_TENSOR_NHWC;
        inp.pass_through=0;
        resource.input=rknn_create_mem(resource.ctx,aligned_size);
        if(!resource.input || !resource.input->virt_addr)
            throw std::runtime_error("rknn_create_mem input failed");
        std::memcpy(resource.input->virt_addr,raw.data(),raw.size());
        ensure(rknn_set_io_mem(resource.ctx,resource.input,&inp),"rknn_set_io_mem(input)");
        out.type=RKNN_TENSOR_FLOAT32;
        out.fmt=RKNN_TENSOR_NCHW;
        const auto output_bytes=static_cast<uint32_t>(out.n_elems*sizeof(float));
        resource.output=rknn_create_mem(resource.ctx,output_bytes);
        if(!resource.output || !resource.output->virt_addr)
            throw std::runtime_error("rknn_create_mem output failed");
        ensure(rknn_set_io_mem(resource.ctx,resource.output,&out),"rknn_set_io_mem(output)");
        std::vector<double> times;
        for(int n=0;n<runs;++n){
            const auto begin=std::chrono::steady_clock::now();
            ensure(rknn_run(resource.ctx,nullptr),"rknn_run");
            const auto end=std::chrono::steady_clock::now();
            const double ms=std::chrono::duration<double,std::milli>(end-begin).count();
            times.push_back(ms);
        }
        const float* ptr=static_cast<const float*>(resource.output->virt_addr);
        for(size_t i=0;i<std::min<size_t>(out.n_elems,10);++i){
            std::cout<<"output["<<i<<"]="<<ptr[i]<<"\n";
        }
        double total=0.0;
        for(double value:times)total+=value;
        std::cout<<"NPU rknn_run mean ms="<<(total/times.size())
                 <<" runs="<<runs<<"\n";
        std::cout<<"This is SDK-owned zero-copy I/O memory binding. Input staging memcpy"
                    " is excluded from the measured rknn_run call.\n";
        return 0;
    }catch(const std::exception& exc){
        std::cerr<<"ERROR: "<<exc.what()<<"\n";
        return 1;
    }
}
