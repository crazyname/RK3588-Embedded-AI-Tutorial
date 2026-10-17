# C++ V4L2→RGA→RKNN 视频检测：独立工程实验与验收

> 工程编号：`v4l2-rga-rknn`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/26_RKNPU2—零拷贝C API.md](../docs/26_RKNPU2—零拷贝C API.md) · [HTML 连续滚动课件](../courseware/lessons/26_RKNPU2—零拷贝C API.html)
- [Markdown：docs/31_yolov8模型部署%28优化加速版%29.md](../docs/31_yolov8模型部署%28优化加速版%29.md) · [HTML 连续滚动课件](../courseware/lessons/31_yolov8模型部署%28优化加速版%29.html)

## 源码清单

- [`examples/hardware/v4l2_rga_rknn_yolov8.cpp`](../examples/hardware/v4l2_rga_rknn_yolov8.cpp)
- [`boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py`](../boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
python3 -m unittest discover -s tools/tests -p test_cpp_yolo_stream.py -v
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 教学数据流与验收

主线是**摄像头取帧→RGA 缩放/letterbox→RKNN 推理→YOLOv8 解码→逐帧结果**。先通过 [RGA 独立实验](rga-preprocess.md) 检查尺寸、填充与坐标还原，再使用本工程的视频程序；其真实板端准备和编译见 [ROCK 5B 视频链路手册](../boards/radxa-rock5b/V4L2_RGA_RKNN_YOLOV8.md)。

```bash
python3 -m unittest discover -s tools/tests -p test_cpp_yolo_stream.py -v
python3 -m unittest discover -s examples/hardware/tests -p test_native_video_pipeline.py -v
```

这两条仅用于 PC 测试；真正验收还须执行 C++ 程序取得连续帧号、图像尺寸、框坐标与终端日志。此工程的 RGA→NPU 路径仍包含 CPU 拷贝，**不宣称端到端 DMA-BUF 零拷贝**。

## ROCK 5B 板端构建与视频

先用 v4l2-ctl --device=/dev/video0 --list-formats-ext 验证摄像头能提供 YUYV 单平面 640×480，不要将 MJPEG 当成 YUYV。RGA 与 RKNPU2 必须使用板端 ARM64 运行库：

~~~bash
cmake -S examples/hardware -B build/native-rknn -DRKNN_INCLUDE_DIR=/actual/rknn/include -DRKNN_LIB=/actual/arm64/librknnrt.so -DRGA_INCLUDE_DIR=/actual/librga/include -DRGA_LIB=/actual/arm64/librga.so
cmake --build build/native-rknn --target v4l2_rga_rknn_yolov8 -j2
./build/native-rknn/v4l2_rga_rknn_yolov8 /path/to/optimized-yolov8.rknn /dev/video0 640 480 10 0.25 > /tmp/camera_detections.jsonl
python3 boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py --jsonl /tmp/camera_detections.jsonl --width 640 --height 480 --expected-frames 10
~~~

验收真实连续帧号、类别、原图坐标和 stderr；RGA 缩放之后仍用 CPU 生成 letterbox 并经 rknn_inputs_set 传输，所以不宣称端到端零拷贝。

## 自动化测试

- [C++ 视频主程序 Fake SDK 原生可执行测试](../examples/hardware/tests/test_native_video_pipeline.py)：编译后执行 `--help`、不存在的模型和摄像头等失败路径；没有伪造成功采集。

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`tools/tests/test_cpp_yolo_stream.py`](../tools/tests/test_cpp_yolo_stream.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

验证逐帧 JSONL 连续帧号、原始像素坐标、分类范围、推理加解码 p95 和采集错误处理。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

仅 V4L2→RGA 共享 fd，RGA→NPU 仍发生 CPU 拷贝。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
