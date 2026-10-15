# ROCK 5B 的后续实际开发路线与验收门槛

我们不以“脚本存在”为完成依据。每个阶段都有**真实设备、明确模型、最小输入、可保存输出、失败原因**。

| 阶段 | 目标 | 准备开发的程序 | 真实验收 |
|---|---|---|---|
| P0（已提供代码） | ROCK 5B 硬件/系统/NPU 初检 | `tools/board_probe.py` | 设备树、内核、RAM、NPU 线索 JSON |
| P1（已提供代码） | USB 摄像头与 V4L2 验收 | `tools/usb_camera_check.py` | 真实帧尺寸/时间统计，非 NPU FPS |
| P2（已提供代码） | Radxa 官方 YOLOv8 对照基线 | `tools/run_official_yolov8.py` | 官方样本真正检出、保存图片 |
| P3（源码已写，待实机测试） | 本仓库独立 MobileNet 图像分类 | `apps/mobilenet_image_lite.py` 等 | 同一张图与官方 C API 示例分类一致 |
| P4（下一阶段） | USB 摄像头→NPU 实时 YOLOv8 | 配套模型检测头专用解码、letterbox/NMS、异常恢复 | 实时帧率、p50/p95、mAP 和掉帧情况 |
| P5（下一阶段） | C++ RKNPU2 + RGA + 零拷贝 | 交叉编译、tensor stride、DMA/缓存同步 | 同图正确性与延迟/内存消融 |
| P6（研究项目） | RKLLM 小语言模型 | 工具链、量化适配、提示词与 KV cache 测试 | 板端 TTFT、tokens/s、RAM 和错误日志 |

P0～P2 的程序属于可以调用真实设备或官方代码的独立文件，**但仍需用户提供实物运行记录后才能声称已验证通过**。后续计划不是已经交付的成果。

## 如何获取足够的板端证据

在真实板卡运行 `board_probe.py` 保存 `results/rock5b-board.json`，拍摄 PCB 修订号时不要泄露不必要的唯一硬件标识。确认官方 YOLOv8 检测后，保存实际程序 stdout/stderr、输入图片来源、模型 SHA256、结果图和日期。只有拿到这些证据，再决定是否进入 USB 摄像头实时推理、内存优化或模型量化。

## 为什么优先使用官方 YOLOv8 而不是 YOLO26

Radxa [官方 YOLOv8 文档](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-toolkit-lite2-yolov8) 有从预转换模型到板端结果图的明确路径；YOLO26 的 ONNX 算子和后处理在 RK3588 当前工具链中的兼容性，需要另行对照。先获得 NPU 环境的已知有效基线，可以区分驱动问题与新模型问题。
