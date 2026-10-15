# 实例 12：Netron 辅助检查 ONNX

理论内容：[Netron的基本使用](../../docs/12_Netron%E7%9A%84%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

pip install onnx；需要真实 ONNX 图。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_12.py --onnx model.onnx --output build/lesson12/graph.json
```

`python3 examples/lesson_12.py --help` 查看其他参数。

## 预期结果与检查方法

真实算子计数、静/动态维度及输入输出列表。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
