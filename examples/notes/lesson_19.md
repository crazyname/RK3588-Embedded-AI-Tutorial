# 实例 19：从真实图片组成多 Batch tensor

理论与技术背景：[多Batch处理](../../docs/19_%E5%A4%9ABatch%E5%A4%84%E7%90%86.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

pip install numpy pillow；四张图片。

## 执行

```bash
python3 examples/lesson_19.py --images a.jpg b.jpg c.jpg d.jpg --batch 4
```

完整参数运行 `python3 examples/lesson_19.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

保存 N×H×W×C 输入与映射 JSON；是否支持多Batch取决 RKNN 模型。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
