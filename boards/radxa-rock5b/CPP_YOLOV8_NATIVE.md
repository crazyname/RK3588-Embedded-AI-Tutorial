# RK3588 原生 C++ YOLOv8：FP32 DFL/NMS、RKNPU2 实际推理与 DMA-BUF 前置检查

这个项目为 ROCK 5B/RK3588 建立一个能复现的 C++ 推理链：**实际 .rknn 模型→RKNPU2 C API→官方优化版 YOLOv8 6/9 个浮点输出→本仓库 C++ DFL、letterbox 坐标反变换、按类 NMS→检测框 JSON**。

同时有与设备无关的 C++ 解码 CLI，可以从磁盘加载真实张量并与课程原有 Python 解码逐个对照。设备侧提供 V4L2 MMAP 缓冲区导出 DMA-BUF fd 的能力检测，但没有把摄像头接到 RGA/NPU。

## 1. 代码位置和严格模型协议

- [C++ DFL/letterbox/NMS](../../examples/hardware/yolov8_postprocess.cpp) 与 [头文件](../../examples/hardware/yolov8_postprocess.hpp)
- [C++ 读取 FP32 检测头的 CPU CLI](../../examples/hardware/yolov8_decode_files.cpp)——可在普通电脑编译、无需 NPU
- [真正使用 RK3588 RKNPU2 多输出推理的程序](../../examples/hardware/rknn_yolov8_raw.cpp)
- [真实图像生成黑边 RGB uint8 输入](../../tools/prepare_yolov8_rgb.py)
- [真实 V4L2 DMA-BUF 导出能力检测](tools/v4l2_dmabuf_export_probe.cpp)
- [Rockchip Model Zoo 优化版 YOLOv8](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/yolov8)（模型和 Runtime、Driver 必须与设备匹配）

**本基准只接受 640×640，80 类 COCO，3 个检测尺度，6 或 9 张量，FP32 NCHW 输出（若 RKNN 量化，SDK 需使用 want_float=1 返回反量化浮点）。** 典型九输出形状按顺序是：

    [1,64,80,80], [1,80,80,80], [1,1,80,80]
    [1,64,40,40], [1,80,40,40], [1,1,40,40]
    [1,64,20,20], [1,80,20,20], [1,1,20,20]

单一 [1,84,8400] 的 Ultralytics ONNX、YOLO26、分割/姿态模型，以及输出通道或布局不同的 RKNN 都不能直接替换；C++ 会主动拒绝错误的输入维度和模型协议。

## 2. PC：先验证真正的 C++ 计算

从仓库根目录：

    g++ -std=c++17 -O2 -Wall -Wextra -Werror \
      examples/hardware/yolov8_postprocess.cpp \
      examples/hardware/yolov8_decode_files.cpp \
      -o build/yolov8_decode_files

回归测试：

    RK_YOLO_CPP_DECODER=build/yolov8_decode_files \
      python3 -m unittest discover -s examples/hardware/tests \
        -p test_yolov8_cpp_parity.py -v

该测试在本地写入实际 FP32 二进制张量：同时让 C++ 和 Python 对六/九输出、不同源图尺寸和错误数据运行，用容差比较坐标、置信度与类号。测试通过证明解码计算符合 Python 参考实现，**不等于证明使用真实 RKNN 模型推理**。

## 3. PC 生成与 C++、Python 一致的预处理文件

先安装符合 SETUP.md 要求的 NumPy/OpenCV。使用本地许可合规的图片（例如自己拍摄的物体图片）：

    python3 tools/prepare_yolov8_rgb.py \
      --image /path/to/image.jpg \
      --raw build/yolov8_input.rgb \
      --manifest build/yolov8_input.json

程序使用和 Python 摄像头 YOLOv8 相同的 BGR→RGB、黑边 letterbox/640×640 过程，保存恰好 1,228,800 字节的连续 UINT8 RGB HWC raw，同时保存原图宽高、缩放与填充参数和文件 SHA256。

