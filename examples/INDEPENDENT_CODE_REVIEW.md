# RK3588 课程源码结构与验证范围

> 本表区分独立源码、主机侧测试与开发板实测；不以代码行数或 `--help` 作为硬件验收证据。

**结论**：35 个编号 Python 程序均为不同源文件；不使用按课程编号转发的薄入口。另有 `examples/hardware/rknn_classify.cpp` 和 `rknn_zero_copy.cpp` 两份 C++ 推理代码。但部分 Python 程序是外部 SDK、模型转换脚本、CMake 或厂商 Demo 的专门启动器，不是每一讲都拥有自包含的完整 NPU 项目。

## 逐讲检查

| 编号 | 实际内容 | 实现模式 | 验收缺口 |
|---|---|---|---|
| 00 | 环境工具及模型哈希 | 独立本地工具 | 主机元数据真实采集 |
| 01 | CPU/内存/设备树 | 只读硬件查询 | 实物板型待验证 |
| 02 | 卷积MAC统计 | 独立数学计算 | 不是NPU速度 |
| 03 | RKNN流程DOT图 | 独立文件生成 | 不是模型部署 |
| 04 | 上游仓库git远端refs | 外部Git调用 | 依赖网络 |
| 05 | RKNN Toolkit2安装检测 | SDK环境探测 | 非模型转换 |
| 06 | NPU驱动和ELF探测 | 只读板端工具 | 待实板兼容性 |
| 07 | sysfs频率温度采样 | 测量工具 | 缺真实负载数据 |
| 08 | Model Zoo demo调用 | 外部程序启动器 | 真实模型/板卡必需 |
| 09 | ONNX校验再RKNN转换 | 硬件转换脚本编排 | 需Toolkit2实测 |
| 10 | 图片RGB归一化 | 真实图片数值处理 | 需与模型训练一致 |
| 11 | 批量ONNX转RKNN | 转换作业编排 | 需真实SDK与校准集 |
| 12 | ONNX图解析 | 真实ONNX解析 | 非RKNPU算子兼容证据 |
| 13 | Toolkit2模型推理 | 直接SDK调用 | 模拟器非板端测速 |
| 14 | 浮点量化NPZ误差 | 真实张量比较 | 待分类/mAP任务精度 |
| 15 | 外部命令时延统计 | 启动器+计时 | 非孤立NPU延迟 |
| 16 | Linux进程内存统计 | 只读proc监测 | 待RK3588长稳测试 |
| 17 | 通道结构剪枝 | 实际numpy权重修改 | 无微调/板端加速 |
| 18 | Fernet文件加解密 | 实文件加密 | 非RKNN官方模型加密 |
| 19 | 多张图片Batch数组 | 真实图像堆叠 | RKNN batch支持待校验 |
| 20 | 多输入ONNX执行 | ONNX Runtime | RKNN多输入待校验 |
| 21 | 动态shape ONNX执行 | ONNX Runtime | RKNN动态shape待校验 |
| 22 | 删除ONNX Identity节点 | 实际ONNX图编辑 | 大型网络回归仍不足 |
| 23 | 自动生成张量描述hpp | C++接口生成 | 不是完整RKNPU推理生成 |
| 24 | RKNNLite模型推理 | 直接Lite2 SDK | 板端输入输出待验收 |
| 25 | CMake/C++分类器 | Python调用独立C++ | RK3588链接和输出待验收 |
| 26 | 零拷贝内存绑定 | Python预检+独立C++ | 需对照API、stride、缓存和性能 |
| 27 | MobileNet分类 | 独立ONNX/RKNNLite双路径 | ONNX CI通过，NPU待实机 |
| 28 | MobileNet图片分类封装 | 独立ONNX类 | 缺独立C++ RKNN封装 |
| 29 | YOLOv5检测 | Ultralytics或外部RKNN demo | 缺独立摄像头RKNN后处理 |
| 30 | YOLO26 PC检测 | Ultralytics真实checkpoint | 未证明NPU兼容 |
| 31 | YOLO数据验证/训练 | 真实数据审计、可执行训练 | 需训练权重与准确率报告 |
| 32 | YOLO导出ONNX/RKNN | Ultralytics+转换器 | 缺板端YOLO26检测验收 |
| 33 | YOLOv8模型性能对比 | PC端Ultralytics | 非RK3588 NPU优化测速 |
| 34 | RKLLM模型执行 | 外部官方二进制启动器 | 未有板端token/内存指标 |

## 当前测试证据

- `.github/workflows/examples-ci.yml`：35 个 CLI 的调用检查、语法检查、教材映射与部分课次真实文件/ONNX 功能测试。
- `examples/tests/test_lessons_09_34.py`：数值、ONNX、图像及错误输入等测试，CI 通过。
- C++ 使用公开 `rknn_api.h` 做**语法检查**，不是 RK3588 实机编译和链接，更不是运行正确性。
- Python `lesson_27.py` 已在 CI 对真实 ONNX Tiny CNN/图片推理；板端 `.rknn` 需真实机器和匹配 SDK。

## 实机实验的验收事项

1. **统一目标硬件**：ROCK 5B 板级 revision、官方系统镜像、内核驱动、Toolkit2/Lite2/Runtime 版本和模型 SHA256 均固定并记录。
2. **完善 C++ 推理验收**：对第25/26讲在板端完成构建和输入输出回归；zero-copy 示例仍先 memcpy 到 SDK 分配内存，不是 USB 摄像头至 NPU 的端到端零拷贝；还要测试 stride、cache 同步和真实性能差异。
3. **相机实时检测验收**：对现有 USB UVC/V4L2 → RGB/letterbox → RKNN YOLOv8 → DFL/NMS → 逐帧输出的工程，在真实 ROCK 5B 上检查帧率、坐标、稳定性和 p50/p95。
4. **课程第 28/32 讲专项验收**：第 28 讲的源码 lesson_28.py 是 ONNX Python 封装，配套有单独 C++ RKNPU2 示例；第 32 讲的源码 lesson_34.py 是外部 RKLLM Demo 启动器，另有原生 C++ RKLLM 回调实现，仍需实机生成与性能日志。
5. **构建真正的模型和数据基线**：真实模型、样例图片、许可来源、前处理 mean/std、量化数据集、标注数据集及训练配置锁定；不要用占位权重或仅凭 ONNX checker 宣称 RKNN 已支持。
6. **实验记录**：保留输入模型、程序命令、板端 Runtime/驱动、实际输出、性能采样及未通过原因；PC CI 不代替这些证据。

## 三种不可混淆的状态

- `独立源码已写`：程序自身实现了某项操作，不是旧的课号分发函数。
- `主机CI已通过`：特定依赖/示例文件在 GitHub x86 runner 上运行，有自动断言。
- `RK3588实机已验收`：需要真实开发板、固件/驱动、输入输出与原始测量记录。目前不能把前两种当作这一种。

可运行 `python3 examples/audit_course.py --strict` 重新确认35个编号脚本和课程说明完整性。
