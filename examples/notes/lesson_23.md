# 实例 23：从 ONNX 生成真实 C++ 模型接口头

理论与技术背景：[自动生成部署C代码](../../docs/23_%E8%87%AA%E5%8A%A8%E7%94%9F%E6%88%90%E9%83%A8%E7%BD%B2C%E4%BB%A3%E7%A0%81.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install onnx；--compile 需 g++。

## 执行

```bash
python3 examples/lesson_23.py --onnx model.onnx --compile
```

完整参数运行 `python3 examples/lesson_23.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

生成真实输入输出 shape/dtype 的 C++17 声明，非完整推理器。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
