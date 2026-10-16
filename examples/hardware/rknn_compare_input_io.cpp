// ROCK 5B RKNPU2 one-input / one-output classification comparison.
// Baseline: rknn_inputs_set -> rknn_run -> rknn_outputs_get(want_float=1).
// Bound I/O: rknn_create_mem + rknn_set_io_mem for INPUT, rknn_run,
//            rknn_outputs_get(want_float=1) for OUTPUT.
// This is INPUT memory binding, NOT camera DMA -> NPU end-to-end zero copy.
// Example: ./rknn_compare_input_io model.rknn rgb_uint8_hwc.raw 15 3
#include "rknn_api.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
void require(int result,const std::string& action){
    if(result!=RKNN_SUCC)throw std::runtime_error(action+" returned "+std::to_string(result));
}
std::vector<uint8_t> read_binary(const std::string& name){
    std::ifstream in(name,std::ios::binary|std::ios::ate);
    if(!in)throw std::runtime_error("Cannot open "+name);
    const auto length=in.tellg();
    if(length<=0)throw std::runtime_error("Missing/empty model or tensor "+name);
    if(static_cast<uint64_t>(length)>UINT32_MAX)
        throw std::runtime_error("File too large for SDK input "+name);
    std::vector<uint8_t> out(static_cast<size_t>(length));
    in.seekg(0);
    if(!in.read(reinterpret_cast<char*>(out.data()),length))
        throw std::runtime_error("Failed to read "+name);
    return out;
}
struct Runtime {
    rknn_context ctx=0;
    rknn_tensor_mem* input=nullptr;
    Runtime(std::vector<uint8_t>& model) {
        require(rknn_init(&ctx,model.data(),static_cast<uint32_t>(model.size()),0,nullptr),"rknn_init");
    }
    ~Runtime(){
        if(input)rknn_destroy_mem(ctx,input);
        if(ctx)rknn_destroy(ctx);
    }
    Runtime(const Runtime&)=delete;
    Runtime& operator=(const Runtime&)=delete;
};
struct Attrs {
    rknn_tensor_attr input{};
    rknn_tensor_attr native{};
    rknn_tensor_attr output{};
};
Attrs query(Runtime& rt){
    rknn_input_output_num counts{};
    require(rknn_query(rt.ctx,RKNN_QUERY_IN_OUT_NUM,&counts,sizeof(counts)),"RKNN_QUERY_IN_OUT_NUM");
    if(counts.n_input!=1||counts.n_output!=1)
        throw std::runtime_error("Single-input, single-output classification model required");
    Attrs a{};
    a.input.index=0;
    a.native.index=0;
    a.output.index=0;
    require(rknn_query(rt.ctx,RKNN_QUERY_INPUT_ATTR,&a.input,sizeof(a.input)),"RKNN_QUERY_INPUT_ATTR");
    require(rknn_query(rt.ctx,RKNN_QUERY_NATIVE_INPUT_ATTR,&a.native,sizeof(a.native)),"RKNN_QUERY_NATIVE_INPUT_ATTR");
    require(rknn_query(rt.ctx,RKNN_QUERY_OUTPUT_ATTR,&a.output,sizeof(a.output)),"RKNN_QUERY_OUTPUT_ATTR");
    if(a.input.type!=RKNN_TENSOR_UINT8 || a.input.fmt!=RKNN_TENSOR_NHWC ||
       a.input.n_dims!=4 || a.input.n_elems==0 || a.output.n_elems==0)
        throw std::runtime_error("This benchmark supports UINT8 NHWC 4D input and one nonempty output only");
    return a;
}
std::vector<float> get_output(rknn_context ctx){
    rknn_output result{};
    result.index=0;
    result.want_float=1;
    require(rknn_outputs_get(ctx,1,&result,nullptr),"rknn_outputs_get");
    std::vector<float> data;
    try {
        if(!result.buf || !result.size || result.size%sizeof(float))
            throw std::runtime_error("RKNN output float buffer is empty/misaligned");
        const auto* ptr=static_cast<const float*>(result.buf);
        data.assign(ptr,ptr+result.size/sizeof(float));
    }catch(...){
        rknn_outputs_release(ctx,1,&result);
        throw;
    }
    require(rknn_outputs_release(ctx,1,&result),"rknn_outputs_release");
    return data;
}
void set_standard(Runtime& rt,const std::vector<uint8_t>& tensor,const Attrs& a){
    rknn_input input{};
    input.index=0;
    input.buf=const_cast<uint8_t*>(tensor.data());
    input.size=static_cast<uint32_t>(tensor.size());
    input.type=RKNN_TENSOR_UINT8;
    input.fmt=RKNN_TENSOR_NHWC;
    input.pass_through=0;
    require(rknn_inputs_set(rt.ctx,1,&input),"rknn_inputs_set");
}
void set_bound(Runtime& rt,const std::vector<uint8_t>& tensor,const Attrs& a){
    // Device stride/pitch is not generally the same as the tightly packed NHWC file.
    // Refuse padded models until a model-specific, query-proven row packing path is used.
    const uint32_t native_bytes=a.native.size_with_stride
        ? a.native.size_with_stride : a.native.size;
    if(!native_bytes || native_bytes!=a.input.size ||
       a.native.w_stride!=0 && a.native.w_stride!=a.input.dims[2])
        throw std::runtime_error(
            "Native input stride differs from contiguous tensor; "
            "row packing and I/O coherence must be validated for this SDK/model first");
    rt.input=rknn_create_mem(rt.ctx,native_bytes);
    if(!rt.input || !rt.input->virt_addr)
        throw std::runtime_error("rknn_create_mem failed");
    std::memcpy(rt.input->virt_addr,tensor.data(),tensor.size());
    rknn_tensor_attr input=a.input;
    input.index=0;
    input.type=RKNN_TENSOR_UINT8;
    input.fmt=RKNN_TENSOR_NHWC;
    input.pass_through=0;
    require(rknn_set_io_mem(rt.ctx,rt.input,&input),"rknn_set_io_mem INPUT");
}
struct Measure {
    std::vector<float> output;
    std::vector<double> milliseconds;
};
Measure measure(Runtime& rt,int warmup,int runs){
    Measure res;
    for(int i=0;i<warmup+runs;++i){
        auto begin=Clock::now();
        require(rknn_run(rt.ctx,nullptr),"rknn_run");
        std::vector<float> output=get_output(rt.ctx);
        const auto end=Clock::now();
        if(i>=warmup){
            res.milliseconds.push_back(std::chrono::duration<double,std::milli>(end-begin).count());
            res.output=std::move(output);
        }
    }
    return res;
}
double percentile(std::vector<double> xs,double q){
    std::sort(xs.begin(),xs.end());
    size_t i=static_cast<size_t>(std::ceil(xs.size()*q));
    if(i==0)i=1;
    return xs[i-1];
}
void show_measure(const char* label,const Measure& m){
    double sum=std::accumulate(m.milliseconds.begin(),m.milliseconds.end(),0.0);
    std::cout<<label<<" calls mean_ms="<<sum/m.milliseconds.size()
             <<" p50_ms="<<percentile(m.milliseconds,.5)
             <<" p95_ms="<<percentile(m.milliseconds,.95)
             <<" samples="<<m.milliseconds.size()<<"\n";
}
} // namespace

