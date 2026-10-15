# 实例 16：Linux 进程内存分析

理论内容：[模型内存评估](../../docs/16_%E6%A8%A1%E5%9E%8B%E5%86%85%E5%AD%98%E8%AF%84%E4%BC%B0.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

Linux、/proc 与实际运行进程 PID。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_16.py --pid 1234 --samples 10 --interval 1
```

`python3 examples/lesson_16.py --help` 查看其他参数。

## 预期结果与检查方法

采集真实 VmRSS/VmHWM 时序表，不伪造 NPU 内存。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
