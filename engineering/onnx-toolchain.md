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

## 自动化测试

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`examples/tests/test_lesson_27.py`](../examples/tests/test_lesson_27.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

同一 ONNX 在 ONNX Runtime 的输入输出形状、数值和 .rknn 编译日志必须分别保存。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

ONNX checker/ONNX Runtime 成功不表示 RKNN 转换和实机推理通过。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
