# USB 摄像头 YOLOv8 检测：独立工程实验与验收

> 工程编号：`yolov8-camera`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/31_yolov8模型部署(优化加速版).md](../docs/31_yolov8模型部署(优化加速版).md) · [HTML 连续滚动课件](../courseware/lessons/31_yolov8模型部署(优化加速版).html)

## 源码清单

- [`boards/radxa-rock5b/apps/camera_yolov8_lite.py`](../boards/radxa-rock5b/apps/camera_yolov8_lite.py)
- [`boards/radxa-rock5b/apps/yolov8_rknn_postprocess.py`](../boards/radxa-rock5b/apps/yolov8_rknn_postprocess.py)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
python3 boards/radxa-rock5b/apps/camera_yolov8_lite.py --help
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 最小完整板端实验

使用 [YOLOv8 优化版模型](../boards/radxa-rock5b/CAMERA_YOLOV8.md) 的约定输出头，不可直接替换成 YOLO26 或普通 Ultralytics 导出的任意 RKNN。USB 摄像头应可读取 `/dev/video0`，模型输入为 640。

```bash
python3 boards/radxa-rock5b/tools/usb_camera_check.py --help
python3 boards/radxa-rock5b/apps/camera_yolov8_lite.py \
  --model /path/to/optimized-yolov8n.rknn \
  --source /dev/video0 --size 640 --frames 30 --warmup 0 \
  --labels boards/radxa-rock5b/assets/coco80.txt \
  --jsonl /tmp/yolov8-frames.jsonl --confirm-optimized-yolov8
```

数据链：V4L2 捕获 BGR 帧→RGB/letterbox（保留缩放和 padding）→RKNN 推理→对应输出头 DFL 解码→阈值/NMS→按 padding 与缩放还原原图像素坐标。验收至少检查一帧类别索引在 0–79 内、框未越界，并保留真实 JSONL。若没有检测目标，可仅判定采集与推理链路正常，不能编造检出框。

## 自动化测试

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`boards/radxa-rock5b/tests/test_camera_yolov8.py`](../boards/radxa-rock5b/tests/test_camera_yolov8.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

校验 RGB、letterbox、输出头布局、DFL/NMS、原图边界框、FPS/p95 和类别映射。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

仅适配文档规定的 Model Zoo 优化版输出；测试不代表实机 mAP。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
