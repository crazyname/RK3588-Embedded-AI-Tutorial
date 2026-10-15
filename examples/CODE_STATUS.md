# 35 节代码完成度与文档去重审计

更新：2026-10-16。此前 34 个包装入口已全部重写，现在 35 个编号入口均包含本讲实际业务逻辑。每个实例配一份操作 MD，**课程 MD 只讲理论与案例，实验 MD 只写安装、命令、真实输入输出和验证**。

## 状态含义

- **已独立实现**：不再只有 `from labs import main`，可查看对应脚本业务逻辑。
- **PC 可测**：可在 CI、Linux 或 Windows 运行真实算法、输入、模型处理或系统诊断。
- **依赖实机**：需要有目标硬件、Toolkit2/Lite2/RKNPU2/RKLLM、匹配模型和板级驱动。
- **不可冒充完成**：单纯运行参数帮助、模拟数据输出、ONNX Runtime 的成功，不等于 NPU、零拷贝或 RKLLM 真正上板验收。

| ID | 本讲实例源码 | 非重复实操 MD | 目前能验证的范围 |
|---|---|---|---|
| 00 | [lesson_00.py](lesson_00.py) | [操作手册](notes/lesson_00.md) | 本机环境 JSON |
| 01 | [lesson_01.py](lesson_01.py) | [操作手册](notes/lesson_01.md) | CPU/设备树只读报告 |
| 02 | [lesson_02.py](lesson_02.py) | [操作手册](notes/lesson_02.md) | 卷积 MAC 计算 |
| 03 | [lesson_03.py](lesson_03.py) | [操作手册](notes/lesson_03.md) | 部署依赖 DOT 图 |
| 04 | [lesson_04.py](lesson_04.py) | [操作手册](notes/lesson_04.md) | GitHub 远端 SHA |
| 05 | [lesson_05.py](lesson_05.py) | [操作手册](notes/lesson_05.md) | Toolkit2 ABI/安装诊断 |
| 06 | [lesson_06.py](lesson_06.py) | [操作手册](notes/lesson_06.md) | 驱动与 RT 只读状态 |
| 07 | [lesson_07.py](lesson_07.py) | [操作手册](notes/lesson_07.md) | 频率与温度采样（板级节点需有） |
| 08 | [lesson_08.py](lesson_08.py) | [操作手册](notes/lesson_08.md) | 真实模型 Demo 子进程执行（需板端） |
| 09 | [lesson_09.py](lesson_09.py) | [操作手册](notes/lesson_09.md) | 真实 Toolkit2 转换（需 SDK） |
| 10 | [lesson_10.py](lesson_10.py) | [操作手册](notes/lesson_10.md) | 真实图像归一化张量 |
| 11 | [lesson_11.py](lesson_11.py) | [操作手册](notes/lesson_11.md) | 实际多任务转换日志 |
| 12 | [lesson_12.py](lesson_12.py) | [操作手册](notes/lesson_12.md) | ONNX graph 算子统计 |
| 13 | [lesson_13.py](lesson_13.py) | [操作手册](notes/lesson_13.md) | Toolkit2 模拟/目标推理（需 SDK） |
| 14 | [lesson_14.py](lesson_14.py) | [操作手册](notes/lesson_14.md) | FP/INT8 真实数组误差 |
| 15 | [lesson_15.py](lesson_15.py) | [操作手册](notes/lesson_15.md) | 外部程序延迟分布 |
| 16 | [lesson_16.py](lesson_16.py) | [操作手册](notes/lesson_16.md) | Linux /proc 真实 PID 内存 |
| 17 | [lesson_17.py](lesson_17.py) | [操作手册](notes/lesson_17.md) | 真实权重结构剪枝；缺输入使用明示合成权重 |
| 18 | [lesson_18.py](lesson_18.py) | [操作手册](notes/lesson_18.md) | Fernet 文件加密解密；非 RKNN 原生加密 |
| 19 | [lesson_19.py](lesson_19.py) | [操作手册](notes/lesson_19.md) | 真实图片多 Batch 输入 |
| 20 | [lesson_20.py](lesson_20.py) | [操作手册](notes/lesson_20.md) | 多输入 ONNX Runtime |
| 21 | [lesson_21.py](lesson_21.py) | [操作手册](notes/lesson_21.md) | 多 Shape ONNX Runtime |
| 22 | [lesson_22.py](lesson_22.py) | [操作手册](notes/lesson_22.md) | ONNX Identity 移除及回归 |
| 23 | [lesson_23.py](lesson_23.py) | [操作手册](notes/lesson_23.md) | 真实 ONNX 生成 C++ 接口头 |
| 24 | [lesson_24.py](lesson_24.py) | [操作手册](notes/lesson_24.md) | RKNNLite 板端推理（需板卡） |
| 25 | [lesson_25.py](lesson_25.py) | [操作手册](notes/lesson_25.md) | RKNPU2 C++ 编译及推理（需板卡） |
| 26 | [lesson_26.py](lesson_26.py) | [操作手册](notes/lesson_26.md) | 真实缓冲字节校验；零拷贝 NPU 推理尚未实现 |
| 27 | [lesson_27.py](lesson_27.py) | [操作手册](LESSON_27.md) | MobileNet 分类 ONNX CI 通过；RKNNLite 待板测 |
| 28 | [lesson_28.py](lesson_28.py) | [操作手册](notes/lesson_28.md) | MobileNet ONNX 分类封装及批图处理 |
| 29 | [lesson_29.py](lesson_29.py) | [操作手册](notes/lesson_29.md) | Ultralytics 真正检测或官方 RKNN Demo（需模型） |
| 30 | [lesson_30.py](lesson_30.py) | [操作手册](notes/lesson_30.md) | Ultralytics 真正预测 |
| 31 | [lesson_31.py](lesson_31.py) | [操作手册](notes/lesson_31.md) | YOLO 数据标注检查及可选真实训练 |
| 32 | [lesson_32.py](lesson_32.py) | [操作手册](notes/lesson_32.md) | YOLO ONNX 导出与可选 RKNN 编译 |
| 33 | [lesson_33.py](lesson_33.py) | [操作手册](notes/lesson_33.md) | 真实 YOLO 模型时延对照（主机，不是 NPU） |
| 34 | [lesson_34.py](lesson_34.py) | [操作手册](notes/lesson_34.md) | 真实 RKLLM 进程驱动和日志；需适配实际 SDK CLI |

## 实机交付仍缺的东西

NPU 的真实 Driver/Runtime 版本、SDK 构建兼容性、单变量性能报告、零拷贝实际 memcpy/DMA 同步及板端测量、完整 YOLO 端到端摄像头工程、RKLLM 长上下文真实输出，均需另行在明确的开发板上测试。不得把 PC 上输出的 JSON 当作 NPU 性能验收。
