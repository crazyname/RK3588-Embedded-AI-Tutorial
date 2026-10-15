# 实例 33：YOLOv8 两模型实际对比

[对应课程理论教材](../../docs/31_yolov8%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2(%E4%BC%98%E5%8C%96%E5%8A%A0%E9%80%9F%E7%89%88).md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

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
