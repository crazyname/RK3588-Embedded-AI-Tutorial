// ROCK 5B: native RKLLM C API callback and performance telemetry.
// This source requires an actual model/Runtime; CI test double is not hardware inference.
#include <cstddef>
#include "rkllm.h"
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
using Clock=std::chrono::steady_clock;
double ms(Clock::duration d){return std::chrono::duration<double,std::milli>(d).count();}
std::string json_escape(const std::string&s){
  const char hex[]="0123456789abcdef";std::string out;
  for(unsigned char c:s){
    if(c=='"')out+="\\\"";else if(c=='\\')out+="\\\\";
    else if(c=='\n')out+="\\n";else if(c=='\r')out+="\\r";else if(c=='\t')out+="\\t";
    else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}
    else out+=char(c);
  }
  return out;
}
struct Args{std::string model,prompt,report;int max_new=128,context=2048;bool save_text=false;};
Args parse(int argc,char**argv){
  Args a;
  for(int i=1;i<argc;i++){
    std::string k=argv[i];
    if(k=="--help"||k=="-h"){
      std::cout<<"usage: rkllm_stream --model MODEL.rkllm --prompt-file PROMPT.txt "
                  "[--report run.json] [--max-new 128] [--context 2048] [--save-text]\n";
      std::exit(0);
    }
    if(k=="--save-text"){a.save_text=true;continue;}
    if(i+1>=argc)throw std::runtime_error("Missing parameter value after "+k);
    std::string v=argv[++i];
    if(k=="--model")a.model=v;else if(k=="--prompt-file")a.prompt=v;
    else if(k=="--report")a.report=v;
    else if(k=="--max-new")a.max_new=std::stoi(v);
    else if(k=="--context")a.context=std::stoi(v);
    else throw std::runtime_error("Unknown option "+k);
  }
  if(a.model.empty()||a.prompt.empty())throw std::runtime_error("--model and --prompt-file required");
  if(a.max_new<1||a.max_new>32768||a.context<1||a.context>65536)
    throw std::runtime_error("Invalid token/context limit");
  return a;
}
std::string read_prompt(const std::string&path){
  std::ifstream in(path,std::ios::binary);
  if(!in)throw std::runtime_error("Prompt file missing");
  std::string s;char buffer[4096];
  while(in.read(buffer,sizeof(buffer))||in.gcount()>0){
    s.append(buffer,size_t(in.gcount()));
    if(s.size()>65536)throw std::runtime_error("Prompt exceeds 64KiB");
  }
  if(s.empty()||s.find('\0')!=std::string::npos)throw std::runtime_error("Invalid prompt text");
  return s;
}
struct Metrics{
  Clock::time_point started{},first{};
  bool got_text=false,finished=false,error=false,perf_seen=false;
  size_t chunks=0,bytes=0;
  std::string text;
  RKLLMPerfStat perf{};
};
int callback(RKLLMResult*r,void*userdata,LLMCallState state){
  auto*m=static_cast<Metrics*>(userdata);
  if(!m)return 0;
  if(state==RKLLM_RUN_ERROR){m->error=true;return 0;}
  if(state==RKLLM_RUN_FINISH){
    m->finished=true;
    if(r){m->perf=r->perf;m->perf_seen=true;}
    return 0;
  }
  if(state!=RKLLM_RUN_NORMAL||!r||!r->text)return 0;
  const std::string chunk(r->text);
  if(chunk.empty())return 0;
  if(!m->got_text){m->first=Clock::now();m->got_text=true;}
  m->chunks++;m->bytes+=chunk.size();m->text+=chunk;
  std::cout<<chunk<<std::flush;
  return 0;
}
struct Session{
  LLMHandle handle=nullptr;
  Session()=default;
  Session(const Session&)=delete;
  Session&operator=(const Session&)=delete;
  ~Session(){if(handle)rkllm_destroy(handle);}
};
void write_report(const Args&a,const Metrics&m,double init_ms,double run_ms,int status,std::streamoff model_bytes){
  if(a.report.empty())return;
  std::ofstream f(a.report,std::ios::binary);
  if(!f)throw std::runtime_error("Could not open report");
  f<<std::fixed<<std::setprecision(3);
  f<<"{\n  \"backend\": \"RKLLM C API\",\n"
   <<"  \"model_file\": \""<<json_escape(a.model)<<"\",\n"
   <<"  \"max_new_tokens\": "<<a.max_new<<",\n"\n   <<"  \"context_tokens\": "<<a.context<<",\n"\n   <<"  \"model_size_bytes\": "<<model_bytes<<",\n"\n   <<"  \"initialized_ms\": "<<init_ms<<",\n  \"run_wall_ms\": "<<run_ms
   <<",\n  \"first_text_chunk_ms\": ";
  if(m.got_text)f<<ms(m.first-m.started);else f<<"null";
  f<<",\n  \"text_chunks\": "<<m.chunks<<",\n  \"output_utf8_bytes\": "<<m.bytes
   <<",\n  \"finished_callback\": "<<(m.finished?"true":"false")
   <<",\n  \"run_status\": "<<status
   <<",\n  \"callback_error\": "<<(m.error?"true":"false")
   <<",\n  \"sdk_generate_tokens\": ";
  if(m.perf_seen&&m.perf.generate_tokens>0)f<<m.perf.generate_tokens;else f<<"null";
  f<<",\n  \"sdk_generate_time_ms\": ";
  if(m.perf_seen&&m.perf.generate_time_ms>0)f<<m.perf.generate_time_ms;else f<<"null";
  f<<",\n  \"sdk_tokens_per_sec\": ";
  if(m.perf_seen&&m.perf.generate_tokens>0&&m.perf.generate_time_ms>0)
     f<<m.perf.generate_tokens*1000.0/m.perf.generate_time_ms;
  else f<<"null";
  f<<",\n  \"sdk_prefill_time_ms\": ";
  if(m.perf_seen&&m.perf.prefill_time_ms>0)f<<m.perf.prefill_time_ms;else f<<"null";
  f<<",\n  \"sdk_peak_memory_mb\": ";
  if(m.perf_seen&&m.perf.memory_usage_mb>0)f<<m.perf.memory_usage_mb;else f<<"null";
  f<<",\n  \"note\": \"first_text_chunk_ms is time to first text callback, NOT necessarily time to first token; text chunks are not tokens\"";
  if(a.save_text)f<<",\n  \"generated_text\": \""<<json_escape(m.text)<<"\"";
  f<<"\n}\n";
  if(!f)throw std::runtime_error("Report write error");
}
int main(int argc,char**argv){
  try{
    const Args a=parse(argc,argv);
    std::ifstream mfile(a.model,std::ios::binary|std::ios::ate);
    if(!mfile||mfile.tellg()<=0)throw std::runtime_error("Model missing or empty");
    const std::streamoff model_bytes=mfile.tellg();
    const std::string prompt=read_prompt(a.prompt);
    Session session;Metrics m;
    RKLLMParam p=rkllm_createDefaultParam();
    p.model_path=a.model.c_str();p.max_new_tokens=a.max_new;
    p.max_context_len=a.context;p.skip_special_token=true;p.is_async=false;
    RKLLMCallback cb{};cb.result_callback=callback;cb.result_userdata=&m;
    const auto t0=Clock::now();
    int init_rc=rkllm_init(&session.handle,&p,&cb);
    double init_ms=ms(Clock::now()-t0);
    if(init_rc)throw std::runtime_error("rkllm_init failure "+std::to_string(init_rc));
    if(!session.handle)throw std::runtime_error("rkllm_init returned null handle");
    RKLLMInput input{};input.role="user";input.input_type=RKLLM_INPUT_PROMPT;
    input.prompt_input=prompt.c_str();
    RKLLMInferParam infer{};infer.mode=RKLLM_INFER_GENERATE;infer.keep_history=0;
    m.started=Clock::now();
    int rc=rkllm_run(session.handle,&input,&infer,&m);
    double elapsed=ms(Clock::now()-m.started);
    std::cout<<"\n";
    write_report(a,m,init_ms,elapsed,rc,model_bytes);
    if(rc||m.error||!m.finished)throw std::runtime_error("RKLLM run failed/incomplete");
    std::cerr<<"RKLLM callback chunks="<<m.chunks<<" run_ms="<<elapsed<<"\n";
    return 0;
  }catch(const std::exception&e){
    std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;
  }
}
