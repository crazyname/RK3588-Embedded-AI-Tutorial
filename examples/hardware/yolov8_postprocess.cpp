#include "yolov8_postprocess.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace rk_yolo {
namespace {
struct Candidate {
    Detection hit;
    std::size_t serial;
};
void require(bool yes,const char* message){
    if(!yes)throw std::invalid_argument(message);
}
bool finite(float v){return std::isfinite(v);}
float clampf(float x,float lower,float upper){
    return std::max(lower,std::min(upper,x));
}
float integral(const Tensor& tensor,int side,int pos){
    const auto plane=std::size_t(tensor.width)*tensor.height;
    float maximum=-std::numeric_limits<float>::infinity();
    for(int bin=0;bin<16;++bin){
        const auto index=(side*16+bin)*plane+pos;
        const float value=tensor.data[index];
        require(finite(value),"Non-finite selected DFL logit");
        maximum=std::max(maximum,value);
    }
    float sum=0,numerator=0;
    for(int bin=0;bin<16;++bin){
        const float value=tensor.data[(side*16+bin)*plane+pos];
        const float weight=std::exp(value-maximum);
        sum+=weight;
        numerator+=weight*bin;
    }
    require(sum>0 && finite(sum),"Numerically invalid DFL distribution");
    return numerator/sum;
}
float iou(const Detection& a,const Detection& b){
    const float l=std::max(a.x1,b.x1), t=std::max(a.y1,b.y1);
    const float r=std::min(a.x2,b.x2), d=std::min(a.y2,b.y2);
    const float intersection=std::max(0.0f,r-l)*std::max(0.0f,d-t);
    const float aarea=(a.x2-a.x1)*(a.y2-a.y1);
    const float barea=(b.x2-b.x1)*(b.y2-b.y1);
    const float denominator=aarea+barea-intersection;
    return denominator>0?intersection/denominator:0.0f;
}
} // namespace

ImageMapping black_letterbox_mapping(int width,int height,int model_size){
    require(width>0&&height>0&&model_size>0,"Invalid letterbox dimensions");
    const double scale=std::min(double(model_size)/width,double(model_size)/height);
    // cv2 resize with Python round() can differ at exact half ties.
    // The Python reference currently uses Python's ties-to-even rounding.
    const auto even_round=[](double value)->int{return int(std::nearbyint(value));};
    const int resized_w=std::max(1,std::min(model_size,even_round(width*scale)));
    const int resized_h=std::max(1,std::min(model_size,even_round(height*scale)));
    return {width,height,float(double(resized_w)/width),float(double(resized_h)/height),
            (model_size-resized_w)/2,(model_size-resized_h)/2};
}

std::vector<Detection> decode(const std::vector<Tensor>& outputs,
                              const ImageMapping& map,const Options& config){
    require(outputs.size()==6||outputs.size()==9,"Expected 6 or 9 optimized YOLOv8 outputs");
    require(config.model_size>0&&config.num_classes>0&&config.max_detections>0,
            "Invalid model size, class count, or max detections");
    require(finite(config.conf_threshold)&&config.conf_threshold>=0&&
            config.conf_threshold<=1&&finite(config.nms_iou_threshold)&&
            config.nms_iou_threshold>0&&config.nms_iou_threshold<1,
            "Invalid confidence or NMS threshold");
    require(map.source_width>0&&map.source_height>0&&
            finite(map.scale_x)&&finite(map.scale_y)&&map.scale_x>0&&map.scale_y>0,
            "Invalid inverse letterbox metadata");
    const int stride=int(outputs.size()/3);
    int last_grid=std::numeric_limits<int>::max();
    std::vector<Candidate> boxes;
    std::size_t serial=0;
    for(int head=0;head<3;++head){
        const Tensor& box=outputs[std::size_t(head)*stride];
        const Tensor& cls=outputs[std::size_t(head)*stride+1];
        const int h=box.height,w=box.width;
        require(h>0&&w>0&&h==w&&w<last_grid&&config.model_size%w==0,
                "YOLOv8 head grids must be square, descending and divide input size");
        last_grid=w;
        const auto cells=std::size_t(h)*w;
        require(box.data&&box.channels==64&&box.elements==64*cells,
                "Expected float32 DFL [1,64,H,W] contiguous output");
        require(cls.data&&cls.channels==config.num_classes&&cls.height==h&&cls.width==w&&
                cls.elements==std::size_t(config.num_classes)*cells,
                "Expected float32 class [1,num_classes,H,W] contiguous output");
        if(stride==3){
            const auto& aux=outputs[std::size_t(head)*stride+2];
            require(aux.data&&aux.channels==1&&aux.height==h&&aux.width==w&&
                    aux.elements==cells,"Auxiliary output tensor must have shape [1,1,H,W]");
        }
        for(std::size_t position=0;position<cells;++position){
            float confidence=-std::numeric_limits<float>::infinity();
            int best=-1;
            for(int c=0;c<config.num_classes;++c){
                const float score=cls.data[std::size_t(c)*cells+position];
                require(finite(score),"Non-finite class score");
                if(score>confidence){confidence=score;best=c;}
            }
            if(confidence<config.conf_threshold)continue;
            const float s=float(config.model_size)/w;
            const float cx=(float(position%w)+0.5f)*s;
            const float cy=(float(position/w)+0.5f)*s;
            Detection hit;
            hit.class_id=best;hit.score=confidence;
            hit.x1=clampf((cx-integral(box,0,int(position))*s-map.pad_x)/map.scale_x,
                           0,float(map.source_width));
            hit.y1=clampf((cy-integral(box,1,int(position))*s-map.pad_y)/map.scale_y,
                           0,float(map.source_height));
            hit.x2=clampf((cx+integral(box,2,int(position))*s-map.pad_x)/map.scale_x,
                           0,float(map.source_width));
            hit.y2=clampf((cy+integral(box,3,int(position))*s-map.pad_y)/map.scale_y,
                           0,float(map.source_height));
            if(hit.x2>hit.x1 && hit.y2>hit.y1)boxes.push_back({hit,serial++});
        }
    }
    // Per-class greedy NMS, mirroring NumPy argsort(kind="stable").
    std::vector<Candidate> retained;
    for(int category=0;category<config.num_classes;++category){
        std::vector<Candidate> current;
        for(const auto& candidate:boxes)
            if(candidate.hit.class_id==category)current.push_back(candidate);
        std::stable_sort(current.begin(),current.end(),
                         [](const Candidate& a,const Candidate& b){
                             return a.hit.score>b.hit.score;
                         });
        std::vector<Detection> accepted;
        for(const auto& candidate:current){
            bool suppressed=false;
            for(const auto& a:accepted){
                if(iou(a,candidate.hit)>config.nms_iou_threshold){suppressed=true;break;}
            }
            if(!suppressed){
                accepted.push_back(candidate.hit);
                retained.push_back(candidate);
                if(int(accepted.size())>=config.max_detections)break;
            }
        }
    }
    std::stable_sort(retained.begin(),retained.end(),[](const Candidate& a,const Candidate& b){
        if(a.hit.score!=b.hit.score)return a.hit.score>b.hit.score;
        if(a.hit.class_id!=b.hit.class_id)return a.hit.class_id<b.hit.class_id;
        return a.serial<b.serial;
    });
    if(retained.size()>std::size_t(config.max_detections))
        retained.resize(std::size_t(config.max_detections));
    std::vector<Detection> answer;
    answer.reserve(retained.size());
    for(const auto& item:retained)answer.push_back(item.hit);
    return answer;
}
} // namespace rk_yolo
