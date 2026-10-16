// CPU-only fake librga symbols for linking V4L2+RGA+RKNPU2 CLI in CI.
// Never use this library on ROCK 5B: it performs no color conversion or resize.
#include <cstddef>
#include "im2d.hpp"
static rga_buffer_handle_t next_handle=1;
rga_buffer_handle_t importbuffer_fd(int fd,int size){
    return fd>=0&&size>0?next_handle++:0;
}
rga_buffer_handle_t importbuffer_virtualaddr(void* address,int size){
    return address&&size>0?next_handle++:0;
}
extern "C" IM_STATUS releasebuffer_handle(rga_buffer_handle_t handle){
    return handle?IM_STATUS_SUCCESS:IM_STATUS_INVALID_PARAM;
}
extern "C" rga_buffer_t wrapbuffer_handle_t(
    rga_buffer_handle_t handle,int width,int height,int wstride,int hstride,int format){
    rga_buffer_t result{};
    result.handle=handle;
    result.width=width;result.height=height;
    result.wstride=wstride;result.hstride=hstride;
    result.format=format;
    return result;
}
IM_STATUS imcvtcolor(rga_buffer_t,rga_buffer_t,int,int,int,int,int*){
    return IM_STATUS_SUCCESS;
}
IM_STATUS imresize(const rga_buffer_t,rga_buffer_t,double,double,int,int,int*){
    return IM_STATUS_SUCCESS;
}
extern "C" const char* imStrError_t(IM_STATUS){
    return "MOCK RGA failure";
}
