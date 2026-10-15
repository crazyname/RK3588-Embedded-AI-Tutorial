# 实例 09：ONNX→RKNN 实际模型转换

理论内容：[rknn模型转换](../../docs/09_rknn%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

主机需安装 onnx 与匹配 RKNN-Toolkit2；必须有真实 ONNX。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_09.py --onnx model.onnx --output build/lesson09/model.rknn --mean 0,0,0 --std 1,1,1
```

`python3 examples/lesson_09.py --help` 查看其他参数。

## 预期结果与检查方法

合法 ONNX 转换成真实 .rknn 并保存双文件 SHA256。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
