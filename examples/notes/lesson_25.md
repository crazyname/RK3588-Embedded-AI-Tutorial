# 实例 25：RKNPU2 C API 编译运行

理论与技术背景：[RKNPU2—通用C API](../../docs/25_RKNPU2%E2%80%94%E9%80%9A%E7%94%A8C%20API.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

RK3588 ARM64 Linux、CMake、编译器与 SDK。

## 执行

```bash
python3 examples/lesson_25.py --include /sdk/include --library /sdk/librknnrt.so --model m.rknn --tensor input.raw
```

完整参数运行 `python3 examples/lesson_25.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

真正执行 CMake 编译与 RKNPU2 分类样例，异常退出非零。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。
