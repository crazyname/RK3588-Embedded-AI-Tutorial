// Offline CPU reference: decode exactly the same FP32 NCHW tensor files as Python.
// No .rknn or hardware runtime; useful for cross-language numerical regression.
// Usage: yolov8_decode_files folder heads grid0 grid1 grid2 sourceW sourceH [conf]
// Example: yolov8_decode_files build/yolo-fixture 9 8 4 2 640 480 0.25
#include "yolov8_postprocess.hpp"
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
int integer(const char* word,int lo,int hi) {
    const int v=std::stoi(word);
    if(v<lo||v>hi)throw std::invalid_argument("Integer argument out of range");
    return v;
}
std::vector<float> read_floats(const std::string& name,std::size_t expected){
    std::ifstream file(name,std::ios::binary|std::ios::ate);
    if(!file)throw std::runtime_error("Cannot read "+name);
    if(file.tellg()!=static_cast<std::streamoff>(expected*sizeof(float)))
        throw std::runtime_error("Unexpected tensor file byte length: "+name);
    std::vector<float> result(expected);
    file.seekg(0);
    if(!file.read(reinterpret_cast<char*>(result.data()),
                  static_cast<std::streamsize>(expected*sizeof(float))))
        throw std::runtime_error("Tensor read error "+name);
    return result;
}
void print(const std::vector<rk_yolo::Detection>& items){
    std::cout<<std::fixed<<std::setprecision(7)<<"{\"detections\":[";
    for(std::size_t k=0;k<items.size();++k){
        const auto& v=items[k];
        if(k)std::cout<<",";
        std::cout<<"{\"class_id\":"<<v.class_id<<",\"score\":"<<v.score
                 <<",\"xyxy\":["<<v.x1<<","<<v.y1<<","<<v.x2<<","<<v.y2<<"]}";
    }
    std::cout<<"],\"backend\":\"cpp-cpu-reference-not-npu\"}\n";
}
}
int main(int argc,char** argv){
    if(argc!=8&&argc!=9){
        std::cerr<<"Usage: "<<argv[0]
                 <<" folder heads(6|9) grid0 grid1 grid2 sourceW sourceH [confidence]\n";
        return 2;
    }
    try{
        const std::string dir=argv[1];
        const int outputs=integer(argv[2],6,9);
        if(outputs!=6&&outputs!=9)throw std::invalid_argument("Only 6 or 9 outputs supported");
        const int grids[3]={integer(argv[3],1,640),integer(argv[4],1,640),
                            integer(argv[5],1,640)};
        const int width=integer(argv[6],1,32768),height=integer(argv[7],1,32768);
        rk_yolo::Options options;
        if(argc==9)options.conf_threshold=std::stof(argv[8]);
        const int spacing=outputs/3;
        std::vector<std::vector<float>> buffers;
        std::vector<rk_yolo::Tensor> tensors;
        buffers.reserve(outputs);tensors.reserve(outputs);
        for(int k=0;k<outputs;++k){
            const int branch=k/spacing;
            const int kind=k%spacing;
            const int channels=(kind==0?64:(kind==1?80:1));
            const int grid=grids[branch];
            const auto count=std::size_t(channels)*grid*grid;
            buffers.push_back(read_floats(dir+"/out_"+std::to_string(k)+".f32",count));
            tensors.push_back({buffers.back().data(),count,channels,grid,grid});
        }
        const auto meta=rk_yolo::black_letterbox_mapping(width,height,640);
        print(rk_yolo::decode(tensors,meta,options));
        return 0;
    }catch(const std::exception& err){
        std::cerr<<"ERROR: "<<err.what()<<"\n";
        return 1;
    }
}
