# ONNX 基准模型与部署转换：独立工程实验与验收

> 工程编号：`onnx-toolchain`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/09_rknn模型转换.md](../docs/09_rknn模型转换.md) · [HTML 连续滚动课件](../courseware/lessons/09_rknn模型转换.html)
- [Markdown：docs/13_rknn-toolkit2模型推理.md](../docs/13_rknn-toolkit2模型推理.md) · [HTML 连续滚动课件](../courseware/lessons/13_rknn-toolkit2模型推理.html)
- [Markdown：docs/27_mobilenet模型部署.md](../docs/27_mobilenet模型部署.md) · [HTML 连续滚动课件](../courseware/lessons/27_mobilenet模型部署.html)

## 源码清单

- [`examples/hardware/create_tiny_onnx.py`](../examples/hardware/create_tiny_onnx.py)
- [`examples/hardware/onnx_reference.py`](../examples/hardware/onnx_reference.py)
- [`examples/hardware/convert_onnx.py`](../examples/hardware/convert_onnx.py)
- [`examples/hardware/lite_infer.py`](../examples/hardware/lite_infer.py)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
python3 examples/hardware/create_tiny_onnx.py --help
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 可执行转换路径

使用仓库自己的 Tiny CNN 做**工具链通路教学**（不是 MobileNet 准确率演示）。普通 PC 安装 `onnx`、`onnxruntime` 与 NumPy；RKNN 转换需额外在兼容 Linux x86_64 环境安装对应 Toolkit2。先查看各脚本参数，再执行实际转换：

```bash
python3 examples/hardware/create_tiny_onnx.py --help
python3 examples/hardware/onnx_reference.py --help
python3 examples/hardware/convert_onnx.py --help
python3 examples/hardware/convert_onnx.py \
  --onnx /path/to/tiny.onnx --output /path/to/tiny.rknn \
  --mean 0,0,0 --std 1,1,1
```

这里 `--mean/--std` 必须与生成 ONNX 时的实际输入协议一致；例子展示不量化的转换入口，量化需另备真实校准集与 `--quantize --dataset`。保存 `load_onnx/build/export_rknn` 的执行日志、输入 shape、导出文件；单纯 ONNX Runtime 运行不等于 RKNN 转换成功。

## 从零生成模型到转换

仓库内置 Tiny CNN，输入 NCHW float32 (1,3,4,4)，输出 (1,2)，是验证工具链的教学模型，不是 MobileNet。

~~~bash
mkdir -p build/tutorial-tiny
python3 examples/hardware/create_tiny_onnx.py --onnx build/tutorial-tiny/tiny.onnx --input-npy build/tutorial-tiny/input.npy --input-raw build/tutorial-tiny/input.raw
python3 examples/hardware/onnx_reference.py --onnx build/tutorial-tiny/tiny.onnx --input-npy build/tutorial-tiny/input.npy --output build/tutorial-tiny/reference.npz
~~~

第一步要求 PC 安装 numpy、onnx；第二步还需 onnxruntime。生成器定义的理论输出是 [[0.5, 0.25]]，需对照实际本机日志确认。之后在已安装兼容 RKNN Toolkit2 的 Linux x86_64 主机尝试转换：

~~~bash
python3 examples/hardware/convert_onnx.py --onnx build/tutorial-tiny/tiny.onnx --output build/tutorial-tiny/tiny.rknn --mean 0,0,0 --std 1,1,1
~~~

这里先不量化；mean/std 必须符合图的 float 输入协议，转换是否支持该图以真实 SDK 日志为准。INT8 需另外准备代表性数据集；ONNX Runtime 的成功不能证明 RKNN 推理成功。

## 自动化测试

- [新增专项行为测试](../tools/tests/test_engineering_image_io.py)

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`examples/tests/test_lesson_27.py`](../examples/tests/test_lesson_27.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

同一 ONNX 在 ONNX Runtime 的输入输出形状、数值和 .rknn 编译日志必须分别保存。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

ONNX checker/ONNX Runtime 成功不表示 RKNN 转换和实机推理通过。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
