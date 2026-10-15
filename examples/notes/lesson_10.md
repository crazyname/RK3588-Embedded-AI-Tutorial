# 实例 10：图像 mean/std 与 RGB 数值

理论内容：[均值和标准差](../../docs/10_%E5%9D%87%E5%80%BC%E5%92%8C%E6%A0%87%E5%87%86%E5%B7%AE.md)。这里专注**操作、产物和验收**，不复写课程原理。

## 先决条件

需 numpy、Pillow 与真实图片。如缺少 SDK、模型或者文件，程序应报错退出，不构造假数据（第17讲明确标记合成权重演示除外）。

## 可直接执行的命令

```bash
python3 examples/lesson_10.py --image bell.jpg --output build/lesson10/image.npy
```

`python3 examples/lesson_10.py --help` 查看其他参数。

## 预期结果与检查方法

产生 float32 输入张量及逐通道最大/最小值。应保留生成文件与运行日志；SDK 或 NPU 的具体支持必须在目标环境验证。

## 排错原则

先核对输入 tensor shape、dtype、model/SDK release 和命令返回码，再进行预处理或转换参数修正。更多背景与原理见课程 MD。
