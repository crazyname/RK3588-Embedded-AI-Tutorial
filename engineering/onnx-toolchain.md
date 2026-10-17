# 实验 A｜从 Tiny ONNX 到 RKNN

本实验只验证工具链。Tiny CNN 由仓库代码生成，输入为 float32 NCHW (1,3,4,4)，输出为 (1,2)。它不是 MobileNet，也不具有真实图片识别能力。

## 对应课程讲义与 HTML 课件

- [第09讲教材](../docs/09_rknn模型转换.md) · [HTML](../courseware/lessons/09_rknn模型转换.html)
- [第13讲教材](../docs/13_rknn-toolkit2模型推理.md) · [HTML](../courseware/lessons/13_rknn-toolkit2模型推理.html)
- [第27讲教材](../docs/27_mobilenet模型部署.md) · [HTML](../courseware/lessons/27_mobilenet模型部署.html)

## 源码清单

- [生成固定 ONNX 和输入](../examples/hardware/create_tiny_onnx.py)
- [ONNX Runtime 参考推理](../examples/hardware/onnx_reference.py)
- [Toolkit2 转换](../examples/hardware/convert_onnx.py)
- [板端 RKNNLite 通用张量推理](../examples/hardware/lite_infer.py)

## 环境与输入

PC 需要 Python、NumPy、onnx、onnxruntime。转换另需适配 Linux x86_64 的 RKNN-Toolkit2；板端使用 RKNNLite2，不能混装工具链。

## 实验命令

先在仓库根目录完成 PC 部分：

~~~bash
mkdir -p build/tutorial-tiny
python3 examples/hardware/create_tiny_onnx.py --onnx build/tutorial-tiny/tiny.onnx --input-npy build/tutorial-tiny/input.npy --input-raw build/tutorial-tiny/input.raw
python3 examples/hardware/onnx_reference.py --onnx build/tutorial-tiny/tiny.onnx --input-npy build/tutorial-tiny/input.npy --output build/tutorial-tiny/reference.npz
~~~

固定输入下，代码计算的预期输出是 [[0.5, 0.25]]。用真实输出检查，不可把该数值写成已经运行过的 NPU 结果。

在安装官方 Toolkit2 的 x86_64 Linux 主机继续：

~~~bash
python3 examples/hardware/convert_onnx.py --onnx build/tutorial-tiny/tiny.onnx --output build/tutorial-tiny/tiny.rknn --mean 0,0,0 --std 1,1,1
~~~

过程依次是 config → load_onnx → build(非量化) → export_rknn。mean/std 要匹配 ONNX 输入协议，遇编译失败记录真实算子日志。转换成功后如要上板，先查询 RKNN 实际输入 dtype/layout，再使用 lite_infer.py 对已经按该协议准备的 .npy 运行。

## 自动化测试

- [第27讲主机模型测试](../examples/tests/test_lesson_27.py)
- [图像 I/O 测试](../tools/tests/test_engineering_image_io.py)

## 验收标准

确认实际 ONNX 文件和固定 NPY 存在，ONNX Runtime 输出 shape 与数值正确；只有 Toolkit2 实际生成有效 RKNN 且日志返回成功才可勾选转换完成。量化与精度分析另做，不能用随机校准输入替代真实数据。

## 验证边界

本教程没有在此环境执行 RK3588 NPU。ONNX 正确、RKNN 导出正确、ROCK 5B 推理正确是三个不同检查点。

