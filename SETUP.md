# 从零准备 RK3588 自学环境

将普通 PC、模型转换主机和 ROCK 5B 板端当作不同环境。Python 版本、SDK wheel、NPU Runtime 不能任意混装。

| 用途 | 推荐环境 | 依赖 |
|---|---|---|
| ONNX/算法/单元测试 | Windows 11 或 Ubuntu x86_64，Python 3.11 | [PC 基础依赖](requirements/pc-core.txt) |
| 图像检测/训练 | PC Windows/Ubuntu，根据训练框架配 GPU | [视觉依赖](requirements/pc-vision.txt)；PyTorch GPU 包按官方说明另行安装 |
| ONNX→RKNN | SDK 支持的 Ubuntu x86_64 与 Python ABI | 官方 RKNN-Toolkit2 wheel |
| ROCK 5B NPU | aarch64、匹配 BSP / Driver | [板端基础依赖](requirements/board-helpers.txt) 加匹配 SDK 的 RKNNLite wheel |

## PC 安装

Windows PowerShell：

    py -3.11 tools/bootstrap_host.py --group core --apply
    .venv\Scripts\python.exe -m unittest discover -s examples/tests -v

Ubuntu/Linux：

    python3 tools/bootstrap_host.py --group core --apply
    .venv/bin/python -m unittest discover -s examples/tests -v

默认仅显示安装计划；只有加 --apply 才会创建 venv 并安装包。整个过程中不执行 sudo，不刷写设备。

## 真实 ONNX 最小示例

    python3 examples/hardware/create_tiny_onnx.py --onnx build/fixtures/tiny.onnx --input-npy build/fixtures/input.npy
    python3 examples/hardware/onnx_reference.py --onnx build/fixtures/tiny.onnx --input-npy build/fixtures/input.npy --output build/fixtures/out.npz
    python3 tools/verify_assets.py --id tiny-conv-onnx --strict

运行时请选择虚拟环境中的 Python。生成的 tiny 模型仅用于 ONNX 工具链烟雾测试，不是真正的分类准确率实验。

## RKNN 环境不是一个通用的 pip install

先根据 [版本兼容记录](requirements/COMPATIBILITY.md) 和 [Radxa 官方 RKNN 安装文档](https://docs.radxa.com/en/rock5/rock5b/app-development/ai/rknn-install) 确认 x86 Toolkit2、aarch64 Lite2、板端 Driver、Runtime、镜像和编译模型版本。脚本不会自动刷机、修改内核或提升权限。

## 资源与全仓检查

模型来源、许可、SHA256 管理见 [模型资源说明](models/README.md)。真实资源默认不提交到 Git。

    python3 examples/audit_course.py --strict
    python3 tools/validate_repo.py
    python3 tools/verify_assets.py --list

硬件上电与设备检查另见 [ROCK 5B 实操](boards/radxa-rock5b/FIRST_BOOT.md)。
