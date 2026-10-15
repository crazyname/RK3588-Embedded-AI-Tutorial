# 实例 13：RKNN Toolkit2 模拟/设备推理

理论内容：[rknn-toolkit2模型推理](../../docs/13_rknn-toolkit2%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

匹配的 Toolkit2、真实 RKNN、正确 .npy 输入。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_13.py --rknn model.rknn --input-npy input.npy --target simulator
```

`python3 examples/lesson_13.py --help` 查看其他参数。

## 预期结果与检查方法

真实输出 NPZ 与 SDK 调用延迟；模拟器时延非 NPU 实测。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
