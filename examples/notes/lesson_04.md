# 实例 04：锁定官方仓库代码版本

对应理论教材：[瑞芯微github仓库介绍](../../docs/04_%E7%91%9E%E8%8A%AF%E5%BE%AEgithub%E4%BB%93%E5%BA%93%E4%BB%8B%E7%BB%8D.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+、Git、联网。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_04.py --repo toolkit2 --ref HEAD --output build/upstream.json
```

查看可配置参数：`python3 examples/lesson_04.py --help`。

## 输出与验收

git ls-remote 的实际提交 SHA；联网失败给错误。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
