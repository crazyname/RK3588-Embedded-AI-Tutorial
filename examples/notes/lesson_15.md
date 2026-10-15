# 实例 15：外部程序性能分布

理论内容：[模型性能评估](../../docs/15_%E6%A8%A1%E5%9E%8B%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

实际可执行推理 Demo 与输入。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_15.py --runs 30 --warmup 3 -- ./rknn_demo model.rknn bell.jpg
```

`python3 examples/lesson_15.py --help` 查看其他参数。

## 预期结果与检查方法

保存真实进程墙钟时间，p50/p95 与 CSV。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
