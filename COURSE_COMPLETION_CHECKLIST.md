# 课程完工清单（教学版）

> 本清单追踪教学闭环，不用文件存在或 CI 通过代替实际运行验收。更新记录时附运行命令和日志链接；未取得证据的项目保持未完成。

## 范围和编号

仓库当前是 **35 份 MD + 35 份 HTML**，文件编号为 **00–32**，其中 **第 30 讲分成三份**。对应源码采用 `examples/lesson_00.py` 到 `lesson_34.py` 的 35 个程序编号；**课程文件编号与程序编号从第 30 讲起并非一一相等**。课程第 31 讲是 YOLOv8，第 32 讲是大模型/RKLLM；不可把源码 34 误写成“第 34 讲”。

范围收束：优先完成 35 份讲义、35 个长页课件、已有课程源码和六条核心实验链路。保留已存在的辅助测试，但不新增生产级故障注入、溯源证明或全套性能回归作为完课门槛。

## P0：课程与源码对齐

- [ ] 核实每份课程 MD 的对应操作说明、可执行命令、实际源文件入口及预期输出。
- [ ] 核实每份 HTML 是连续滚动长页，能定位真实代码/实验，不只是概念摘要。
- [ ] 优先逐份复核 24–32（含三份 30）HTML：实验完整命令、关键 API、张量形状和结果解释。
- [ ] 区分 30 讲 YOLO26（兼容性/导出扩展）与 31 讲 YOLOv8（主要板端实战）。
- [ ] 逐个核对 `engineering/manifest.json` 中 `lesson_ids` 与 `lesson_pages` 的真实对应，不用数量通过表示语义正确。

## P0：六条端到端学习链路

| 链路 | 当前入口 | 最终验收证据 |
| --- | --- | --- |
| ONNX → RKNN | [ONNX 工具链](engineering/onnx-toolchain.md) | 真实 ONNX、转换命令、成功导出的 RKNN 路径和工具版本 |
| RKNN → Python | [MobileNet 静态分类](engineering/mobilenet-image.md) | 图像、预处理参数、Top-K/标签输出及板端版本 |
| RKNN → C++ | [C++ 分类](engineering/cpp-rknn-classify.md) | CMake/编译命令、同一模型的输入输出及终端记录 |
| 摄像头 → YOLOv8 | [YOLOv8 摄像头](engineering/yolov8-camera.md) | 一帧输入、letterbox/DFL/NMS 后检测结果及设备信息 |
| 摄像头 → RGA → RKNN | [V4L2/RGA/RKNN](engineering/v4l2-rga-rknn.md) | RGA 图像正确性对照、输出框和缓冲生命周期说明 |
| RKLLM → 生成文本 | [RKLLM 原生工程](engineering/rkllm-native.md) | 模型来源与兼容性、构建运行命令、回调输出、生成文本 |

以上入口已有不等于全部在真实 ROCK 5B 验收通过。完整 DMA-BUF 共享零拷贝不作为 P0：第 26 讲先区分普通拷贝、SDK 内存绑定与 DMA-BUF。

## P1：讲解质量与收尾

- [ ] 逐讲明确前置知识和下一步、参数含义、关键函数及输入/输出 shape。
- [ ] 重点增加量化精度对照、letterbox 坐标回映、DFL/NMS、RKLLM 回调图解。
- [ ] MD 负责原理，工程实验 MD 负责操作，源码注释负责实现；删除不必要的重复文字。
- [ ] 运行最小 PC 单测、工程映射检查及仓库链接检查；核对失败项。
- [ ] README 给出从环境准备到模型转换、分类、检测、大模型的最短学习路线。

## P2：选做，不阻挡课程完工

- [ ] 完整 DMA-BUF 端到端共享链路。
- [ ] 超出基础教学要求的性能回归、故障注入与溯源审计。

## 必须采用的验收状态

记录时区分 **文件具备** / **PC 实测通过** / **ROCK 5B 实测通过** / **待验证**。只有实际执行并保留版本、输入、命令和关键输出，才可写“实测通过”。模拟输出应显式标记，不得充当 RK3588 性能与推理证据。

建议先执行：

```bash
python3 -m unittest discover -s examples/tests -v
python3 tools/audit_engineering.py --strict
python3 tools/validate_repo.py
```

这些只用于主机与文档级检查；设备、NPU、摄像头和 RKLLM 的实测必须在 ROCK 5B 上进行。
