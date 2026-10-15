# RK3588 课程的真实源码与运行说明

这次增加的是真实 Python/C++ 文件，不再只是讲义伪代码。分为两类：

1. examples/lesson_00.py 到 lesson_34.py（35 个可执行入口）及 labs.py：Python >=3.9 标准库。实现数学算法、数据格式检查、只读系统诊断、性能统计、YOLO NMS/letterbox 等真实计算。没有板卡时也能学习、运行和测试。它们不冒充 RK3588 上的真实模型推理。
2. examples/hardware/：SDK/模型/硬件依赖的真实模型转换及推理代码。需要你自己的 ONNX、RKNN、输入 tensor、匹配的 Toolkit2/Lite2/RKNPU2。

## 代码完成度审计（2026-10-16）

**重要纠正：35 个编号脚本不等于 35 个完整独立实验工程。** 实测仓库源码发现：

- **第 27 讲**：已从薄包装改为约 255 行真实推理程序，具有 ONNX Runtime 和 RKNNLite 路径；ONNX 路径在 GitHub Actions 使用真实 CNN 模型、真实 PNG 图像执行成功，RK3588 硬件运行尚未实测。
- **其余 25 讲（09–26、28–34）**：编号脚本仍只是 `from labs import main` 加对应编号的 7 行入口；其中部分真实算法计算在公共 `labs.py`，另有部分工具代码存在于 `hardware/`，但不能说这些课程已有独立完整板端项目。
- **硬件专项**：RKNN 模型转换、RKNNLite 推理、单输入 C++ 分类、Ultralytics 模型导出、ONNX 参考推理和输入张量准备等源码已提供，模型/SDK/硬件兼容性需目标环境检验。零拷贝完整工程、摄像头 YOLO 检测和 RKLLM 应用等仍未交付独立可验收实现。

逐课状态参见 [CODE_STATUS.md](CODE_STATUS.md)。请不要仅凭脚本数量和 CI 的入口测试通过宣称全部课程代码完成。

## 第 00–08 讲：各讲独立实验

第 00–08 讲已从统一包装器改成针对课程目标的独立程序，包括环境记录、板级只读诊断、卷积计算量、部署流程图、官方仓库 ref 校验、Toolkit2 环境、NPU Runtime 检查、频率时间序列和真正调用外部 RKNN Demo。每讲还提供 [实验说明](notes/)，功能回归测试已加入持续集成。网络访问、真实 NPU 和驱动依赖仍然需要对应环境；不能把离线控制流程测试误写为实机通过。

## 第 27 讲：真实 MobileNet 分类推理

`lesson_27.py` 现为约 255 行独立工程，不再使用 `labs.py` 的模拟 Top-K。它需要真实 ONNX / RKNN 模型和图片；支持 ONNX Runtime CPU 与 RKNNLite 端侧路径。详见 [第 27 讲运行说明](LESSON_27.md)，包含可重复的微型 ONNX 模型测试及官方 MobileNetV2 权重获取地址。

## 运行普通电脑实验

从仓库根目录执行以下命令：

    python3 examples/lesson_00.py
    python3 examples/lesson_02.py
    python3 examples/lesson_10.py
    python3 examples/lesson_14.py
    python3 examples/lesson_29.py
    python3 examples/lesson_31.py
    python3 -m unittest discover -s examples/tests -v

Windows 可以使用 py -3 替代 python3。

必须提供真实文件的实验：

    python3 examples/lesson_09.py --input model.onnx
    python3 examples/lesson_11.py --input README.md
    python3 examples/lesson_18.py --input README.md
    python3 -m pip install onnx
    python3 examples/lesson_12.py --input model.onnx
    python3 examples/lesson_31.py --input dataset/labels/train

第 18 讲执行 SHA-256 完整性检查，不是模型加密。第 08 等展示输出的实验采用标明的演示性数据，绝非实际 NPU 测量结果。

## 真正的 RKNN 模型转换（开发机）

先在官方 SDK 支持的 Linux x86_64/Python 环境安装 RKNN-Toolkit2。转换前核对源模型的 mean/std 与 RGB/BGR。下面的 mean/std 是某些官方 YOLOv5 实例使用的配置，不适用于所有模型：

    python3 examples/hardware/convert_onnx.py --onnx model.onnx --output model.rknn --mean 0,0,0 --std 255,255,255

INT8 量化还需真实校准图片列表：

    python3 examples/hardware/convert_onnx.py --onnx model.onnx --output model_int8.rknn --mean 0,0,0 --std 255,255,255 --quantize --dataset calibration.txt

## 不下载预训练权重，也能跑通真实 ONNX 推理

从仓库根目录运行以下命令，在普通 PC 使用真实 ONNX 计算图：

    python3 -m pip install numpy onnx onnxruntime pillow
    python3 examples/hardware/create_tiny_onnx.py --onnx build/tiny.onnx --input-npy build/input.npy --input-raw build/input.raw
    python3 examples/hardware/onnx_reference.py --onnx build/tiny.onnx --input-npy build/input.npy --output build/onnx_output.npz
    python3 examples/hardware/compare_outputs.py --reference build/onnx_output.npz --candidate build/onnx_output.npz

