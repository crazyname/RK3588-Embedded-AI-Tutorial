// CI mock ONLY. Not RKLLM inference and must not ship to ROCK 5B production.
#include <cstddef>
#include "rkllm.h"
#include <cstdlib>
static RKLLMCallback cb{};
extern "C" RKLLMParam rkllm_createDefaultParam(){return RKLLMParam{};}
extern "C" int rkllm_init(LLMHandle*h,RKLLMParam*,RKLLMCallback*c){
 if(std::getenv("RKLLM_TEST_INIT_FAILURE"))return -42;
 *h=reinterpret_cast<LLMHandle>(0x1234);cb=*c;return 0;
}
extern "C" int rkllm_run(LLMHandle,RKLLMInput*in,RKLLMInferParam*,void*userdata){
 if(!in||in->input_type!=RKLLM_INPUT_PROMPT||!in->prompt_input)return -1;
 RKLLMResult r{};
 if(std::getenv("RKLLM_TEST_RUN_FAILURE")){
   cb.result_callback(&r,userdata,RKLLM_RUN_ERROR);return -5;
 }
 r.text="hello ";cb.result_callback(&r,userdata,RKLLM_RUN_NORMAL);
 r.text="world";cb.result_callback(&r,userdata,RKLLM_RUN_NORMAL);
 r.text=nullptr;
 if(!std::getenv("RKLLM_TEST_NO_PERF")){
   r.perf.prefill_time_ms=25.0f;r.perf.generate_time_ms=100.0f;
   r.perf.generate_tokens=5;r.perf.memory_usage_mb=128.0f;
 }
 cb.result_callback(&r,userdata,RKLLM_RUN_FINISH);return 0;
}
extern "C" int rkllm_destroy(LLMHandle){return 0;}
