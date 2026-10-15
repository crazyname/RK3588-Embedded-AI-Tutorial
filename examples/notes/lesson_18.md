# 实例 18：真正使用 Fernet 认证加密与解密

理论与技术背景：[模型加密](../../docs/18_%E6%A8%A1%E5%9E%8B%E5%8A%A0%E5%AF%86.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install cryptography；生产密钥勿放公共 Git。

## 执行

```bash
python3 examples/lesson_18.py generate-key --key-file build/test.key
```

完整参数运行 `python3 examples/lesson_18.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

随后用 encrypt/decrypt --input/--output 真实文件，比较 SHA256；这不是 RKNN SDK 原生加密格式。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
