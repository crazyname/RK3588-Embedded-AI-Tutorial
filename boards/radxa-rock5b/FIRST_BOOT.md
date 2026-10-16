# ROCK 5B：首次上电与首个 NPU 验收

本文以 **ROCK 5B 原版**和 Radxa 官方 Debian/Radxa OS 为目标。不要在没有检查型号与启动介质的情况下执行任何写入 eMMC/SPI/NVMe 的操作。

## 第一关：不通电检查

1. 取下主板所有包装材料，查看 PCB 丝印：记录“ROCK 5B”和 V1.xx 修订号；确认不是 5B+。
2. 检查 USB-C 电源是否符合 [官方 5B 电源说明](https://docs.radxa.com/rock5/rock5b/getting-started/power-supply)。推荐官方 Radxa PD30W 与配套线。
3. 装好兼容散热器，放在不导电、通风的平面上。首轮不用 GPIO 直接供电。
4. 准备一张 microSD；保存重要数据，然后在**电脑端**用 [官方镜像列表](https://docs.radxa.com/rock5/rock5b/download) 中适用于 ROCK **5B** 的 Debian 镜像制作启动盘。优先使用与官方文档一致的 Balena Etcher；烧录会清除所选 SD 卡，请反复确认目标盘。
5. 有条件时连接 HDMI、键鼠和网线；最后再接 USB-C 电源。

## 第二关：启动与基础环境

首次启动到桌面或终端后，确认系统归属和设备状态：

    uname -m
    uname -a
    cat /proc/device-tree/model
    cat /etc/os-release
    free -h
    df -h

只看输出，不修改任何设备配置。板卡型号、芯片内核、文件系统信息应与实际镜像吻合；若出现异常，先检查引导顺序和镜像型号。

从仓库根目录运行：

    python3 boards/radxa-rock5b/tools/board_probe.py --strict
    python3 boards/radxa-rock5b/tools/board_probe.py --strict --output boards/radxa-rock5b/results/rock5b-board.json

`--strict` 在非原版 ROCK 5B ARM64 环境拒绝通过，但该脚本只根据设备树判断；最终仍需核对 PCB 丝印。采集数据中不包含唯一序列号、MAC 或 Wi-Fi 密码；日志公开前仍请人工审核。

## 第三关：NPU 驱动是否存在

可先只读检查：

    ls /sys/class/devfreq/
    lsmod | grep -i rknpu || true
    dmesg | grep -Ei 'rknpu|npu' | tail -n 20

注意：`dmesg` 在某些系统上需要提升权限才能读取；驱动也可能编译进内核而不出现在 lsmod 中。驱动是否可用应以随后真实 RKNN 初始化与推理为准。**此步骤不执行驱动更新**。

如果官方镜像没有相关组件，按 [Radxa 的 RKNN 安装说明](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install) 核对 BSP/Runtime/SDK 版本，再决定怎么安装。避免混入为 RK3566/RK3568 编译的驱动。

## 第四关：首次真实 NPU 推理——优先用厂商预转换 YOLOv8

Radxa 官方 [YOLOv8 板端教程](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-toolkit-lite2-yolov8) 在 **Radxa OS** 中提供 `rknn-model-zoo-rk3588` 软件包和预转换模型。首先按照厂商软件源说明安装包：

    sudo apt update
    sudo apt install rknn-model-zoo-rk3588

只有确认是在匹配的软件源、软件包依赖符合当前镜像时才执行。安装后先确认文件：

    test -f /usr/share/rknn_model_zoo/examples/yolov8/python/yolov8.py && echo DEMO_FOUND
    test -f /usr/share/rknn_model_zoo/examples/yolov8/model/yolov8.rknn && echo MODEL_FOUND

若都存在，本仓库启动器先做 dry-run：

    python3 boards/radxa-rock5b/tools/run_official_yolov8.py --dry-run --save

真正执行由你主动启动：

    python3 boards/radxa-rock5b/tools/run_official_yolov8.py --save

若模型库仅对特定用户权限开放，则先按**官方教程**及系统安全策略处理权限问题；启动器不会自动以 root 执行。原版官方文档示例是：

    cd /usr/share/rknn_model_zoo/examples/yolov8/python
    sudo python3 yolov8.py --model_path ../model/yolov8.rknn --img_save

本课程以实际模型输出、有意义的检测框和生成的 `result/` 图片作为通过证据，而不是只看程序退出码为 0。运行时如果提示驱动/Runtime/模型版本不匹配，记录完整错误而不是立即刷机。

## 第五关：摄像头仅做图像采集验收

插入自己选择的 USB UVC 摄像头后，在板端查看：

    ls -l /dev/video*
    python3 boards/radxa-rock5b/tools/usb_camera_check.py --source /dev/video0 --frames 60 --save-json boards/radxa-rock5b/results/camera.json

`/dev/video0` 只是示例，必须按设备实际枚举的节点选择。某些 `/dev/videoX` 是编解码器或 ISP 的视频节点，并不代表 USB 摄像头；通过系统设备名称和真实读帧来确认。脚本只测帧采集，不执行 AI 推理。可选 `--save-image boards/radxa-rock5b/results/camera.jpg` 保存一张图片供检查，注意隐私。

## 第六关：摄像头与 MobileNet 联合运行

先确认第 5 关 USB 摄像头可正常读帧，且 [单图片 MobileNet 示例](apps/mobilenet_image_lite.py) 能用同一份 RKNN 模型推理。再按 [摄像头分类实验手册](CAMERA_MOBILENET.md) 运行 `apps/camera_mobilenet_lite.py`，保存真实帧率和 p95 耗时，不要将 CI 的模拟摄像头结果当作板端实测。

## 学习验收与记录

- [ ] PCB 确认为 ROCK 5B，修订号已记录，电源稳定、散热可靠。
- [ ] 系统镜像、内核、CPU 架构、RAM、Python 及设备树信息可复现。
- [ ] NPU 驱动/Runtime 信息或明确的缺失错误已记录。
- [ ] 官方 YOLOv8 样例产生了实际检测结果，保存真实日志和结果图（或明确记录未通过原因）。
- [ ] USB 摄像头（若配备）能从正确的设备节点读取连续帧。
- [ ] 摄像头→RKNNLite MobileNet 分类输出真实标签、保存摘要和每帧 JSONL（或记录明确失败原因）。
- [ ] 任何日志、图片上传仓库之前已检查隐私和大文件问题。

完成后可进入 [后续实际应用开发](NEXT_PROJECTS.md)。
