# 实例 14：量化前后真实张量误差分析

理论内容：[模型量化精度分析](../../docs/14_%E6%A8%A1%E5%9E%8B%E9%87%8F%E5%8C%96%E7%B2%BE%E5%BA%A6%E5%88%86%E6%9E%90.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

pip install numpy；需要真实 FP 和 INT8 推理输出 NPZ。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_14.py --float fp.npz --quantized int8.npz --max-mae 0.1
```

`python3 examples/lesson_14.py --help` 查看其他参数。

## 预期结果与检查方法

真实 MAE/RMSE/余弦/Top1 对比，超阈值非零退出。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
