# 实例 24：RK3588 Toolkit-Lite2 推理

理论与技术背景：[RKNN-ToolkitLite2基本使用](../../docs/24_RKNN-ToolkitLite2%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

板端匹配 RKNNLite、真实 .rknn 和输入 .npy。

## 执行

```bash
python3 examples/lesson_24.py --rknn model.rknn --input-npy x.npy
```

完整参数运行 `python3 examples/lesson_24.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

使用真实 NPU runtime 保存输出和调用延时；尚无实机结果。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
