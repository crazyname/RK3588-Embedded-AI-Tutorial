# V4L2 DMA-BUF fd 导出预检：独立工程实验与验收

> 工程编号：`v4l2-dmabuf`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/26_RKNPU2—零拷贝C API.md](../docs/26_RKNPU2—零拷贝C API.md) · [HTML 连续滚动课件](../courseware/lessons/26_RKNPU2—零拷贝C API.html)

## 源码清单

- [`boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp`](../boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
g++ -std=c++17 -O2 -Wall -Wextra -Werror boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp -o build/v4l2_dma_probe
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 自动化测试

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`boards/radxa-rock5b/tests/test_board_tools.py`](../boards/radxa-rock5b/tests/test_board_tools.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

板端运行须记录真实 VIDIOC_EXPBUF 结果、设备格式和 fd 生命周期。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

预检只证明相机 fd 可导出，不证明 RGA/NPU 端到端共享。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
