# 实例 05：RKNN 开发主机环境核查

对应理论教材：[搭建rknn · toolkit2开发环境](../../docs/05_%E6%90%AD%E5%BB%BArknn_toolkit2%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+，可选已装 Toolkit2。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_05.py --output build/toolkit_env.json
```

查看可配置参数：`python3 examples/lesson_05.py --help`。

## 输出与验收

检测 Python ABI 与导入结果；加 --require-toolkit 严格验收。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
