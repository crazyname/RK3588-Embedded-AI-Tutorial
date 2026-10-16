// ROCK 5B RGA preprocessing: packed RGB888 raw -> resized black letterbox RGB888.
// Uses librga (im2d). Import virtual addresses ONCE, accelerate resize with RGA,
// then CPU-copy resized RGB to black canvas. NOT camera DMA-BUF zero copy.
// Usage: ./rga_letterbox_rgb888 frame.rgb 640 480 letterbox.rgb [runs=10]
#include <cstddef>  // current librga headers use NULL in default arguments
#include "im2d.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
std::vector<uint8_t> read_exact(const std::string& filename,size_t expect){
    std::ifstream stream(filename,std::ios::binary|std::ios::ate);
    if(!stream)throw std::runtime_error("Cannot open "+filename);
    if(stream.tellg()!=static_cast<std::streamoff>(expect))
        throw std::runtime_error("Input must be tightly packed RGB888 W*H*3 bytes");
    std::vector<uint8_t> data(expect);
    stream.seekg(0);
    if(!stream.read(reinterpret_cast<char*>(data.data()),static_cast<std::streamsize>(expect)))
        throw std::runtime_error("Read failed");
    return data;
}
int integer(const char* text,int low,int high){
    const auto value=std::stoi(text);
    if(value<low||value>high)throw std::runtime_error("Dimension/count out of bounds");
    return value;
}
struct Handle {
    rga_buffer_handle_t id=0;
    explicit Handle(std::vector<uint8_t>& pixels){
        id=importbuffer_virtualaddr(pixels.data(),static_cast<int>(pixels.size()));
        if(!id)throw std::runtime_error("RGA importbuffer_virtualaddr failed; check librga driver");
    }
    ~Handle(){if(id)releasebuffer_handle(id);}
    Handle(const Handle&)=delete; Handle& operator=(const Handle&)=delete;
};
}
int main(int argc,char** argv){
    if(argc<5||argc>6){
        std::cerr<<"Usage: "<<argv[0]<<" rgb888.raw src_width src_height output_letterbox.rgb [runs=10]\n";
        return 2;
    }
    try{
        const int width=integer(argv[2],2,4096);
        const int height=integer(argv[3],2,4096);
        const int runs=argc==6?integer(argv[5],1,10000):10;
        constexpr int size=640;
        auto source=read_exact(argv[1],size_t(width)*height*3);
        const double scale=std::min(double(size)/width,double(size)/height);
        const int dst_w=std::max(1,std::min(size,int(std::lround(width*scale))));
        const int dst_h=std::max(1,std::min(size,int(std::lround(height*scale))));
        const int left=(size-dst_w)/2;
        const int top=(size-dst_h)/2;
        std::vector<uint8_t> resized(size_t(dst_w)*dst_h*3,0);
        std::vector<uint8_t> canvas(size_t(size)*size*3,0);
        // Real RGA virtual-address import (NOT dma-buf) needs compatible RK3588
        // librga headers/libs and RGA kernel driver.
        Handle src_handle(source);
        Handle dst_handle(resized);
        rga_buffer_t src=wrapbuffer_handle(src_handle.id,width,height,RK_FORMAT_RGB_888);
        rga_buffer_t dst=wrapbuffer_handle(dst_handle.id,dst_w,dst_h,RK_FORMAT_RGB_888);
        const auto status=imcheck(src,dst,{}, {});
        if(status!=IM_STATUS_NOERROR)
            throw std::runtime_error(std::string("imcheck: ")+imStrError(status));
        using Clock=std::chrono::steady_clock;
        double total=0;
        for(int i=0;i<runs;++i){
            const auto start=Clock::now();
            const auto result=imresize(src,dst);
            const auto end=Clock::now();
            if(result!=IM_STATUS_SUCCESS)
                throw std::runtime_error(std::string("imresize: ")+imStrError(result));
            total+=std::chrono::duration<double,std::milli>(end-start).count();
        }
        // Crop/pad stage remains explicit CPU copy; no pretence of zero copy.
        for(int y=0;y<dst_h;++y){
            const auto* from=resized.data()+size_t(y)*dst_w*3;
            auto* to=canvas.data()+(size_t(y+top)*size+left)*3;
            std::memcpy(to,from,size_t(dst_w)*3);
        }
        std::ofstream file(argv[4],std::ios::binary|std::ios::trunc);
        if(!file || !file.write(reinterpret_cast<const char*>(canvas.data()),
                                static_cast<std::streamsize>(canvas.size())))
            throw std::runtime_error("Cannot write output");
        std::cout<<std::fixed<<std::setprecision(4)
                 <<"source="<<width<<"x"<<height<<" resized="<<dst_w<<"x"<<dst_h
                 <<" padded="<<size<<"x"<<size
                 <<" pad_x="<<left<<" pad_y="<<top
                 <<" scale_x="<<double(dst_w)/width
                 <<" scale_y="<<double(dst_h)/height<<"\n"
                 <<"RGA imresize mean_ms="<<total/runs<<" runs="<<runs<<"\n"
                 <<"Result: RGB888 contiguous raw "<<canvas.size()<<" bytes.\n"
                 <<"IMPORTANT: input file already RGB, not BGR; virtualaddr import and "
                   "CPU letterbox copy prevent an end-to-end zero-copy claim.\n";
        return 0;
    }catch(const std::exception& err){
        std::cerr<<"ERROR: "<<err.what()<<"\n";
        return 1;
    }
}
