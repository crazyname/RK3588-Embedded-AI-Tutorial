# 实例 11：批量 RKNN 转换任务

理论内容：[模型转换工具rknn · convert](../../docs/11_%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2%E5%B7%A5%E5%85%B7rknn_convert.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

主机 Toolkit2、真实 ONNX、逐任务 JSON。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_11.py --jobs jobs.json --log-dir build/lesson11
```

`python3 examples/lesson_11.py --help` 查看其他参数。

## 预期结果与检查方法

每个真实转换进程的退出码和日志，可追溯失败原因。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
