# 实验 E｜摄像头 → RGA → RKNN C++ 检测

目标：理解真实视频捕获、硬件图像缩放和 NPU 之间的数据传递。教学重点是每一阶段的缓冲区含义，不以端到端零拷贝作为完课要求。

## 对应课程讲义与 HTML 课件

- [第26讲内存绑定](../docs/26_RKNPU2—零拷贝C API.md) · [HTML](../courseware/lessons/26_RKNPU2—零拷贝C API.html)
- [第31讲 YOLOv8](../docs/31_yolov8模型部署%28优化加速版%29.md) · [HTML](../courseware/lessons/31_yolov8模型部署%28优化加速版%29.html)

## 源码清单

- [V4L2/RGA/RKNPU2 C++ 主程序](../examples/hardware/v4l2_rga_rknn_yolov8.cpp)
- [视频 JSONL 验收工具](../boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py)
- [详细接口与数据流说明](../boards/radxa-rock5b/V4L2_RGA_RKNN_YOLOV8.md)

## 环境与输入

ROCK 5B、支持单平面 YUYV 的 V4L2 摄像头、匹配的 ARM64 librga / librknnrt 与头文件、Model Zoo 优化版 YOLOv8 RKNN。先运行 v4l2-ctl --device=/dev/video0 --list-formats-ext 检查实际相机是否支持 640×480 YUYV。

## 实验命令

~~~bash
cmake -S examples/hardware -B build/native-rknn -DRKNN_INCLUDE_DIR=/actual/rknn/include -DRKNN_LIB=/actual/arm64/librknnrt.so -DRGA_INCLUDE_DIR=/actual/librga/include -DRGA_LIB=/actual/arm64/librga.so
cmake --build build/native-rknn --target v4l2_rga_rknn_yolov8 -j2
./build/native-rknn/v4l2_rga_rknn_yolov8 /path/to/optimized-yolov8.rknn /dev/video0 640 480 10 0.25 > /tmp/camera_detections.jsonl
python3 boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py --jsonl /tmp/camera_detections.jsonl --width 640 --height 480 --expected-frames 10
~~~

数据流：V4L2 DQBUF → VIDIOC_EXPBUF 输出 DMA-BUF fd → RGA 导入 YUYV/转换缩放 → CPU 合成 640×640 letterbox → rknn_inputs_set → rknn_run → 取输出并进行 DFL/NMS → JSONL。这不是完整零拷贝：RGA 输出到 NPU 之间仍存在 CPU 数据复制。

## 自动化测试

- [逐帧 JSONL 单元测试](../tools/tests/test_cpp_yolo_stream.py)
- [假 SDK C++ 视频控制流](../examples/hardware/tests/test_native_video_pipeline.py)

## 验收标准

真实板端成功处理指定帧数，类别、坐标和帧号正确，并保存 stderr 的设备/SDK 输出。校验工具只能确认 JSONL 格式正确，不能确认日志来自实体设备。

## 验证边界

没有真实相机、RGA 和 RKNN 的 ROCK 5B 测试时，状态仍为待上板。不要把 DMA-BUF fd 导出成功说成了 NPU 零拷贝已实现。