生成的 toy CNN 由 Conv → GlobalAveragePool → Flatten 组成，权重被明确设置为输入红色和绿色通道各自的均值。预期输出约 [0.5, 0.25]，是真正的 ONNX Runtime 计算，而非在程序里打印硬编码推理结果。

如需继续验证 RKNN 转换，准备主机 RKNN-Toolkit2：

    python3 examples/hardware/convert_onnx.py --onnx build/tiny.onnx --output build/tiny.rknn --mean 0,0,0 --std 1,1,1

注意这个生成模型接收的是 float32 NCHW，[1,3,4,4]。RKNN 转换、板端输入属性、运行时数值及算子支持必须再核对；不要在未经检查时直接假定 raw 文件能交给任何版本的 NPU Runtime。

## ONNX Runtime 参考推理（开发机）

准备真实预处理后的输入 tensor 文件 input.npy，其 shape/dtype 必须匹配 ONNX：

    python3 -m pip install numpy onnxruntime
    python3 examples/hardware/onnx_reference.py --onnx model.onnx --input-npy input.npy --output reference.npz

程序运行真实 ONNX Runtime 并将输出保存为 NPZ 文件，便于后续比较。

## RK3588 上真实 Lite2 NPU 推理

在 RK3588 板上安装匹配 BSP 的 RKNNLite wheel、NumPy、Runtime/Driver，然后执行：

    python3 examples/hardware/lite_infer.py --rknn model.rknn --input-npy input.npy --output board.npz --warmup 5 --runs 20

input.npy 必须是按实际模型协议准备的真实 tensor，并非随意生成的数据。程序打印 RKNNLite 接口耗时与输出 shape，输出不是摄像头端到端 FPS。

## RKNPU2 C++ 推理

硬件工程文件：examples/hardware/rknn_classify.cpp、examples/hardware/CMakeLists.txt。

此程序适用于单输入单输出的分类模型，输入是预处理后的 raw tensor 文件而不是 JPG 图片。确保 SDK 的 rknn_api.h、适配 RK3588 ARM64 的 librknnrt.so、板端 Driver 与 RKNN 模型相兼容。示例命令：

    cmake -S examples/hardware -B build/rknn -DRKNN_INCLUDE_DIR=/absolute/path/to/include -DRKNN_LIB=/absolute/path/to/librknnrt.so
    cmake --build build/rknn -j
    ./build/rknn/rknn_classifier model.rknn input_tensor.raw

原始 tensor 的字节数、type、format 要与程序查询到的模型输入属性一致。示例输出类别索引与数值，具体类别名称须使用该模型配套的标签表。

## Ultralytics 模型导出 ONNX

在训练主机上安装 Ultralytics 与 ONNX，准备真实的 best.pt：

    python3 -m pip install ultralytics onnx
    python3 examples/hardware/export_yolo_onnx.py --weights best.pt --imgsz 640

该程序真实导出并用 ONNX checker 检查。能导出 ONNX 不意味着特定 YOLO26 模型已经得到 RK3588 RKNN 编译器支持；继续做 ONNX Runtime 与 RKNN 兼容验证。对于官方支持的检测模型完整图像采集与解码，优先使用同一版本的 RKNN Model Zoo 官方 YOLOv5/YOLOv8 完整示例。


## 生成真实图片输入与检查差异

上面 Lite2 和 ONNX Runtime 的 input.npy 不能随意填充，必须从真实图片生成，并与具体模型的预处理保持一致。需要安装 Pillow、NumPy：

    python3 -m pip install numpy pillow
    python3 examples/hardware/prepare_image.py --image test.jpg --width 224 --height 224 --color RGB --layout NHWC --dtype uint8 --output input.npy --raw input_tensor.raw

若模型真正要求 float32 NCHW，且训练输入按 0–1 做标准化，应把 --dtype 设置为 float32、--layout 设为 NCHW、--scale 设为 0.0039215686，并按该模型的 mean/std 传参数。不要对已经由 RKNN config 完成归一化的输入再重复执行这些变换。

比较真正推理产生的两个 NPZ 文件：

    python3 examples/hardware/compare_outputs.py --reference reference.npz --candidate board.npz --atol 0.01 --rtol 0.01

差异输出可用于排错，但量化模型不能仅凭逐元素 allclose 作为任务精度结论；检测模型还需使用匹配后处理比较 mAP 和漏检。

## 代码与测试状态

- 35 个 Python 文件只是对应的课程实验入口，算法实现在公用 labs.py。并非 35 套独立模型部署工程。
- Python 自测：python3 -m unittest discover -s examples/tests -v
- GitHub Actions：.github/workflows/examples-ci.yml 负责编译语法和测试 Python 入口。
- hardware/ 是实际 SDK 代码，但没有所需模型/板卡就无法确认运行结果。本仓库未提供声称实测通过的 C++ 二进制、模型权重或产测日志。
- 特定 SDK API 的行为请以官方发布版本的 rknn_api.h、RKNN-Toolkit2 文档为准。

官方参考：https://github.com/airockchip/rknn-toolkit2
模型示例：https://github.com/airockchip/rknn_model_zoo
