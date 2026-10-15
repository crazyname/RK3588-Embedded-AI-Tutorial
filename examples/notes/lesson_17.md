# 实例 17：真实张量权重结构剪枝

理论内容：[模型剪枝](../../docs/17_%E6%A8%A1%E5%9E%8B%E5%89%AA%E6%9E%9D.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

pip install numpy；可指定实际 conv1/conv2 权重 NPZ。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_17.py --keep-ratio 0.75 --output build/lesson17/pruned.npz
```

`python3 examples/lesson_17.py --help` 查看其他参数。

## 预期结果与检查方法

产出剪掉通道后的权重文件；无 --weights 时明确使用合成权重。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
