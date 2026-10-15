// RK3588 RKNPU2 classifier inference from a PREPROCESSED RAW input tensor.
// Input is NOT a JPG: supply bytes matching rknn_query's input size/type/layout.
// See examples/README.md for how to build and prepare data.
#include "rknn_api.h"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

static std::vector<uint8_t> read_binary(const char* path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) throw std::runtime_error(std::string("Cannot open ")+path);
    const auto length=file.tellg();
    if (length<=0) throw std::runtime_error("File is empty");
    std::vector<uint8_t> data(static_cast<size_t>(length));
    file.seekg(0);
    if (!file.read(reinterpret_cast<char*>(data.data()),length))
        throw std::runtime_error("File read failed");
    return data;
}

// The model byte vector in main stays alive for the context lifetime.
class RknnContext {
 public:
    explicit RknnContext(std::vector<uint8_t>& model) {
        int rc=rknn_init(&ctx_,model.data(),static_cast<uint32_t>(model.size()),0,nullptr);
        if (rc!=RKNN_SUCC) throw std::runtime_error("rknn_init failed "+std::to_string(rc));
    }
    ~RknnContext(){if(ctx_)rknn_destroy(ctx_);}
    RknnContext(const RknnContext&)=delete;
    RknnContext& operator=(const RknnContext&)=delete;
    rknn_context get()const{return ctx_;}
 private:
    rknn_context ctx_=0;
};

int main(int argc,char** argv){
    if(argc!=3){
        std::cerr<<"Usage: "<<argv[0]<<" model.rknn input_tensor.raw\n"
                 <<"Input tensor must be preprocessed according to the model.\n";
        return 2;
    }
    try {
        auto model=read_binary(argv[1]);
        auto bytes=read_binary(argv[2]);
        RknnContext runtime(model);
        const auto ctx=runtime.get();
        rknn_input_output_num counts{};
        int rc=rknn_query(ctx,RKNN_QUERY_IN_OUT_NUM,&counts,sizeof(counts));
        if(rc!=RKNN_SUCC)throw std::runtime_error("query io "+std::to_string(rc));
        if(counts.n_input!=1||counts.n_output!=1)
            throw std::runtime_error("Only one-input, one-output classification models supported");
        rknn_tensor_attr input{};
        input.index=0;
        rc=rknn_query(ctx,RKNN_QUERY_INPUT_ATTR,&input,sizeof(input));
        if(rc!=RKNN_SUCC)throw std::runtime_error("query input "+std::to_string(rc));
        rknn_tensor_attr output_attr{};
        output_attr.index=0;
        rc=rknn_query(ctx,RKNN_QUERY_OUTPUT_ATTR,&output_attr,sizeof(output_attr));
        if(rc!=RKNN_SUCC)throw std::runtime_error("query output "+std::to_string(rc));
        std::cerr<<"Input: byte size="<<input.size<<" dtype="<<input.type
                 <<" layout="<<input.fmt<<" shape=";
        for(uint32_t i=0;i<input.n_dims;++i)std::cerr<<input.dims[i]<<" ";
        std::cerr<<"\n";
        if(bytes.size()!=input.size)
            throw std::runtime_error("Raw file size differs from model's queried byte size");
        rknn_input r_input{};
        r_input.index=0;
        r_input.buf=bytes.data();
        r_input.size=static_cast<uint32_t>(bytes.size());
        r_input.type=input.type;
        r_input.fmt=input.fmt;
        r_input.pass_through=0;
        rc=rknn_inputs_set(ctx,1,&r_input);
        if(rc!=RKNN_SUCC)throw std::runtime_error("rknn_inputs_set "+std::to_string(rc));
        rc=rknn_run(ctx,nullptr);
        if(rc!=RKNN_SUCC)throw std::runtime_error("rknn_run "+std::to_string(rc));
        rknn_output r_output{};
        r_output.index=0;
        r_output.want_float=1;
        rc=rknn_outputs_get(ctx,1,&r_output,nullptr);
        if(rc!=RKNN_SUCC)throw std::runtime_error("rknn_outputs_get "+std::to_string(rc));
        if(!r_output.buf){
            rknn_outputs_release(ctx,1,&r_output);
            throw std::runtime_error("Null output");
        }
        std::vector<std::pair<float,size_t>> ranked;
        const auto count=static_cast<size_t>(r_output.size)/sizeof(float);
        const float* scores=static_cast<const float*>(r_output.buf);
        for(size_t i=0;i<count;++i)ranked.emplace_back(scores[i],i);
        rc=rknn_outputs_release(ctx,1,&r_output);
        if(rc!=RKNN_SUCC)throw std::runtime_error("rknn_outputs_release "+std::to_string(rc));
        std::sort(ranked.begin(),ranked.end(),
                  [](const auto& a,const auto& b){return a.first>b.first;});
        for(size_t i=0;i<std::min<size_t>(5,ranked.size());++i)
            std::cout<<"output index="<<ranked[i].second
                     <<" score="<<ranked[i].first<<"\n";
        std::cerr<<"This is a classifier example. Category names require the model's labels.\n";
        return 0;
    }catch(const std::exception& e){
        std::cerr<<"ERROR: "<<e.what()<<"\n";
        return 1;
    }
}
