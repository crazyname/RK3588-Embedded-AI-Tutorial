# ROCK 5B：真实 V4L2 YUYV DMA-BUF → RGA → RKNPU2 YOLOv8 实验

> 状态：**完整 C++ 程序源码 + 官方 SDK 头文件编译/模拟运行时检查**。这里的“真实”指 C++ 程序调用实际 Linux ioctl、librga、RKNPU2 API；目前尚无实体 ROCK 5B 的成功运行和性能日志。**不是端到端零拷贝**。

## 1. 架构及边界

```text
USB UVC V4L2 /dev/videoX (single-planar YUYV only)
    │ VIDIOC_S_FMT(YUYV), REQBUFS(MMAP), QBUF/STREAMON, poll/DQBUF
    ├─ mmap() address for buffer management (not used to preprocess pixels)
    └─ VIDIOC_EXPBUF → DMA-BUF fd
                         │ importbuffer_fd(fd, size)
                         ▼
                  librga imcvtcolor YUYV→RGB
                         │ RGB virtual buffer
                         ▼
                  librga imresize (RGB)
                         │ resized RGB virtual buffer
                         ▼
                  CPU memcpy into black 640×640 letterbox
                         │ packed RGB uint8 NHWC
                         ▼
                  rknn_inputs_set (copies/sets RKNN input)
                         │ RKNPU2 rknn_run / outputs_get(want_float=1)
                         ▼
                  C++ DFL + class-aware NMS → JSON Lines detections
```

第一个共享接口是 **V4L2 exporter→RGA importer**，不是 RGA→NPU；两次 RGA 操作设为同步，处理完才能将对应相机缓冲重新 QBUF。RGA 的导出 fd、虚拟内存导入句柄、NPU 上下文及视频缓冲区均应正常释放。CPU 黑边合成、`rknn_inputs_set` 数据传输和 CPU 检测解码仍在路径中。

## 2. 必要硬件与 SDK

