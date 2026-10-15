# 实例 34：RKLLM 真实进程执行

[对应课程理论教材](../../docs/32_Deepseek_Qwen%E5%A4%A7%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md) 包含原理、案例和扩展题。本 MD **只保留执行手册**，避免重复讲解。

## 运行环境

真实 RK3588、官方匹配 RKLLM binary 与模型。

## 启动命令

```bash
python3 examples/lesson_34.py --program ./rkllm_demo --model model.rkllm --prompt 你好
```

所有选项：`python3 examples/lesson_34.py --help`。

## 输出和验收

来自实际程序的 stdout/stderr、退出码和时间，不伪造 token/s。输入文件必须来自实际模型/图片/数据集。无法从普通电脑的输出得出 RK3588 实机性能结论。

## 故障排查

检查 SDK release、操作系统架构、模型输出协议以及日志。训练集泄漏、后处理与转换算子差异需要单独检验，不应猜测模型已经全面兼容。
