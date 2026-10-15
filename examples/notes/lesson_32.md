# 实例 32：YOLO ONNX 与 RKNN 转换

[对应课程理论教材](../../docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2(%E4%BB%8E0%E5%88%B01%E7%89%88)_%E5%AF%BC%E5%87%BAonnx%E4%B8%8Erknn%E6%A8%A1%E5%9E%8B%E5%B9%B6%E6%9D%BF%E7%AB%AF%E6%8E%A8%E7%90%86.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

Ultralytics onnx，真实 .pt；可选主机 Toolkit2。

## 启动命令

```bash
python3 examples/lesson_32.py --weights best.pt --imgsz 640 --report build/conversion.json
```

所有选项：`python3 examples/lesson_32.py --help`。

## 输出和验收

ONNX checker、哈希、可选真实 RKNN build 返回情况。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。