int main(int argc,char** argv){
    if(argc<3||argc>5){
        std::cerr<<"Usage: "<<argv[0]<<" model.rknn input_rgb_uint8_nhwc.raw [runs=20] [warmup=5]\n";
        return 2;
    }
    try{
        const int runs=argc>3?std::stoi(argv[3]):20;
        const int warmup=argc>4?std::stoi(argv[4]):5;
        if(runs<1||runs>10000||warmup<0||warmup>10000)
            throw std::runtime_error("runs must be 1..10000 and warmup 0..10000");
        auto model=read_binary(argv[1]);
        auto input=read_binary(argv[2]);
        Runtime standard(model);
        const auto attr=query(standard);
        if(input.size()!=attr.input.size)
            throw std::runtime_error("Input byte count is not the queried model input.size");
        std::cerr<<"Model input bytes="<<attr.input.size
                 <<" native stride bytes="<<attr.native.size_with_stride
                 <<" w_stride="<<attr.native.w_stride<<"\n";
        set_standard(standard,input,attr);
        const auto baseline=measure(standard,warmup,runs);

        // Separate context avoids switching the input path mid-model execution.
        Runtime bound(model);
        const auto bound_attrs=query(bound);
        if(bound_attrs.input.size!=attr.input.size)
            throw std::runtime_error("Different queried input sizes between contexts");
        set_bound(bound,input,bound_attrs);
        const auto attached=measure(bound,warmup,runs);
        if(baseline.output.size()!=attached.output.size())
            throw std::runtime_error("Output lengths differ between standard and bound paths");
        double max_abs=0,mean_abs=0;
        bool matching=true;
        for(size_t i=0;i<baseline.output.size();++i){
            const double a=baseline.output[i],b=attached.output[i];
            if(!std::isfinite(a)||!std::isfinite(b))
                throw std::runtime_error("Non-finite output value");
            const double diff=std::abs(a-b);
            max_abs=std::max(max_abs,diff);
            mean_abs+=diff;
            if(diff>0.01+0.01*std::abs(a))matching=false;
        }
        mean_abs/=baseline.output.size();
        std::cout<<std::fixed<<std::setprecision(5);
        show_measure("standard",baseline);
        show_measure("bound_input",attached);
        std::cout<<"output_elements="<<baseline.output.size()
                 <<" mean_abs_error="<<mean_abs
                 <<" max_abs_error="<<max_abs
                 <<" allclose_atol_0.01_rtol_0.01="<<(matching?"true":"false")<<"\n";
        std::cout<<"WARNING: binding path still performs a CPU memcpy into SDK memory, "
                    "and both paths copy float outputs via rknn_outputs_get. "
                    "No camera DMA-BUF or end-to-end zero-copy is claimed.\n";
        std::cout<<"WARNING: baseline is always measured before bound input; "
                    "temperature and scheduling can bias latency. Reverse order in a later experiment.\n";
        return matching?0:3;
    }catch(const std::exception& e){
        std::cerr<<"ERROR: "<<e.what()<<"\n";
        return 1;
    }
}
