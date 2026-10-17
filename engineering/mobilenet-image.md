# MobileNet RKNNLite 静态图片分类：独立工程实验与验收

> 工程编号：`mobilenet-image`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/24_RKNN-ToolkitLite2基本使用.md](../docs/24_RKNN-ToolkitLite2基本使用.md) · [HTML 连续滚动课件](../courseware/lessons/24_RKNN-ToolkitLite2基本使用.html)
- [Markdown：docs/27_mobilenet模型部署.md](../docs/27_mobilenet模型部署.md) · [HTML 连续滚动课件](../courseware/lessons/27_mobilenet模型部署.html)

## 源码清单

- [`boards/radxa-rock5b/apps/mobilenet_image_lite.py`](../boards/radxa-rock5b/apps/mobilenet_image_lite.py)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
python3 boards/radxa-rock5b/apps/mobilenet_image_lite.py --help
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 最小完整板端实验

先按 [ROCK 5B 初次启动](../boards/radxa-rock5b/FIRST_BOOT.md) 安装与当前驱动匹配的 RKNNLite2，准备**已确认输入为 RGB uint8 NHWC、224×224** 的 MobileNet RKNN 模型、测试图片和对应标签。模型文件不随教程捏造提供。

```bash
python3 -c "from rknnlite.api import RKNNLite; print('RKNNLite import OK')"
python3 boards/radxa-rock5b/apps/mobilenet_image_lite.py \
  --model /path/to/mobilenet.rknn --image /path/to/test.jpg \
  --labels /path/to/labels.txt --width 224 --height 224 \
  --topk 5 --runs 1 --warmup 0 --confirm-rgb-uint8-nhwc
```

逐项检查：图片读取→resize→BGR 转 RGB→NHWC uint8→Lite2 加载/初始化→输出张量→Top-5 标签。**只有模型转换时确实采用上述输入协议才能添加确认参数**；否则应修改预处理设置而不是强行运行。记录真实 Top-5 与概率、文件路径及版本，不预填类别或耗时。

## 自动化测试

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`boards/radxa-rock5b/tests/test_board_tools.py`](../boards/radxa-rock5b/tests/test_board_tools.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

真实运行必须指定匹配 .rknn 模型、图片与预处理协议，并保存 Top-K、模型哈希和异常日志。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

--help 和 mock SDK 不证明真实图片分类结果。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
