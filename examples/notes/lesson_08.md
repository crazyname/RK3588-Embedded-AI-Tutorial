# 实例 08：真正调用 Model Zoo 外部 Demo

对应理论教材：[快速体验rknn · demo](../../docs/08_%E5%BF%AB%E9%80%9F%E4%BD%93%E9%AA%8Crknn_demo.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

需要自己构建的可执行 Demo、真实模型与图片。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_08.py --program ./rknn_mobilenet_demo --model model.rknn --image bell.jpg
```

查看可配置参数：`python3 examples/lesson_08.py --help`。

## 输出与验收

输出真实子进程返回码和日志；没有依赖时明确失败。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
