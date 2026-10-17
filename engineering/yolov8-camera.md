# 实验 D｜USB 摄像头 YOLOv8 检测

目标：在 ROCK 5B 读取真实视频帧，使用 RKNNLite 推理并完成 letterbox、DFL 解码、NMS 和原图框还原。采用 Rockchip Model Zoo 优化版 YOLOv8，不能混用 YOLO26 检测头。

## 对应课程讲义与 HTML 课件

- [第31讲 YOLOv8](../docs/31_yolov8模型部署%28优化加速版%29.md) · [连续滚动 HTML](../courseware/lessons/31_yolov8模型部署%28优化加速版%29.html)

## 源码清单

- [摄像头检测入口](../boards/radxa-rock5b/apps/camera_yolov8_lite.py)
- [NumPy 后处理](../boards/radxa-rock5b/apps/yolov8_rknn_postprocess.py)
- [完整模型和相机前置条件](../boards/radxa-rock5b/CAMERA_YOLOV8.md)

## 环境与输入

需要真实 ROCK 5B、ARM64 Lite2、NumPy、OpenCV、可用的 USB 摄像头和 Model Zoo 优化版 640×640 RGB uint8 RKNN。代码限定对应的六或九个输出头（COCO 80 类），普通 YOLOv8 单一 ONNX 输出不能直接使用。

## 实验命令

~~~bash
python3 boards/radxa-rock5b/tools/usb_camera_check.py --help
python3 boards/radxa-rock5b/apps/camera_yolov8_lite.py --model /path/to/optimized-yolov8n.rknn --source /dev/video0 --size 640 --frames 30 --warmup 0 --labels boards/radxa-rock5b/assets/coco80.txt --jsonl /tmp/yolov8-frames.jsonl --confirm-optimized-yolov8
~~~

数据流：OpenCV BGR 取帧 → RGB 与 letterbox（记录 ratio 和 pad）→ RKNNLite.inference → 三个检测尺度 DFL 解码 → 分类阈值和 NMS → 原图 xyxy。单张图先与官方例程对照，再做摄像头实验。程序不默认保存视频，JSONL 按帧记录框和时延。

## 自动化测试

- [摄像头/后处理离线测试](../boards/radxa-rock5b/tests/test_camera_yolov8.py)

## 验收标准

至少连续处理 30 帧，保留实际 JSONL；验证坐标落在相机尺寸内、类别在 0–79 之间。若场景没有可检出物体，可以确认帧采集和 NPU 执行正常，但不能编造检出框。FPS 是整个同步循环的速度，不是独立 NPU 算子性能。

## 验证边界

离线 Python 张量、模拟摄像头和假 SDK 只能测试后处理与程序路径。需要真实 ROCK 5B 日志才可勾选上板通过。

