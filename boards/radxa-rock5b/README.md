# ROCK 5B 16GB：课程统一硬件基准（从上电到 NPU 目标检测）

这是根据 **Radxa 公开的 ROCK 5B 手册及 RKNN/YOLOv8 部署指导** 编写的板级操作课程。目标是让《RK3588 嵌入式 AI 教程》里的环境、命令、设备、故障排查和实验验证对应**一款确切的开发板**。

> **型号边界：ROCK 5B（原版，RK3588）16GB LPDDR4X**，不是 ROCK 5B+、5A、5C、Orange Pi 5，也不是 RK3588S 板卡。RAM 容量是我们选择的实验配置；官方 ROCK 5B 还提供其他容量。型号、PCB 修订号和实际系统镜像必须从你的板卡核对。当前仓库程序尚未在用户的实物上执行，所有设备状态均为“待上板验收”。

## 一、为什么选择这一块板

- 有完整 RK3588 NPU 与较充裕的 16GB 内存，适合后续 MobileNet/YOLO、视频流和小型 RKLLM 实验。
- Radxa **中文官方手册**可找到 ROCK 5B 的供电、microSD 装机、接口、原理图与不同 PCB 版本对应的设计文件。
- 官方 **AI 开发**文档明确介绍 Toolkit2/Lite2/Runtime/驱动层次，提供 MobileNet、YOLOv5、YOLOv8 及 RKLLM 专题。
- 官方板端 YOLOv8 文档给出预转换模型和 `rknn-model-zoo-rk3588` 软件包的示例，适合作为首个“已知可对照”的 NPU 验证路径。

## 二、设备采购/准备清单

| 设备 | 建议 | 说明 |
|---|---|---|
| 开发板 | Radxa ROCK 5B **16GB** | 购买前再次确认是 5B，不是 5B+；容量可按预算调整 |
| 电源 | **官方推荐的 Radxa PD 30W** 与匹配 USB-C 线 | ROCK 5B 的推荐电源；不要混用 5B+ 所需供电指标 |
| 存储 | microSD 卡（建议 32GB 起，建议 64GB）与读卡器 | 推荐先用 SD 启动，避免首轮改写 eMMC/SPI/NVMe |
| 散热 | 与 ROCK 5B 匹配的散热器，按需要加风扇 | 持续 NPU 测试需要记录温度 |
| 网络 | 网线与可访问的路由器 | 原版 ROCK 5B **没有板载 Wi-Fi**；优先有线网络 |
| 调试 | HDMI 显示器、线、USB 键鼠（首轮） | 先可视化确认启动和网络再配置 SSH |
| 可选摄像头 | 普通 **USB UVC 摄像头** | 不指定未经验证的摄像头型号；先检查 `/dev/video*` |
| 可选串口 | 确定接口电平兼容的 **3.3V USB-UART** | 必须对照当前 PCB 修订号官方引脚图；**禁止将 5V TTL 直接接入信号引脚** |

不推荐首轮购买 MIPI CSI 摄像头或 NVMe 作为必须项目；它们涉及额外的排线、设备树、SPI 启动或专用驱动，容易分散对 NPU 推理本身的学习。

## 三、学习与开发顺序

1. [检查官方资料和型号差异](MANUAL_MAP.md)
2. [首次上电、系统镜像与无侵入检查](FIRST_BOOT.md)
3. 在板上执行：`python3 boards/radxa-rock5b/tools/board_probe.py --strict --output boards/radxa-rock5b/results/rock5b-board.json`
4. 可选摄像头：`python3 boards/radxa-rock5b/tools/usb_camera_check.py --source /dev/video0 --frames 30 --save-json boards/radxa-rock5b/results/camera.json`
5. 在 **Radxa OS** 中按厂商文档安装 `rknn-model-zoo-rk3588`，运行预训练 YOLOv8 实例；可用 [厂商实例启动器](tools/run_official_yolov8.py) 检查路径并启动。
6. [第二阶段硬件专项开发与验收](NEXT_PROJECTS.md)：MobileNet 图像分类、USB 摄像头取帧、NPU 推理、性能测试、YOLO 自定义模型、RGA、C++ 与 RKLLM。

### 运行前的基本原则

