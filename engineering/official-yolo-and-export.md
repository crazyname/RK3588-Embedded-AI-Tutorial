# 官方 YOLOv8 基线与 ONNX 导出：独立工程实验与验收

## 对应课程讲义与 HTML 课件

- [Markdown：docs/29_yolov5模型部署实战.md](../docs/29_yolov5模型部署实战.md) · [HTML 连续滚动课件](../courseware/lessons/29_yolov5模型部署实战.html)
- [Markdown：docs/30_yolov26模型部署(从0到1版)_数据集构建与模型训练.md](../docs/30_yolov26模型部署(从0到1版)_数据集构建与模型训练.md) · [HTML 连续滚动课件](../courseware/lessons/30_yolov26模型部署(从0到1版)_数据集构建与模型训练.html)

## 源码清单
- [`boards/radxa-rock5b/tools/run_official_yolov8.py`](../boards/radxa-rock5b/tools/run_official_yolov8.py)
- [`examples/hardware/export_yolo_onnx.py`](../examples/hardware/export_yolo_onnx.py)
- [`examples/hardware/prepare_image.py`](../examples/hardware/prepare_image.py)

## 环境和输入
准备与 Rockchip 官方 release 匹配的 SDK、对应目标板与真实模型，固定输入图像、转换参数、模型 SHA256 和板端 Runtime 版本。不要将构建示例中的 SDK 路径作为实际存在的默认路径。

## 实验命令
```bash
python3 boards/radxa-rock5b/tools/run_official_yolov8.py --help
```

板端编译与执行必须结合 [ROCK 5B 手册](../boards/radxa-rock5b/README.md) 和 [C++ RGA 输入对照](../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md)。构建前替换 SDK include/lib 为实际 ARM64 文件；保留 stdout、stderr、输入图、模型哈希及错误日志。

## 自动化测试
- [`boards/radxa-rock5b/tests/test_board_tools.py`](../boards/radxa-rock5b/tests/test_board_tools.py)
- [`tools/tests/test_export_yolov8_fp32.py`](../tools/tests/test_export_yolov8_fp32.py)

上列测试为现有交叉参考入口，**不能据此断言该 C++ 工程已有专属功能测试**。必须补实际硬件测试，涉及代码行为的离线单元测试应逐步新增。

## 验收标准
保存官方运行命令、模型权重来源、导出 ONNX 的 opset、图像预处理协议和真实检测结果；不能用帮助信息代替上板基线。将对照值、测试样本和期望结果存储在本地 results 目录，区分成功、失败和未测试状态。

## 验证边界
导出为 ONNX 不是 RKNN 兼容认证，官方模型必须按实际 Model Zoo release 对照。**硬件验收状态：待实际 ROCK 5B 日志**。模拟/编译/CLI 成功不是板端验收。
