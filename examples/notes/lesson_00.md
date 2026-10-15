# 实例 00：环境信息采集

对应理论教材：[导学](../../docs/00_%E5%AF%BC%E5%AD%A6.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_00.py --output build/lesson00/environment.json
```

查看可配置参数：`python3 examples/lesson_00.py --help`。

## 输出与验收

JSON 内有系统、Python、Git/CMake 版本；模型可选 sha256。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