**不要把 JPEG 文件直接传给 RKNPU2，也不要把已经除以 255 的 float32 再当 uint8 输入。** 必须确保模型转换时的 mean/std 约定与 Rockchip 官方优化版一致。

## 4. ROCK 5B：编译并执行真实 RKNPU2 C++ 检测

使用开发板上与镜像、驱动匹配的官方 rknn_api.h 和 ARM64 librknnrt.so：

    cmake -S examples/hardware -B build/native-rknn \
      -DRKNN_INCLUDE_DIR=/real/sdk/include \
      -DRKNN_LIB=/real/arm64/librknnrt.so
    cmake --build build/native-rknn --target rknn_yolov8_raw -j

在板上（要求路径是板端实际存在的文件）执行：

    ./build/native-rknn/rknn_yolov8_raw \
      /path/to/optimized_yolov8.rknn \
      build/yolov8_input.rgb \
      640 480 0.25 5 > build/yolov8_cpp_detections.json

640、480 必须替换为**原始图像**的宽和高，而不是改成模型输入尺寸；否则检测框无法正确映射回原图。建议使用上一步 JSON manifest 中的 source_width/source_height。程序不接收 `--image` 或摄像头文件夹；这里只是对已经预处理好的 raw 执行真实 NPU 推理。

输出包含 class_id、score、xyxy 和多次 rknn_run + outputs_get 的平均墙钟毫秒，**不包含图像采集、预处理和 C++ 解码时间**；因此不能当作整机 FPS，也不能把此项平均时延与 Python 摄像头同步 FPS 直接比较。

## 5. V4L2 DMA-BUF：先确认硬件支持什么

在 ROCK 5B 上使用 Linux 的 V4L2 开发头文件编译：

    g++ -std=c++17 -O2 -Wall -Wextra -Werror \
      boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp \
      -o build/v4l2_dma_probe
    ./build/v4l2_dma_probe /dev/video0

此工具通过 VIDIOC_QUERYCAP/VIDIOC_G_FMT 检查单平面采集节点，然后申请 V4L2_MEMORY_MMAP 缓冲区，并用 VIDIOC_EXPBUF 将其导出为 fd，随后关闭全部 fd 并释放 V4L2 buffers。**仅证明驱动可能支持导出，不采集一帧、不执行 RGA、不执行 NPU**。MJPEG/H.264 输出即使导出 fd 仍须解码，不能当 RGB 原始图像直接送 RGA。

注意概念区别：V4L2_MEMORY_MMAP + VIDIOC_EXPBUF 是**由 V4L2 分配后导出**，V4L2_MEMORY_DMABUF 则是**由外部提供 DMA-BUF 并交给 V4L2 导入**。不能混写 ioctl；摄像头、RGA、NPU 三方共享同一缓冲区还需要格式/stride、fd 生命周期、同步 fence、cache coherency、SDK binding 与实际数据内容检查。

## 6. 验收边界、仍待完成

| 检查项 | 当前证明 |
|---|---|
| C++ FP32 DFL+NMS 同 Python | CI 使用数值张量文件逐项比较，已通过 |
| C++ RKNPU2 API、张量查询和释放 | 编译使用官方头文件，CPU 模拟 Runtime 测完成路径和失败路径 |
| ROCK 5B 真正运行优化版 .rknn | 待有设备、模型、匹配驱动/Runtime 后取得原始日志 |
| V4L2 单平面 DMA-BUF 导出 | C++ 实现了真实 ioctl 探测，待实体 UVC 或 CSI 节点验证 |
| 实时 C++ 摄像头画框、RGA/DMA-BUF 到 NPU | **尚未实现**；当前 Python 摄像头应用能完成 CPU 预处理+NPU+画框 |

建议实机记录 ROCK 5B 板型、镜像版本、rknpu 驱动、librknnrt.so SHA256、优化版 Model Zoo commit、真实模型 SHA256、图片、stdout、每张图的检测框，以及与同一模型同一输入下 Python 的 IoU/分类一致性。不要将模拟 SDK 的输出或合成 DFL 张量记作设备性能。

