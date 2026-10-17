# 实例 33：YOLOv8 两模型实际对比

[对应课程理论教材](../../docs/31_yolov8%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BC%98%E5%8C%96%E5%8A%A0%E9%80%9F%E7%89%88%29.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

两个真实模型文件与一组相同的真实图片。

## 启动命令

```bash
python3 examples/lesson_33.py --baseline old.pt --optimized new.pt --images a.jpg b.jpg
```

所有选项：`python3 examples/lesson_33.py --help`。

## 输出和验收

实际推理总时延、框数差异和加速比，不当作 RK3588 NPU benchmark。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。

## ROCK 5B USB 摄像头 YOLOv8 实时检测工程

- [真实 RKNNLite 摄像头检测主程序](../../boards/radxa-rock5b/apps/camera_yolov8_lite.py)
- [独立 NumPy DFL/letterbox/NMS 源码](../../boards/radxa-rock5b/apps/yolov8_rknn_postprocess.py)
- [模型协议、运行步骤和真实板端验收](../../boards/radxa-rock5b/CAMERA_YOLOV8.md)

这是单独的**目标检测系统**，不能与本讲的 PC Ultralytics 性能比较混为一谈。严格使用官方优化版 Model Zoo 9/6 输出模型；普通 YOLOv8 ONNX 单输出结构不适用。CI 使用模型形状正确的 NumPy 张量和明确模拟的 SDK 测试数学与异常路径，设备性能需要另行实测。

## 原生 C++ RKNPU2 YOLOv8 多输出实操

请参照 [ROCK 5B C++ YOLOv8 与 DMA-BUF 实验说明](../../boards/radxa-rock5b/CPP_YOLOV8_NATIVE.md)。配套 [NPU C API 主程序](../hardware/rknn_yolov8_raw.cpp)、[DFL/NMS C++ 后处理](../hardware/yolov8_postprocess.cpp) 与 [真实 RKNNLite 输出 NPZ → C++ FP32 兼容导出](../../tools/export_yolov8_fp32.py)。此项目要求 Model Zoo 优化版 6/9 输出，不能把普通 ONNX 模型输出强行 reshape。尚待 ROCK 5B 实机验收。
