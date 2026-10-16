# ROCK 5B USB 摄像头 → RKNN YOLOv8 实时目标检测

**工程目标**：原版 Radxa ROCK 5B / RK3588，在 Linux UVC 视频节点上连续采集图像，逐帧送入 Rockchip RKNN-Toolkit-Lite2 的真实 NPU Runtime，独立解析模型的 DFL 边框、执行按类别 NMS，必要时画框，保存可复核的检测记录和性能统计。本仓库实现了自己的解码和主循环，并非仅启动 Model Zoo 示例。

> **模型边界必须读清楚**：只支持 [Rockchip Model Zoo 优化版 YOLOv8](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/yolov8) 的 **640×640、RGB uint8 HWC、3 个检测尺度、每个尺度 [box64,class80,aux1] 的 9 个浮点输出**（或经确认输出箱和类别各 1 个的 6 输出版本）。普通 Ultralytics ONNX [1,84,8400]、其他 YOLOv8/YOLO26 架构、分割、姿态估计及原始未反量化整数输出均**不受支持**，会直接报错。不能仅看文件后缀 `.rknn` 判断兼容。

## 1. 代码和官方参考

- [真正的 USB 摄像头 RKNNLite 主程序](apps/camera_yolov8_lite.py)：启动模型、读帧、推理、写 JSON/JSONL、可选绘制和视频录制。
- [纯 NumPy 检测头解码与 NMS](apps/yolov8_rknn_postprocess.py)：DFL softmax/积分、三尺度坐标还原、黑色 letterbox、按类别 NMS。
- [80 类 COCO 标签映射](assets/coco80.txt)：为 Model Zoo 的 COCO 80 类训练版本准备。自己训练的类别必须修改成正确的类别集合，但本基准程序暂时固定 80 类以防止静默出错。
- [Rockchip Model Zoo YOLOv8 README](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8/README.md)：明确说明 9 输出的优化结构、来源及转换方法。
- [官方 Python 基准实现](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/yolov8/python/yolov8.py)：用于同图对照，特意使用 **黑色填充**而非常见 114 灰色。
- [Radxa ROCK 5B RKNN 安装手册](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install)。

不在仓库中捆绑第三方 `.rknn` 权重、软件镜像或未经授权的数据；使用前记录 Model Zoo commit、ToolKit2、Lite2、Kernel/Driver、模型 SHA256。

## 2. 准备实物、镜像和模型

在 ROCK 5B 上先完成 [首次启动](FIRST_BOOT.md) 与 [USB 摄像头验收](CAMERA_MOBILENET.md) 中的环境/读帧检查。确保安装板端支持的 Python NumPy、OpenCV、RKNN-Toolkit-Lite2 wheel 和运行库，摄像头可读取 `/dev/video0`（或实际对应节点）。不要使用 PC 的 x86 Toolkit2 wheel 代替 ARM64 Lite2。

然后使用官方 Model Zoo 提供的优化版 `yolov8n.onnx` 与配套 `convert.py` 在支持的 Linux x86_64 环境转换，或使用 Radxa 已提供的对应预转换 `.rknn`。官方转换脚本使用 `mean_values=[[0,0,0]]`、`std_values=[[255,255,255]]`，**所以本工程直接传 RGB uint8，绝不再次除以 255**。确保校准数据与对应版本一致。

模型输出应是 9 个张量：

    [1,64,80,80], [1,80,80,80], [1,1,80,80],
    [1,64,40,40], [1,80,40,40], [1,1,40,40],
    [1,64,20,20], [1,80,20,20], [1,1,20,20]

其中 64 是四组 16-bin DFL logits，80 是 COCO 分类分数，最后 1 通道是官方优化后的辅助分支。这些是 **模型协议示例形状**，不是任何 `.rknn` 都会有的输出。

## 3. ROCK 5B 命令（仓库根目录）

先检查命令行接口：

    python3 boards/radxa-rock5b/apps/camera_yolov8_lite.py --help

实际执行 100 帧，默认**不保存原始视频或图片**：

    python3 boards/radxa-rock5b/apps/camera_yolov8_lite.py \
      --model /path/to/official/optimized/yolov8.rknn \
      --source /dev/video0 --capture-width 640 --capture-height 480 \
      --size 640 --frames 100 --warmup 10 \
      --conf 0.25 --iou 0.45 --confirm-optimized-yolov8 \
      --summary boards/radxa-rock5b/results/yolov8_summary.json \
      --jsonl boards/radxa-rock5b/results/yolov8_frames.jsonl

要**明确选择保存画框结果**，可增加：

    --output-image boards/radxa-rock5b/results/yolov8_last.jpg

有本地图形桌面时，还可使用 `--view` 并按 q 退出；若需要视频，使用 `--output-video boards/radxa-rock5b/results/yolov8_record.avi`（MJPG 编码，必须注意可能包含人脸与现场隐私）。两项均为显式选择，不默认录制。

## 4. 输出数据和 FPS 含义

摘要 JSON 包含真实模型 SHA256、总处理帧数、检测数量、最后一帧检测框 `xyxy`（**映射回原始相机帧坐标**）、各阶段平均/p50/p95/max 时延、同步循环 FPS。

每帧 JSONL 记录该帧全部检出物体的 COCO 类别、分数、边框及 capture/preprocess/inference/postprocess/render/end-to-end 毫秒时延。该 `synchronous_fps` 包含摄像头取帧、CPU 缩放/letterbox、Lite2 推理、CPU DFL/NMS 以及绘制（如有），**不是 NPU 算子单独 FPS**，也不是显示器刷新率。

其中 `inference_ms` 是 `RKNNLite.inference()` Python API 墙钟时间；实际 NPU Core 利用率、温度/能耗、模型 mAP 应独立测量，不可把这里的帧率直接写成模型准确率。

## 5. 功能验收和排障

1. 用同一个 `.rknn` 和同一张 `bus.jpg`，先运行 Model Zoo 官方 YOLOv8 静态图片例程；与本程序保存的检测框进行**同图同预处理**对照，确认类别、IoU、分数足够接近。
2. 若提示“Expected 6 or 9”，多半拿错了模型版本；不要强制 reshape 原生 YOLOv8 输出。
3. 若提示 DFL/Class 形状不一致，检查 Model Zoo commit、模型输出顺序、是否启用对应的优化版导出。
4. 若类别错误，核对对应的 80 类标签与输入 BGR/RGB、均值标准差。**预训练权重的输出标签不能依靠人为偏移硬改**。
5. 若摄像头节点不存在、权限不足或取帧失败，请先使用 `usb_camera_check.py`；主程序在异常时释放 Runtime 与摄像头。
6. 若运行速度偏低，比较真实的 `preprocess_ms`、`inference_ms`、`postprocess_ms`；当前实现使用 CPU OpenCV 和 NumPy，不是 RGA/DMA 零拷贝，也未进行多线程流水线。

**测试状态**：当前 CI 会检查 NumPy DFL 数值、letterbox、6/9 输出结构、非官方格式拒绝、NMS 和使用明确标注的假摄像头/假 SDK 对象测试资源释放/报告。它**没有实机 ROCK 5B，也不能证明 RKNN/USB 摄像头已经通过实测**。

下一阶段可根据实物测量结果添加 C++ RGA、零拷贝与多线程图像流水线优化，而不是先推测 FPS。

