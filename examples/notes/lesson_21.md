# 实例 21：不同输入形状真实 ONNX 执行

理论与技术背景：[动态shape输入](../../docs/21_%E5%8A%A8%E6%80%81shape%E8%BE%93%E5%85%A5.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install numpy onnxruntime；支持动态 shape 的模型与多份 .npy。

## 执行

```bash
python3 examples/lesson_21.py --onnx dynamic.onnx --inputs x320.npy x640.npy
```

完整参数运行 `python3 examples/lesson_21.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

每种 shape 的结果及运行时间输出 CSV；不能证明 RKNN 动态shape。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
