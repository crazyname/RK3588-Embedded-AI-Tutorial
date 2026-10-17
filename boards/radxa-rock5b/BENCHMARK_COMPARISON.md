# ROCK 5B C++ YOLOv8：可复现性能比较

> 适用范围：`v4l2_rga_rknn_yolov8` 的逐帧 JSONL 输出；比较的是程序记录的推理+解码耗时，**不是纯 NPU 算子延迟**。本工具不能鉴定日志是否真实来自开发板。

## 1. 先获取两组完整日志

使用 [V4L2 / RGA / RKNN 实验](V4L2_RGA_RKNN_YOLOV8.md)中的命令，分别运行基线 A 和候选 B。固定相同的模型、摄像头格式与分辨率、摄像头标称 FPS、板卡/系统/驱动、RGA 与 RKNN Runtime、实验帧数及预热策略；确保外界负载、温度和供电条件尽量接近。

保留原始 `a.jsonl`、`b.jsonl` 与各自的 `stderr`，不要人工修改 JSONL。最好分别记录开始/结束温度与频率，多轮交替测量，避免单次运行的系统噪声。

## 2. 为每组日志保存来源清单

下面是供填写的**字段示意，不是真实硬件采集结果**：

```json
{
  "board": "ROCK 5B rev <实际版本> 16GB",
  "os_image": "<镜像版本与SHA256>",
  "kernel": "<uname -r>",
  "npu_driver": "<驱动实际版本>",
  "rknn_runtime": "<实际版本>",
  "rga_version": "<实际版本>",
  "model_sha256": "<64位十六进制模型SHA256>",
  "model_contract": "model-zoo optimized YOLOv8 640x640 RGB uint8 COCO80",
  "camera_format": "YUYV",
  "camera_width": 640,
  "camera_height": 480,
  "camera_fps": 30,
  "pipeline": "v4l2-rga-rknn-cpp",
  "measurement_protocol": "60 measured frames; same warmup and power policy",
  "evidence_type": "board-captured",
  "log_sha256": "<64位十六进制JSONL SHA256>"
}
```

将占位内容替换成**真实记录**；不要提交这个示意 JSON 直接运行。只有明确是合成测试数据时才写 `"evidence_type": "synthetic"`。这个字段是操作者声明，不能作为第三方硬件真实性证明。

Linux：

```bash
sha256sum /actual/models/optimized_yolov8.rknn
sha256sum a.jsonl b.jsonl
uname -r
```

将第一条摘要分别填入两个清单的 `model_sha256`，将每个日志摘要分别填入各自清单的 `log_sha256`。实际驱动、Runtime、RGA 版本须从系统/SDK 自身读取，不可由本说明推断。生成 `a.manifest.json` 和 `b.manifest.json`。

## 3. 单次校验，再做双次比较

```bash
python3 boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py \
  --jsonl a.jsonl --width 640 --height 480
python3 boards/radxa-rock5b/tools/validate_cpp_yolo_stream.py \
  --jsonl b.jsonl --width 640 --height 480

python3 boards/radxa-rock5b/tools/compare_cpp_yolo_runs.py \
  --baseline-jsonl a.jsonl --baseline-manifest a.manifest.json \
  --candidate-jsonl b.jsonl --candidate-manifest b.manifest.json \
  --output comparison.json
```

默认拒绝任何比较配置差异（包括模型哈希、驱动、采集格式、测量协议）。`--allow-mismatch` 只用于调查不一致的原因：输出的 `comparison_valid=false`，进程退出码为 **3**，不应把差值称为有效的单变量性能收益。无效日志或清单退出码为 **2**。

输出包含两次运行的帧数、各阶段平均/p50/p95/max，以及 `inference_and_decode_ms` 的 p95 绝对变化和百分比变化；**负值表示候选运行记录的 p95 更低**。JSONL 不提供总循环墙钟耗时，不能用各阶段相加声称真实吞吐 FPS；程序本身在 stderr 中报告的 FPS 应单独记录。

## 4. 正确解释结论

- 两次配置相同且日志格式合法，只能得出 **所提交日志之间可以数值比较**；`hardware_verified=false` 始终保留。
- 保留 Model Zoo commit、模型来源与许可证、实际固件/驱动版本、温度、电源策略、摄像头测试场景和原始日志，才能人工审核实机复现性。
- NPU 算子独立延迟需要 SDK profiling；`inference_and_decode_ms` 还包含输入设置、输出提取和 CPU 后处理。
- 对检测准确率应另用人工标注的测试集计算 mAP；检测数或 p95 改善并不能证明精度没有下降。
- `boards/radxa-rock5b/results/` 不纳入仓库；视频目标框也可能涉及个人隐私。公开报告前先审查内容。

## 5. 无硬件时检查工具

```bash
python3 -m unittest discover -s boards/radxa-rock5b/tests -p 'test_compare_cpp_yolo_runs.py' -v
```

测试使用合成 JSONL，不接触摄像头/RGA/NPU。
