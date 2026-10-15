# 实例 29：YOLOv5 真实图像检测

[对应课程理论教材](../../docs/29_yolov5%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E5%AE%9E%E6%88%98.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

Ultralytics 及真实 pt/onnx 权重，或配套 Model Zoo RKNN 演示程序。

## 启动命令

```bash
python3 examples/lesson_29.py --engine ultralytics --model yolov5.pt --image test.jpg
```

所有选项：`python3 examples/lesson_29.py --help`。

## 输出和验收

保存每条真实框的坐标、得分和画框图片；RKNN 模式调用实际官方 binary。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。
