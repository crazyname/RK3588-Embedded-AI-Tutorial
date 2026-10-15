# 实例 02：卷积与深度可分离计算量

对应理论教材：[NPU原理及对比](../../docs/02_NPU%E5%8E%9F%E7%90%86%E5%8F%8A%E5%AF%B9%E6%AF%94.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_02.py --height 224 --width 224 --in-channels 32 --out-channels 64
```

查看可配置参数：`python3 examples/lesson_02.py --help`。

## 输出与验收

JSON 包含两个结构真实 MAC 及加速比公式。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
