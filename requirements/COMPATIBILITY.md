# RK3588 SDK、系统与 Python 版本兼容记录

这个表格是实验环境记录模板，不是未经实机验证的兼容性承诺。

| 环节 | 需要记录 | 当前课程基准 |
|---|---|---|
| 板卡 | PCB 修订号、内存、型号 | ROCK 5B 原版 16 GB，实物待确认 |
| 主机 | Linux x86_64 版本、Python ABI | Toolkit2 官方 wheel 所支持的版本 |
| 板端 | Radxa OS 镜像名、SHA256、Kernel/BSP | 从 ROCK 5B 官方下载页选择 |
| NPU | RKNPU Driver 版本、错误日志 | 实机待记录 |
| Runtime | librknnrt.so SHA256、aarch64 ABI | 实机待记录 |
| RKNN Toolkit2 | wheel、SDK release、目标平台 | 与模型和板端 Runtime 对齐 |
| RKNN Toolkit Lite2 | aarch64 wheel、Python ABI | 与板端 BSP 对齐 |
| Model Zoo | commit、模型文件哈希、前处理约定 | 必须使用成套模型与后处理 |
| RKLLM | toolkit、runtime、模型版权许可 | 实机待记录 |

官方资料：https://github.com/airockchip/rknn-toolkit2

板商资料：https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install

操作前在本地结果目录记录上述信息，不把个人硬件序列号或私有训练数据上传公开仓库。
