// Model Zoo optimized YOLOv8, FP32 NCHW outputs: six or nine tensors.
// No dependency on RKNPU2, OpenCV, or other device SDK; usable on x86 CI.
#pragma once
#include <cstddef>
#include <vector>

namespace rk_yolo {
struct Tensor {
    const float* data = nullptr; // NCHW batch=1, contiguous, float32
    std::size_t elements = 0;
    int channels=0;
    int height=0;
    int width=0;
};
struct ImageMapping {
    int source_width=0;
    int source_height=0;
    float scale_x=0;
    float scale_y=0;
    int pad_x=0;
    int pad_y=0;
};
struct Detection {
    int class_id=0;
    float score=0;
    float x1=0, y1=0, x2=0, y2=0;
};
struct Options {
    int model_size=640;
    int num_classes=80;
    float conf_threshold=0.25f;
    float nms_iou_threshold=0.45f;
    int max_detections=100;
};
ImageMapping black_letterbox_mapping(int width,int height,int model_size=640);
std::vector<Detection> decode(const std::vector<Tensor>& outputs,
                              const ImageMapping& mapping,
                              const Options& options=Options{});
} // namespace rk_yolo
