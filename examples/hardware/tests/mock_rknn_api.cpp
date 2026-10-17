// FAKE RKNN Runtime used ONLY for CPU CI tests of rknn_compare_input_io.cpp.
// Must NEVER be installed on RK3588 or described as real NPU execution.
#include "rknn_api.h"
#include <cstdlib>
// Failure injection is controlled only by test environment variables.
static bool fail(const char* key){const char* v=std::getenv(key);return v && std::strcmp(v,"1")==0;}
#include <cstring>
#include <map>
#include <vector>
struct State {
    std::vector<uint8_t> input;
    rknn_tensor_mem* bound=nullptr;
    rknn_tensor_mem* bound_output=nullptr;
    float outputs[4]={};
};
static std::map<rknn_context,State> states;
static rknn_context next_ctx=1;
extern "C" {
int rknn_init(rknn_context* ctx,void* model,uint32_t bytes,uint32_t,rknn_init_extend*){
    if(!model||!bytes)return -1;
    *ctx=next_ctx++;
    states[*ctx]=State{};
    return RKNN_SUCC;
}
int rknn_destroy(rknn_context ctx){states.erase(ctx);return RKNN_SUCC;}
int rknn_query(rknn_context ctx,rknn_query_cmd cmd,void* target,uint32_t bytes){
    if(!states.count(ctx)||!target)return -1;
    if(cmd==RKNN_QUERY_IN_OUT_NUM){
        if(bytes<sizeof(rknn_input_output_num))return -1;
        auto* n=static_cast<rknn_input_output_num*>(target);
        n->n_input=1;n->n_output=1;return RKNN_SUCC;
    }
    if(bytes<sizeof(rknn_tensor_attr))return -1;
    auto* a=static_cast<rknn_tensor_attr*>(target);
    if(cmd!=RKNN_QUERY_INPUT_ATTR && cmd!=RKNN_QUERY_NATIVE_INPUT_ATTR &&
       cmd!=RKNN_QUERY_OUTPUT_ATTR)return -1;
    a->index=0;
    a->n_dims=4;
    a->dims[0]=1;a->dims[1]=4;a->dims[2]=4;a->dims[3]=3;
    a->n_elems=48;
    a->size=48;
    a->type=RKNN_TENSOR_UINT8;
    a->fmt=RKNN_TENSOR_NHWC;
    a->w_stride=4;
    a->size_with_stride=48;
    if(cmd==RKNN_QUERY_OUTPUT_ATTR){
        a->n_elems=4;a->size=4*sizeof(float);a->type=RKNN_TENSOR_FLOAT32;
    }
    return RKNN_SUCC;
}
int rknn_inputs_set(rknn_context ctx,uint32_t num,rknn_input inputs[]){
    if(!states.count(ctx)||num!=1||!inputs||inputs[0].size!=48||!inputs[0].buf)return -1;
    auto* first=static_cast<uint8_t*>(inputs[0].buf);
    states[ctx].input.assign(first,first+48);
    return RKNN_SUCC;
}
rknn_tensor_mem* rknn_create_mem(rknn_context ctx,uint32_t bytes){
    if(!states.count(ctx)||!bytes||fail("RKNN_FAKE_FAIL_ALLOC"))return nullptr;
    auto* obj=static_cast<rknn_tensor_mem*>(std::calloc(1,sizeof(rknn_tensor_mem)));
    if(!obj)return nullptr;
    obj->virt_addr=std::calloc(bytes,1);
    if(!obj->virt_addr){std::free(obj);return nullptr;}
    obj->size=bytes;
    return obj;
}
int rknn_destroy_mem(rknn_context,rknn_tensor_mem* mem){
    if(!mem)return -1;
    std::free(mem->virt_addr);std::free(mem);return RKNN_SUCC;
}
int rknn_set_io_mem(rknn_context ctx,rknn_tensor_mem* mem,rknn_tensor_attr* attr){
    if(!states.count(ctx)||!mem||!attr)return -1;
    if(attr->type==RKNN_TENSOR_FLOAT32 && mem->size==4*sizeof(float)){
        states[ctx].bound_output=mem;
        return RKNN_SUCC;
    }
    if(attr->type==RKNN_TENSOR_UINT8 && mem->size==48){
        states[ctx].bound=mem;
        return RKNN_SUCC;
    }
    return -1;
}
int rknn_run(rknn_context ctx,rknn_run_extend*){
    if(!states.count(ctx)||fail("RKNN_FAKE_FAIL_RUN"))return -1;
    auto& s=states[ctx];
    if(s.bound){
        auto* bytes=static_cast<uint8_t*>(s.bound->virt_addr);
        s.input.assign(bytes,bytes+48);
    }
    if(s.input.size()!=48)return -1;
    float sum=0;
    uint8_t min=255,max=0;
    for(uint8_t value:s.input){
        sum+=value;if(value<min)min=value;if(value>max)max=value;
    }
    s.outputs[0]=sum/48;
    s.outputs[1]=min;
    s.outputs[2]=max;
    s.outputs[3]=s.input[0];
    if(s.bound_output && s.bound_output->virt_addr && s.bound_output->size>=sizeof(s.outputs))
        std::memcpy(s.bound_output->virt_addr,s.outputs,sizeof(s.outputs));
    return RKNN_SUCC;
}
int rknn_outputs_get(rknn_context ctx,uint32_t num,rknn_output outputs[],rknn_output_extend*){
    if(!states.count(ctx)||num!=1||!outputs||fail("RKNN_FAKE_FAIL_OUTPUTS"))return -1;
    outputs[0].size=4*sizeof(float);
    outputs[0].buf=std::malloc(outputs[0].size);
    if(!outputs[0].buf)return -1;
    std::memcpy(outputs[0].buf,states[ctx].outputs,outputs[0].size);
    return RKNN_SUCC;
}
int rknn_outputs_release(rknn_context,uint32_t count,rknn_output outputs[]){
    if(count!=1||!outputs)return -1;
    std::free(outputs[0].buf);outputs[0].buf=nullptr;
    return RKNN_SUCC;
}
}
