# 实例 28：模块化 MobileNet 批量图片分类

[对应课程理论教材](../../docs/28_mobilenet%E6%A8%A1%E5%9E%8B%E4%BB%A3%E7%A0%81%E5%B0%81%E8%A3%85.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

真实 MobileNet ONNX、图片、可选类别文件，需 numpy Pillow onnxruntime。

## 启动命令

```bash
python3 examples/lesson_28.py --onnx mobilenet.onnx --images bell.jpg dog.jpg --labels synset.txt
```

所有选项：`python3 examples/lesson_28.py --help`。

## 输出和验收

分类封装对象、逐图片 Top-K、模型输出与标签检查。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。
