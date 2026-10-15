# RK3588 嵌入式 AI：官方文档与参考书目

> 查阅时间：2026-10。软件接口、支持模型及系统版本可能调整。必须对照你实际安装的 SDK release。

## A. Rockchip 官方工具与示例

1. [RKNN-Toolkit2（维护中的仓库）](https://github.com/airockchip/rknn-toolkit2)：主机模型转换、量化、调试、Lite2 工具和 SDK 说明。旧 rockchip-linux/rknn-toolkit2 已标记迁移。
2. [Quick Start 与 RKNN User Guide](https://github.com/airockchip/rknn-toolkit2/tree/master/doc)：安装 wheel、检查 Python/OS 兼容、接口签名、性能与内存评估。
3. [RKNN Model Zoo](https://github.com/airockchip/rknn_model_zoo)：官方 MobileNet、YOLOv5、YOLOv8、C/C++ 和 Python 端侧示例。应使用同一版本配套的 ONNX/转换脚本/后处理代码。
4. [RKNPU2 C API 示例](https://github.com/rockchip-linux/rknpu2)：张量、输入输出、内存与零拷贝相关接口。具体签名以目标板 SDK 头文件为准。
5. [RKLLM 工具链](https://github.com/airockchip/rknn-llm)：RKLLM-Toolkit、Runtime、适配平台与支持模型家族。

## B. ONNX、训练框架与模型部署

6. [ONNX 文档](https://onnx.ai/onnx/) 与 [Shape Inference](https://github.com/onnx/onnx/blob/main/docs/ShapeInference.md)：graph、opset、shape、模型 checker 和静态推断。
7. [ONNX Runtime 官方文档](https://onnxruntime.ai/docs/) 与 [量化介绍](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)：模型功能回归、静态量化、误差调试。
8. [Netron 可视化](https://github.com/lutzroeder/netron)：打开 ONNX、查看节点、layout 和输入输出 tensor。
9. [Ultralytics 文档](https://docs.ultralytics.com/)：训练、数据格式、模型预测与 ONNX 导出。
10. [官方 YOLOv5 示例](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/yolov5) 与 [YOLOv8 示例](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/yolov8)：理解 Rockchip 优化输出与模型专用后处理。

## C. 推荐学习书籍

- **《动手学深度学习》（Dive into Deep Learning）**，Aston Zhang、Zack C. Lipton、Mu Li、Alex J. Smola 等；[中文版在线教材](https://d2l.com.cn/)。用于补线性代数、卷积、分类、目标检测和 Transformer。尤其推荐自己运行数学与 Python 代码。
- **《Deep Learning》**，Ian Goodfellow、Yoshua Bengio、Aaron Courville；MIT Press（2016），[作者公开的在线版本](https://www.deeplearningbook.org/)。重点选读数值计算、优化、正则化、CNN 和概率基础。
- **《Computer Systems: A Programmer's Perspective》**，Randal E. Bryant、David R. O'Hallaron；Pearson，第三版，[出版商页面](https://www.pearson.com/en-us/subject-catalog/p/computer-systems-a-programmers-perspective/P200000003479)。用于理解动态链接、内存层次、并发与程序性能；书中的 x86-64 实例不是 RK3588 ARM64 指令示例。
- **Linux kernel 文档**：[docs.kernel.org](https://docs.kernel.org/)：处理 CPU 频率、/proc、设备驱动与内存观测时查阅。
- **C++ Core Guidelines**：[isocpp.github.io](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)：学习 RAII、资源所有权、异常安全和代码封装。

## D. 如何判断资料可靠性

对于工具 API 与命令：当前 SDK 版本的官方 README、Quick Start 和本地 --help 优先于论坛/视频截图。对于基础理论：教材优先于零散的博客解释。对于性能与精度：你自己在目标板上、针对真实模型和输入采集的可复现日志优先于任何网上的标称 TOPS/FPS。不要直接照搬未经核查的刷机、频率和密钥命令。

本课程的正文为针对这些资料的原创教学整理，并未复制书籍原文。