- 原版 [ROCK 5B RK3588 官方平台](https://docs.radxa.com/en/rock5/rock5b)；16 GB 仅为课程建议配置。
- 向 Linux 提供 **V4L2 单平面 YUYV** 的相机（大部分常见 UVC 摄像头可能只对指定尺寸/帧率支持 YUYV；仅支持 MJPEG 的摄像头不兼容本程序）。
- 与镜像/内核/BSP 版本匹配的 [Rockchip librga](https://github.com/airockchip/librga) 头文件和 ARM64 `librga.so`，且 RGA 驱动支持所使用 YUYV→RGB 转换、RGB resize、DMA-BUF fd 导入。
- 与同一 BSP 和型号匹配的 [RKNPU2 RK3588](https://github.com/rockchip-linux/rknpu2) `rknn_api.h`、ARM64 `librknnrt.so`。
- 经验证的 **Rockchip Model Zoo 优化版 YOLOv8**，640×640、单 UINT8 RGB 输入、80 类 COCO、三个尺度、六或九个**NCHW**输出。常规 [1,84,8400] ONNX、YOLO26、不同类别/stride 模型不支持。

系统需要可访问所选 `/dev/videoX`，并有 RGA/RKNPU2 设备权限。不要靠猜测随意修改设备驱动或执行 `sudo`；遇权限问题先阅读板商的组权限/udev 说明。

## 3. 先确认摄像头格式和 DMA-BUF 能力

在板端执行：

```bash
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

确认设备确实提供你需要的采集分辨率下的 **YUYV**，而不仅仅是 `MJPG`/`H264`。先用已有的 [MMAP/EXPBUF 检查工具](tools/v4l2_dmabuf_export_probe.cpp) 验证 fd 导出：

```bash
mkdir -p build
g++ -std=c++17 -O2 -Wall -Wextra -Werror \
  boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp \
  -o build/v4l2_dma_probe
./build/v4l2_dma_probe /dev/video0
```

该检查工具**不会采集帧**，只检查摄像头 DMA-BUF fd 能否成功导出。新程序执行实采集、RGA 转换和 NPU 推理；如果捕获格式是 MJPEG、步长存在未支持的 padding，必须明确失败，不可将压缩 JPEG bytes 按 YUYV/RGB 读取。

## 4. 原生编译

使用与 ROCK 5B 运行库匹配的 ARM64 编译器，在仓库根目录构建：

```bash
cmake -S examples/hardware -B build/native-rknn \
  -DRKNN_INCLUDE_DIR=/actual/sdk/rknpu2/include \
  -DRKNN_LIB=/actual/arm64/librknnrt.so \
  -DRGA_INCLUDE_DIR=/actual/sdk/librga/include \
  -DRGA_LIB=/actual/arm64/librga.so
cmake --build build/native-rknn --target v4l2_rga_rknn_yolov8 -j
```

四个 SDK 路径必须替换为实际文件/目录，**不要使用 PC 的 x86_64 共享库代替 ARM64**。`CMakeLists.txt` 只在设置 RGA include 和 lib 时编译此目标。完成后运行：

```bash
./build/native-rknn/v4l2_rga_rknn_yolov8 --help
```

## 5. 第一次真实采集与推理

请用实际模型路径、实际摄像头节点和相机支持的**偶数宽度**。以 640×480、采集 60 帧为例：

```bash
mkdir -p boards/radxa-rock5b/results
./build/native-rknn/v4l2_rga_rknn_yolov8 \
  /actual/models/optimized_yolov8.rknn /dev/video0 640 480 60 0.25 \
  > boards/radxa-rock5b/results/cpp_yolov8_frames.jsonl \
  2> boards/radxa-rock5b/results/cpp_yolov8_runtime.log
```

**stdout** 每帧一条 JSON：`frame`、`capture_ms`、`rga_plus_cpu_letterbox_ms`、`inference_and_decode_ms`，和数组 `detections`，内含 `class_id`、`score`、原相机图尺寸下的 `xyxy`；**stderr** 输出总帧数、FPS 与错误。默认不保存相机图片或视频，但 JSON 目标位置也可能涉及隐私，实验产物不要直接公开提交。

这里的 `inference_and_decode_ms` 包括输入设置、真实 `rknn_run`、取输出和 CPU 解码，不等于 NPU 硬件算子耗时；总体 FPS 是单线程循环吞吐量，和 CUDA/GPU/多线程视频管线不直接可比。

## 6. 首轮验收建议

先跑官方 Model Zoo 同一模型、同一张图片，再跑仓库现有的 [Python RKNNLite 摄像头检测](CAMERA_YOLOV8.md)。对照 RGB/BGR、640 黑边、输出顺序与类别映射。记录 Model Zoo commit、`.rknn` SHA256、板级版本、驱动/Runtime、librga.so 版本、原始 stdout/stderr、p50/p95、温度和实际帧率。

| 验收点 | 可接受的证据 |
|---|---|
| 驱动导出 DMA-BUF | `VIDIOC_EXPBUF` 成功且 fd 导入 RGA 句柄成功 |
| 真正采集 | `DQBUF` 的 bytesused 正确且真实帧数等于参数 |
| 图像转换 | RGA YUYV→RGB、resize 成功并与同源 CPU/OpenCV 比较颜色与尺寸 |
| NPU 真正推理 | 有板端 RKNPU2 加载、执行、输出和检测结果 |
| 性能结果 | 同型号/版本/相机配置与多次实验 p50/p95、FPS、CPU 温度 |
| 真正端到端零拷贝 | **未完成**：CPU letterbox 和 `rknn_inputs_set` 仍有数据复制 |

**尚未支持**：V4L2 多平面、MJPEG/H.264 解码、任意 bytesperline/stride、CSI ISP 特有格式、RGA 分辨率/对齐自动适配、RGA→NPU 共享 buffer、同步 fence 的跨驱动零拷贝、采集与推理多线程流水线、C++ 检测框直接显示/录制。遇不支持的设备要先记录错误、不要静默伪造帧。

这套代码已有官方头文件 C++ 语法检查、模拟 RGA/RKNPU2 **链接和缺设备失败路径**测试；真实 RGA 加速、相机采集、NPU 检测效果与上述零拷贝要求必须使用你的 ROCK 5B 实测。

