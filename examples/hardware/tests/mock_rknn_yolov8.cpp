// CPU MOCK, NOT ROCK 5B EXECUTION.
// Implements ONLY the RKNN functions needed by rknn_yolov8_raw.cpp.
#include "rknn_api.h"
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <map>
#include <vector>
#include <initializer_list>

namespace {
struct State { bool input=false; bool inferred=false; };
std::map<rknn_context,State> states;
rknn_context next_context=1;
constexpr int GRIDS[3]={80,40,20};
std::size_t output_elements(unsigned index){
    const int kind=int(index%3);
    const int grid=GRIDS[index/3];
    const int channels=kind==0?64:kind==1?80:1;
    return std::size_t(channels)*grid*grid;
}
}
extern "C" {
int rknn_init(rknn_context* out,void* model,uint32_t size,uint32_t,rknn_init_extend*){
    if(!out||!model||!size)return -1;
    *out=next_context++;
    states[*out]=State{};
    return RKNN_SUCC;
}
int rknn_destroy(rknn_context ctx){
    return states.erase(ctx)==1?RKNN_SUCC:-1;
}
int rknn_query(rknn_context ctx,rknn_query_cmd cmd,void* ptr,uint32_t size){
    if(!states.count(ctx)||!ptr)return -1;
    if(cmd==RKNN_QUERY_IN_OUT_NUM){
        if(size<sizeof(rknn_input_output_num))return -1;
        auto* count=static_cast<rknn_input_output_num*>(ptr);
        count->n_input=1;
        count->n_output=9;
        return RKNN_SUCC;
    }
    if(size<sizeof(rknn_tensor_attr))return -1;
    auto* attr=static_cast<rknn_tensor_attr*>(ptr);
    const auto idx=attr->index;
    if(cmd==RKNN_QUERY_INPUT_ATTR){
        if(idx)return -1;
        attr->type=RKNN_TENSOR_UINT8;
        attr->fmt=RKNN_TENSOR_NHWC;
        attr->n_dims=4;
        attr->dims[0]=1;attr->dims[1]=640;attr->dims[2]=640;attr->dims[3]=3;
        attr->n_elems=640*640*3;
        attr->size=attr->n_elems;
        return RKNN_SUCC;
    }
    if(cmd==RKNN_QUERY_OUTPUT_ATTR){
        if(idx>=9)return -1;
        const int grid=GRIDS[idx/3];
        const int channels=idx%3==0?64:idx%3==1?80:1;
        attr->type=RKNN_TENSOR_FLOAT32;
        attr->fmt=RKNN_TENSOR_NCHW;
        attr->n_dims=4;
        attr->dims[0]=1;attr->dims[1]=channels;
        attr->dims[2]=grid;attr->dims[3]=grid;
        attr->n_elems=channels*grid*grid;
        attr->size=attr->n_elems*sizeof(float);
        return RKNN_SUCC;
    }
    return -1;
}
int rknn_inputs_set(rknn_context ctx,uint32_t num,rknn_input inputs[]){
    if(!states.count(ctx)||num!=1||!inputs||!inputs[0].buf||
       inputs[0].size!=640*640*3||inputs[0].fmt!=RKNN_TENSOR_NHWC)return -1;
    states[ctx].input=true;
    return RKNN_SUCC;
}
int rknn_run(rknn_context ctx,rknn_run_extend*){
    if(!states.count(ctx)||!states[ctx].input)return -1;
    states[ctx].inferred=true;
    return RKNN_SUCC;
}
int rknn_outputs_get(rknn_context ctx,uint32_t count,rknn_output outputs[],rknn_output_extend*){
    if(!states.count(ctx)||!states[ctx].inferred||count!=9||!outputs)return -1;
    for(unsigned i=0;i<count;++i){
        if(outputs[i].index!=i||!outputs[i].want_float)return -1;
    }
    for(unsigned i=0;i<count;++i){
        const auto elements=output_elements(i);
        float* data=static_cast<float*>(std::malloc(elements*sizeof(float)));
        if(!data)return -1;
        for(std::size_t v=0;v<elements;++v)
            data[v]=i%3==0?-20.0f:0.0f;
        if(i%3==0){
            const int grid=GRIDS[i/3];
            const auto cells=std::size_t(grid)*grid;
            for(int channel: {1,17,33,49}){
                for(std::size_t p=0;p<cells;++p)data[std::size_t(channel)*cells+p]=20.0f;
            }
        }
        if(i==1){
            const int grid=80;
            data[std::size_t(2)*grid*grid+std::size_t(40)*grid+40]=.93f;
        }
        outputs[i].buf=data;
        outputs[i].size=uint32_t(elements*sizeof(float));
    }
    return RKNN_SUCC;
}
int rknn_outputs_release(rknn_context ctx,uint32_t count,rknn_output outputs[]){
    if(!states.count(ctx)||count!=9||!outputs)return -1;
    for(unsigned i=0;i<count;++i){
        std::free(outputs[i].buf);
        outputs[i].buf=nullptr;
    }
    return RKNN_SUCC;
}
}
