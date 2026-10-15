# 实例 06：板端驱动及 Runtime 检查

对应理论教材：[设备端npu环境搭建与npu驱动更新](../../docs/06_%E8%AE%BE%E5%A4%87%E7%AB%AFnpu%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8Enpu%E9%A9%B1%E5%8A%A8%E6%9B%B4%E6%96%B0.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Linux 开发板；可选 Runtime SO 文件。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_06.py --runtime /path/to/librknnrt.so
```

查看可配置参数：`python3 examples/lesson_06.py --help`。

## 输出与验收

只读输出版本、NPU 节点、动态库架构，不刷写系统。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
