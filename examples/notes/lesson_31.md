# 实例 31：YOLO 数据标注验收与训练

[对应课程理论教材](../../docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E6%95%B0%E6%8D%AE%E9%9B%86%E6%9E%84%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

真实 labels/ 与 data.yaml；训练时需要权重与 Ultralytics。

## 启动命令

```bash
python3 examples/lesson_31.py --labels dataset/labels/train --report build/dataset_audit.json
```

所有选项：`python3 examples/lesson_31.py --help`。

## 输出和验收

标注违规行、有效框数量；加 --train 真实启动训练。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。
