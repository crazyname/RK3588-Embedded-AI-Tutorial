# 实例 01：设备信息与 CPU 架构

对应理论教材：[快速了解rk3588](../../docs/01_%E5%BF%AB%E9%80%9F%E4%BA%86%E8%A7%A3rk3588.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+；板端 Linux 能提供更多信息。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_01.py --output build/lesson01/board.json
```

查看可配置参数：`python3 examples/lesson_01.py --help`。

## 输出与验收

设备树可读时包含板卡型号，不伪造 RK3588 身份。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
