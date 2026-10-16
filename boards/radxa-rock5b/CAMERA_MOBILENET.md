# USB UVC 摄像头 → RKNNLite MobileNet 实时分类

**开发板目标：Radxa ROCK 5B 原版，RK3588，Radxa OS 或匹配 Runtime/Driver 的发行版。** 本示例不是 YOLO 目标检测，而是完整的摄像头图像分类管线：每帧输出类别索引与预测分数，计算采集、预处理、RKNNLite API 和整体单帧耗时，并保存 JSON/JSONL 供验收。

## 环境与正确的模型

1. 按 [首次上电及模型验收](FIRST_BOOT.md) 确认系统、摄像头和 RKNPU 驱动。
2. 根据 [MobileNet 官方案例](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/mobilenet) 从官方配套 Model Zoo/Toolkit2 准备能在 RK3588 运行的 `.rknn` 模型；按发布版要求安装 ARM64 RKNNLite、Runtime 和 Python 依赖。
3. 仔细核对输入属性：本程序只支持 **RGB、uint8、HWC/NHWC batch1、单输入单输出的分类模型**，模型的 mean/std 预处理约定需在转换时确认。默认目标输入为 224×224，但并非每个 `.rknn` 都符合这些假设。
4. 安装或确认 Python 的 `numpy`、`Pillow`、`cv2` 和 `rknnlite` 均可导入；对于 OpenCV 优先使用板商兼容的系统包。
5. 摄像头通过 USB UVC/V4L2 连接；通过 `v4l2-ctl --list-devices` 和实际读取确认对应 `/dev/videoX`，部分视频节点可能是 ISP/Codec 而非 UVC 摄像头。

## 实机运行（从仓库根目录）

    python3 boards/radxa-rock5b/apps/camera_mobilenet_lite.py \
      --model /path/to/compatible_mobilenet.rknn \
      --source /dev/video0 --capture-width 640 --capture-height 480 \
      --width 224 --height 224 --resize center-crop \
      --frames 120 --warmup 10 --topk 3 \
      --confirm-rgb-uint8-nhwc \
      --json boards/radxa-rock5b/results/camera_mobilenet.json \
      --jsonl boards/radxa-rock5b/results/camera_mobilenet_frames.jsonl

`--confirm-rgb-uint8-nhwc` 是**显式确认你已核对真实模型输入协议**，而不是通用自动转换开关。需要其他输入布局、float32 归一化、两个输入、输出检测框的模型应使用相应程序，不能直接复用本例。

## 真实输出与判定

- `summary.json`：模型文件的 SHA256、实际帧数、模型输入规格、最后一帧 Top-K、摄像头到 NPU 单线程同步处理的吞吐 FPS，以及 capture/preprocess/inference/end-to-end 的 mean、p50、p95、max 毫秒值。
- `frames.jsonl`：每帧的 Top-K、分数和分阶段耗时。默认**不保存、上传或展示原始图像**，避免不必要的隐私数据。
- 模型分类的 `model_score` 不自动转换为概率。标签行数必须严格等于类别数，否则停止，避免错误映射。
- `throughput_fps` 测量单线程**读取摄像头 → CPU Pillow 缩放 → NPU RKNNLite 同步推理**的循环，而不是显示 FPS、相机驱动真实曝光频率或纯 NPU 算子耗时；`inference_ms` 是 RKNNLite Python API 调用墙钟时间，不等于 NPU-only profile。

### 错误处理

- 摄像头不能打开/某帧采集失败：退出并提示排查设备节点和权限，始终释放 V4L2 资源。
- 加载模型/初始化 Runtime 失败：打印明确阶段与 SDK 返回码，释放 RKNNLite 资源。优先对照驱动/Runtime/模型 SDK 版本，而不是立即更新固件。
- 模型输入 shape/dtype 不匹配：先使用官方示例对相同模型跑通。任意更改 mean/std、resize/crop 可能使预测完全不同。
- 用户 Ctrl+C 中断运行：程序负责在 finally 释放摄像头与 Runtime，但未完成的报表可能不存在；不要将中断前的非完整数据视为正式性能结果。


## 保存后的自动验收

先按上文执行真实板端程序并生成 JSON/JSONL，然后在仓库根目录运行：

    python3 boards/radxa-rock5b/tools/validate_camera_report.py \
      --summary boards/radxa-rock5b/results/camera_mobilenet.json \
      --jsonl boards/radxa-rock5b/results/camera_mobilenet_frames.jsonl \
      --model /path/to/compatible_mobilenet.rknn

它检查帧数、Top-K、p50/p95 统计结构与模型 SHA256 对应关系。可选 `--min-fps`、`--max-inference-p95-ms` 参数按**自己的应用验收门槛**进行自动判定。此工具对保存的文件做结构/阈值校验，**不能独立证明数据来自真实 NPU**；必须另外保留板端日志、SDK/驱动版本等证据。

## 验收状态

GitHub CI 使用**明确标记的模拟摄像头和 SDK 对象**，验证图像通道处理、224×224 参数化缩放、Top-K、资源释放、性能报告的 JSON 格式和各种失败路径；它不模拟真实的 NPU 精度或速度。**真实 RK3588 USB 摄像头与 RKNNLite 联调仍待使用实体 ROCK 5B 验收。**

后续再开发 YOLOv8 的专用后处理和目标检测框，而不把本项目误称为物体检测系统。