- `board_probe.py` 只读取 Linux 系统信息，**不会**刷机、更新 NPU 驱动、改频或写 GPIO。
- 摄像头检查只读取帧，可指定保存一张测试图片；图像可能涉及隐私，不要自动上传到公共仓库。
- `run_official_yolov8.py` **不会自动 sudo、apt install、下载模型或刷写固件**。没有官方文件将明确报错，文件齐全才启动原版实例。
- 真正的 RKNN 模型输出和 FPS，必须由实物板端运行记录来确认。板端路径不兼容时优先查官方发布说明。

## MobileNet：真正的图片到 RKNNLite 分类源码

厂商的 [MobileNet 示例](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/mobilenet) 提供了模型转换和 C API 工程；此处补充一个本仓库自己实现的 [Python RKNNLite 图片分类程序](apps/mobilenet_image_lite.py)。

先用官方 Model Zoo 的 `mobilenetv2-12.onnx` 与配套转换脚本生成适用于 `rk3588` 的 `mobilenet_v2.rknn`，并下载对应 `bell.jpg` 等样例文件。务必理解并核对该模型期望的 **224×224、RGB、UINT8、NHWC** 输入协议，以及是否已在 RKNN 编译阶段包含 mean/std。示例运行：

    python3 boards/radxa-rock5b/apps/mobilenet_image_lite.py \
      --model /path/to/mobilenet_v2.rknn --image /path/to/bell.jpg \
      --confirm-rgb-uint8-nhwc --resize center-crop \
      --runs 10 --warmup 3 --json boards/radxa-rock5b/results/mobilenet.json

实际 resize/crop 规则应与用于对照的官方 C 示例统一。这个 Python 应用会进行真实的 RKNNLite 推理并打印 Top-K 类索引与分数；如果提供 `--labels`，只有标签行数与模型输出类别数一致才映射类名，避免把偏移错误强行打印为正确类别。分类分数未经 softmax，不应直接称为概率。

**测试状态**：Python 代码可以在 CI 用伪运行时测试控制流程和预处理，但模型输出和速度仍需在 ROCK 5B 实机核对；不同 SDK release 的 RKNN 模型输入契约可能变化。

## USB 摄像头 → NPU 的真正闭环（新增）

在静态图片分类和单独摄像头读帧检查通过后，使用 [完整摄像头 MobileNet 实验](CAMERA_MOBILENET.md) 和 [实际 RKNNLite 源码](apps/camera_mobilenet_lite.py) 将两者组合：BGR→RGB、缩放/裁切、RKNNLite 推理、Top-K、单帧耗时与 p95 统计、输出 JSON/JSONL，并使用 [报告校验工具](tools/validate_camera_report.py) 自动检查模型哈希和性能门槛。默认不保存原始摄像头图片。

**测试边界**：CI 用明确标注的 FakeCapture/FakeSDK 测功能和释放逻辑；真正 USB 摄像头/NPU 速度尚未上板实测，不应把这个分类应用误称为 YOLO 目标检测。

## YOLOv8 摄像头实时目标检测工程（新增）

在 MobileNet 分类流水线之后，新增 [完整 ROCK 5B USB 摄像头 YOLOv8 检测教程](CAMERA_YOLOV8.md)、[RKNNLite 检测主程序](apps/camera_yolov8_lite.py) 和 [独立 DFL/NMS 后处理](apps/yolov8_rknn_postprocess.py)。要求 Model Zoo **优化版** 640×640 / 9 或 6 输出模型，支持画框、逐帧 JSONL 与 FPS/p95。**这是目标检测，与 MobileNet 图像分类不同；真实 RK3588 推理尚待硬件验收**。

## 四、公开来源（请与自己的板卡版本核对）

- [ROCK 5B/5B+ 官方中文手册](https://docs.radxa.com/rock5/rock5b)
- [规格参数](https://docs.radxa.com/en/rock5/rock5b/getting-started/introduction)
- [电源选择](https://docs.radxa.com/rock5/rock5b/getting-started/power-supply)
- [microSD 启动](https://docs.radxa.com/rock5/rock5b/getting-started/install-os/boot_from_sd_card)
- [镜像、原理图和硬件 PCB 修订资料](https://docs.radxa.com/rock5/rock5b/download)
- [RKNN SDK 安装、兼容性与驱动](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install)
- [RK3588 上运行官方 YOLOv8 模型](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-toolkit-lite2-yolov8)
- [MobileNet 从转换到 C API 的完整案例](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/mobilenet)

手册会更新，建议购买后保存 PCB 修订号、所选镜像的 SHA256、Toolkit2/Lite2 release、模型来源和板端真实日志。
