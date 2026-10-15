# 实例 22：保语义删除 ONNX Identity 算子

理论与技术背景：[ONNX模型编辑](../../docs/22_ONNX%E6%A8%A1%E5%9E%8B%E7%BC%96%E8%BE%91.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install onnx；建议另装 numpy onnxruntime 验证。

## 执行

```bash
python3 examples/lesson_22.py --onnx src.onnx --output stripped.onnx --input-npy input.npy
```

完整参数运行 `python3 examples/lesson_22.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

模型结构静态校验、实际输入的回归比较，通过后写新 ONNX。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
