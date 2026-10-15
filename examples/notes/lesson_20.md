# 实例 20：多输入 ONNX Runtime 实际运行

理论与技术背景：[多输入模型](../../docs/20_%E5%A4%9A%E8%BE%93%E5%85%A5%E6%A8%A1%E5%9E%8B.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install numpy onnxruntime；模型和每个输入 .npy。

## 执行

```bash
python3 examples/lesson_20.py --onnx multi.onnx --inputs inputs.json
```

完整参数运行 `python3 examples/lesson_20.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

按模型真实输入名称绑定多条 tensor，结果保存 NPZ。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
