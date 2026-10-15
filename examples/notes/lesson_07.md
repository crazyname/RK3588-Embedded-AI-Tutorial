# 实例 07：频率与温度时间序列

对应理论教材：[查看和调整CPU · NPU · DDR频率](../../docs/07_%E6%9F%A5%E7%9C%8B%E5%92%8C%E8%B0%83%E6%95%B4CPU_NPU_DDR%E9%A2%91%E7%8E%87.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Linux /sys 可读，Python 3.9+。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_07.py --samples 10 --interval 1
```

查看可配置参数：`python3 examples/lesson_07.py --help`。

## 输出与验收

CSV 实际节点采样，没有节点时明确报告。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
