# 官方手册索引：以 ROCK 5B 原版为准

| 需求 | 最合适的官方资料 | 本课程对应 |
|---|---|---|
| 确认型号、SoC、RAM、板载 Wi-Fi 与接口 | [产品介绍](https://docs.radxa.com/en/rock5/rock5b/getting-started/introduction) | 第 01–03 讲、板卡选择 |
| PD 供电和典型启动问题 | [电源选择](https://docs.radxa.com/rock5/rock5b/getting-started/power-supply)、[常见问题](https://docs.radxa.com/rock5/rock5b/faq) | 第 00、06、07 讲 |
| 安装 Debian、制作 SD 启动盘 | [镜像列表](https://docs.radxa.com/rock5/rock5b/download)、[microSD 安装步骤](https://docs.radxa.com/rock5/rock5b/getting-started/install-os/boot_from_sd_card) | 第 05–06 讲 |
| 原理图、PCB 版本与引脚设计 | [硬件设计文件](https://docs.radxa.com/rock5/rock5b/download)、[硬件说明](https://docs.radxa.com/rock5/rock5b/hardware-design) | 第 01–03 讲，外设扩展 |
| Toolkit2、Lite2、驱动和 NPU | [RKNN 安装](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install) | 第 04–14、24–26 讲 |
| 第一次官方模型上板 | [YOLOv8 实际部署](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-toolkit-lite2-yolov8) | 第 08、29、33 讲 |
| MobileNet 分类/C API | [MobileNet](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/mobilenet) | 第 25、27–28 讲 |
| 摄像头和图像预处理 | [OpenCV](https://docs.radxa.com/en/rock5/rock5b/app-development/opencv)、[RGA](https://docs.radxa.com/en/rock5/rock5b/app-development/rga) | 第 10、29、33 讲 |
| LLM 与大模型适配 | [AI 官方索引](https://docs.radxa.com/en/rock5/rock5b/app-development/ai) 里 RKLLM 教程 | 第 34 讲 |

## 版本固定原则

- **本课程的第一块板**：ROCK 5B 16GB **原版**，不对 ROCK 5B+ 做接口、电源、eMMC/NVMe 布局方面的隐式推断。
- **首轮推荐目标系统**：Radxa 下载页面列出的 **ROCK 5B Debian Bookworm（内核 6.1）官方镜像**，并记录实际 release 名称和 SHA256。页面同时列有 5.10 镜像；教程不能把两者的驱动兼容性混为一谈。
- **NPU 工具链**：Radxa 的 RKNN 安装页面目前提供 Toolkit2 v2.3.2 的实例及对应 Python 版本提示；本课程不假定“最新版 SDK”就能与任意老镜像驱动匹配。
- **厂商示例**：采用 `rknn-model-zoo-rk3588` 包中的配套 `.rknn`、Python YOLOv8 后处理，不要随意替换上游原生 YOLO 权重。
- **原理图**：网站分别公布 V1.3、V1.42、V1.423、V1.45、V1.46 等板级资料。**先核对真实 PCB 上丝印的版本号，再选择对应设计图**；不要用一个版本的排针/原理图确认另一版本的电气连接。

## 特别要区分的事情

1. `uname -m` 返回 aarch64 只证明 CPU 架构，不证明板卡就是 ROCK 5B。
2. 在 `/proc/device-tree/model` 读到 ROCK 5B 可以判断设备树目标，但设备树本身也可能被刷错；再结合 PCB 丝印确认实体。
3. 发现 `rknpu` 设备节点或驱动信息，只代表驱动有加载迹象；还需要用**真实模型推理**完成 NPU 验证。
4. 设备树不同、镜像不同或 PCB 版本不同，应先保存证据，不要直接照抄网络教程执行 `dd`、`rkdeveloptool`、`modprobe` 或固件写入命令。

本文件是根据官方资料整理的独立导航，不是复制的厂商手册。
