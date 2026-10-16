# ROCK 5B：C++ RKNPU2 输入绑定与 RGA 图像缩放

这是对应第25、26讲的板级实验，分为两个**独立可执行的 C++ 程序**：一个比较同模型的标准输入与 SDK 输入内存绑定；另一个使用 librga 缩放 RGB888 并通过 CPU 合成黑边。当前没有实现摄像头 DMA-BUF 到 NPU 的端到端零拷贝。

## 官方 API 与源码

- [RK3588 官方 RKNPU2 SDK](https://github.com/rockchip-linux/rknpu2/tree/master/runtime/RK3588/Linux/librknn_api/include)：包括 rknn_inputs_set、rknn_create_mem、rknn_set_io_mem、rknn_outputs_get。
- [官方 librga](https://github.com/airockchip/librga)：包括 im2d.hpp、importbuffer_virtualaddr、wrapbuffer_handle、imcheck 和 imresize。
- [分类模型输入方式对照](../../examples/hardware/rknn_compare_input_io.cpp)：比较两个输入方式的输出数值和 p50/p95。
- [RGA RGB888 letterbox 程序](../../examples/hardware/rga_letterbox_rgb888.cpp)：将 packed RGB 缩放/黑色填充到 640x640，并生成 raw 文件。
- [PC 对照误差检测](../../tools/compare_rga_letterbox.py)：对真实 RGA 输出文件做 OpenCV 参考与像素误差检查。

## 编译（需要真正的 RK3588 SDK/库）

从本仓库根目录，用 ROCK 5B 板端编译器或适配 ARM64 的交叉工具链运行：

    cmake -S examples/hardware -B build/native-rknn \
      -DRKNN_INCLUDE_DIR=/sdk/rknpu2/include \
      -DRKNN_LIB=/sdk/librknnrt.so \
      -DRGA_INCLUDE_DIR=/sdk/librga/include \
      -DRGA_LIB=/sdk/librga.so
    cmake --build build/native-rknn -j

必须根据官方当前 SDK 把占位绝对路径替换为实际文件。没有 RGA 时省略两个 RGA 参数，仍可单独编译 RKNPU2 程序。主机 x86 的语法检查不代表链接出的二进制能在 ARM64 上运行。

## 同模型 RKNPU2 标准输入 vs. SDK 绑定输入

只适用于**一输入、一输出、UINT8 NHWC** 分类模型，不支持九输出 YOLOv8。先准备与此模型预处理完全一致的紧密排列 RGB raw（不是 PNG 或 JPEG）：

    ./build/native-rknn/rknn_compare_input_io \
      /path/to/mobilenet.rknn /path/to/rgb_uint8_nhwc.raw 20 5

第一组使用 rknn_inputs_set，第二组使用 rknn_create_mem + CPU memcpy + rknn_set_io_mem 绑定输入。两组均用 rknn_outputs_get 取回 float32 输出，在同模型同输入下验证 atol=0.01/rtol=0.01，显示 mean、p50、p95 API 墙钟耗时。若模型原生输入需要 stride/padding 而无法安全直接映射，程序会明确拒绝，不会误用紧密排列数据。匹配失败返回退出码 3。

本程序只绑定**输入内存**；模型数据先 CPU memcpy 到 SDK 内存，输出仍由 SDK 复制到用户数据缓冲，**不属于端到端零拷贝**。目前先测标准路径、再测绑定路径，温度或调度顺序可能引入偏差，正式测试应换序重复并记录温度。

## librga 图像缩放 + 640 黑边

准备 640x480 RGB888 原始输入，注意是 RGB 而非摄像头常见的 BGR：

    python3 examples/hardware/prepare_image.py \
      --image test.jpg --width 640 --height 480 \
      --color RGB --layout NHWC --dtype uint8 \
      --output build/rga-input.npy --raw build/rga-input.rgb

在有正确 librga Runtime 和 RGA 驱动的 ROCK 5B 上运行：

    ./build/native-rknn/rga_letterbox_rgb888 \
      build/rga-input.rgb 640 480 build/rga-output.rgb 20

输出是严格 RGB888 packed 的 640x640 原始数据，共 1,228,800 字节。RGA 完成缩放；黑边合成依旧是 CPU memcpy。RGA 通过 virtualaddr 导入数据，也不是摄像头 DMA-BUF。

在主机上对照 OpenCV（允许自行定义像素平均绝对误差阈值）：

    python3 tools/compare_rga_letterbox.py \
      --input-rgb build/rga-input.rgb \
      --rga-rgb build/rga-output.rgb \
      --width 640 --height 480 --max-mean-error 3

工具核对输出尺寸、黑边、缩放区域均值误差、最大误差与文件 SHA256。它不能独立证明文件真的由 RGA 设备产生；必须附板端原始日志、库版本和图像产物。

## 验收状态与下一步

| 项目 | 已完成 | 仍需完成 |
|---|---|---|
| C++ RKNN 输入对照 | 官方头文件语法检查、CPU mock 真二进制执行、输出相等断言 | ROCK 5B 实板链接/模型/性能 |
| RGA 缩放 | 官方 librga 头文件语法检查、OpenCV 对照工具与4项单元测试 | 驱动上的真实 imresize 调用、误差采样 |
| YOLOv8 C++ 多输出解码 | 无，已有独立 Python 版 | 按模型版本编写原生后处理并验收 |
| 摄像头 V4L2 DMA-BUF → RGA → NPU | 未实现 | fd、stride、buffer 生命周期与缓存同步、带宽/延迟验收 |

报告应保存：ROCK 5B PCB/Kernel/BSP、RKNPU Driver/Runtime、librga 版本、模型及输入 SHA256、每次执行原始 stdout、两条路径输出误差/p50/p95 和设备温度。不能把 CPU mock 的执行成功解释为真实 NPU 性能。

