# 实例 03：模型部署链与依赖图

对应理论教材：[RKNPU推理软件架构与模型部署流程](../../docs/03_RKNPU%E6%8E%A8%E7%90%86%E8%BD%AF%E4%BB%B6%E6%9E%B6%E6%9E%84%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E6%B5%81%E7%A8%8B.md)。本页**只记录实操**，原理、拓展阅读和课堂测验以课程 MD 为准。

## 运行条件

Python 3.9+；可选 Graphviz。在仓库根目录操作。所有需要设备/互联网/模型的场景，缺失依赖时应报错，不产生模拟结果。

## 操作命令

```bash
python3 examples/lesson_03.py --dot build/lesson03/pipeline.dot
```

查看可配置参数：`python3 examples/lesson_03.py --help`。

## 输出与验收

DOT 图包含各流程节点，状态只能根据自测结果填写。检查程序实际 stdout / JSON / CSV 和退出状态；不能把主机模拟值作为 RK3588 实机性能数据。

## 故障定位

先检查 `--help`、目标文件权限、操作系统与依赖版本，再定位错误码；硬件相关的版本兼容性以当前 BSP/SDK 为准。
