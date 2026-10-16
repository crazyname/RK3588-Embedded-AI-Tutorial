[逐讲源码复核与待完成工程](INDEPENDENT_CODE_REVIEW.md)

# RK3588：35 节课程源码与去重实验手册

## 文档分工：不重复

- **`docs/*.md`（35份课程 MD）**：负责学习目标、概念、原理、案例、自测、课程字幕与参考资料。
- **`examples/notes/lesson_XX.md`（34份）+ `examples/LESSON_27.md`（1份）**：负责该实例需要哪些输入文件、如何安装依赖、精确运行命令、输出在哪、如何验收与排错。**不复制理论段落**。
- **`examples/lesson_XX.py`（35个独立程序）**：负责真正执行各讲对应的算法、诊断、模型工具或 SDK 调用。代码文件不再使用原先的七行 `from labs import main` 包装。
- **`examples/hardware/`**：保存可复用的 RKNN、ONNX、RKNNLite 和 C++ 工具代码；不需要在每个 lesson 文件中重复造轮子。

**验收边界**：35 个脚本独立重写≠35 个实机部署项目均已完成。无 RK3588 时可在 CI 实测 PC 部分；零拷贝、RKLLM、板端 YOLO 等必须有真实板卡及 SDK/模型才能做最终验收。

## 去重实例索引

| 课次 | 实操源码 | 实操说明 | 对应理论 |
|---|---|---|---|
| 00 导学 | [Python](lesson_00.py) | [操作 MD](notes/lesson_00.md) | [课程 MD](../docs/00_%E5%AF%BC%E5%AD%A6.md) |
| 01 快速了解rk3588 | [Python](lesson_01.py) | [操作 MD](notes/lesson_01.md) | [课程 MD](../docs/01_%E5%BF%AB%E9%80%9F%E4%BA%86%E8%A7%A3rk3588.md) |
| 02 NPU原理及对比 | [Python](lesson_02.py) | [操作 MD](notes/lesson_02.md) | [课程 MD](../docs/02_NPU%E5%8E%9F%E7%90%86%E5%8F%8A%E5%AF%B9%E6%AF%94.md) |
| 03 RKNPU推理软件架构与模型部署流程 | [Python](lesson_03.py) | [操作 MD](notes/lesson_03.md) | [课程 MD](../docs/03_RKNPU%E6%8E%A8%E7%90%86%E8%BD%AF%E4%BB%B6%E6%9E%B6%E6%9E%84%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E6%B5%81%E7%A8%8B.md) |
| 04 瑞芯微github仓库介绍 | [Python](lesson_04.py) | [操作 MD](notes/lesson_04.md) | [课程 MD](../docs/04_%E7%91%9E%E8%8A%AF%E5%BE%AEgithub%E4%BB%93%E5%BA%93%E4%BB%8B%E7%BB%8D.md) |
| 05 搭建rknn · toolkit2开发环境 | [Python](lesson_05.py) | [操作 MD](notes/lesson_05.md) | [课程 MD](../docs/05_%E6%90%AD%E5%BB%BArknn_toolkit2%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83.md) |
| 06 设备端npu环境搭建与npu驱动更新 | [Python](lesson_06.py) | [操作 MD](notes/lesson_06.md) | [课程 MD](../docs/06_%E8%AE%BE%E5%A4%87%E7%AB%AFnpu%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8Enpu%E9%A9%B1%E5%8A%A8%E6%9B%B4%E6%96%B0.md) |
| 07 查看和调整CPU · NPU · DDR频率 | [Python](lesson_07.py) | [操作 MD](notes/lesson_07.md) | [课程 MD](../docs/07_%E6%9F%A5%E7%9C%8B%E5%92%8C%E8%B0%83%E6%95%B4CPU_NPU_DDR%E9%A2%91%E7%8E%87.md) |
| 08 快速体验rknn · demo | [Python](lesson_08.py) | [操作 MD](notes/lesson_08.md) | [课程 MD](../docs/08_%E5%BF%AB%E9%80%9F%E4%BD%93%E9%AA%8Crknn_demo.md) |
| 09 rknn模型转换 | [Python](lesson_09.py) | [操作 MD](notes/lesson_09.md) | [课程 MD](../docs/09_rknn%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2.md) |
| 10 均值和标准差 | [Python](lesson_10.py) | [操作 MD](notes/lesson_10.md) | [课程 MD](../docs/10_%E5%9D%87%E5%80%BC%E5%92%8C%E6%A0%87%E5%87%86%E5%B7%AE.md) |
| 11 模型转换工具rknn · convert | [Python](lesson_11.py) | [操作 MD](notes/lesson_11.md) | [课程 MD](../docs/11_%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2%E5%B7%A5%E5%85%B7rknn_convert.md) |
| 12 Netron的基本使用 | [Python](lesson_12.py) | [操作 MD](notes/lesson_12.md) | [课程 MD](../docs/12_Netron%E7%9A%84%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md) |
| 13 rknn-toolkit2模型推理 | [Python](lesson_13.py) | [操作 MD](notes/lesson_13.md) | [课程 MD](../docs/13_rknn-toolkit2%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86.md) |
| 14 模型量化精度分析 | [Python](lesson_14.py) | [操作 MD](notes/lesson_14.md) | [课程 MD](../docs/14_%E6%A8%A1%E5%9E%8B%E9%87%8F%E5%8C%96%E7%B2%BE%E5%BA%A6%E5%88%86%E6%9E%90.md) |
| 15 模型性能评估 | [Python](lesson_15.py) | [操作 MD](notes/lesson_15.md) | [课程 MD](../docs/15_%E6%A8%A1%E5%9E%8B%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.md) |
| 16 模型内存评估 | [Python](lesson_16.py) | [操作 MD](notes/lesson_16.md) | [课程 MD](../docs/16_%E6%A8%A1%E5%9E%8B%E5%86%85%E5%AD%98%E8%AF%84%E4%BC%B0.md) |
| 17 模型剪枝 | [Python](lesson_17.py) | [操作 MD](notes/lesson_17.md) | [课程 MD](../docs/17_%E6%A8%A1%E5%9E%8B%E5%89%AA%E6%9E%9D.md) |
| 18 模型加密 | [Python](lesson_18.py) | [操作 MD](notes/lesson_18.md) | [课程 MD](../docs/18_%E6%A8%A1%E5%9E%8B%E5%8A%A0%E5%AF%86.md) |
| 19 多Batch处理 | [Python](lesson_19.py) | [操作 MD](notes/lesson_19.md) | [课程 MD](../docs/19_%E5%A4%9ABatch%E5%A4%84%E7%90%86.md) |
| 20 多输入模型 | [Python](lesson_20.py) | [操作 MD](notes/lesson_20.md) | [课程 MD](../docs/20_%E5%A4%9A%E8%BE%93%E5%85%A5%E6%A8%A1%E5%9E%8B.md) |
| 21 动态shape输入 | [Python](lesson_21.py) | [操作 MD](notes/lesson_21.md) | [课程 MD](../docs/21_%E5%8A%A8%E6%80%81shape%E8%BE%93%E5%85%A5.md) |
| 22 ONNX模型编辑 | [Python](lesson_22.py) | [操作 MD](notes/lesson_22.md) | [课程 MD](../docs/22_ONNX%E6%A8%A1%E5%9E%8B%E7%BC%96%E8%BE%91.md) |
| 23 自动生成部署C代码 | [Python](lesson_23.py) | [操作 MD](notes/lesson_23.md) | [课程 MD](../docs/23_%E8%87%AA%E5%8A%A8%E7%94%9F%E6%88%90%E9%83%A8%E7%BD%B2C%E4%BB%A3%E7%A0%81.md) |
| 24 RKNN-ToolkitLite2基本使用 | [Python](lesson_24.py) | [操作 MD](notes/lesson_24.md) | [课程 MD](../docs/24_RKNN-ToolkitLite2%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md) |
| 25 RKNPU2—通用C API | [Python](lesson_25.py) | [操作 MD](notes/lesson_25.md) | [课程 MD](../docs/25_RKNPU2%E2%80%94%E9%80%9A%E7%94%A8C%20API.md) |
| 26 RKNPU2—零拷贝C API | [Python](lesson_26.py) | [操作 MD](notes/lesson_26.md) | [课程 MD](../docs/26_RKNPU2%E2%80%94%E9%9B%B6%E6%8B%B7%E8%B4%9DC%20API.md) |
| 27 mobilenet模型部署 | [Python](lesson_27.py) | [操作 MD](LESSON_27.md) | [课程 MD](../docs/27_mobilenet%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md) |
| 28 mobilenet模型代码封装 | [Python](lesson_28.py) | [操作 MD](notes/lesson_28.md) | [课程 MD](../docs/28_mobilenet%E6%A8%A1%E5%9E%8B%E4%BB%A3%E7%A0%81%E5%B0%81%E8%A3%85.md) |
| 29 yolov5模型部署实战 | [Python](lesson_29.py) | [操作 MD](notes/lesson_29.md) | [课程 MD](../docs/29_yolov5%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E5%AE%9E%E6%88%98.md) |
| 30 yolov26模型部署(从0到1版) · windows环境搭建与模型预测分析 | [Python](lesson_30.py) | [操作 MD](notes/lesson_30.md) | [课程 MD](../docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_windows%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%A2%84%E6%B5%8B%E5%88%86%E6%9E%90.md) |
| 31 yolov26模型部署(从0到1版) · 数据集构建与模型训练 | [Python](lesson_31.py) | [操作 MD](notes/lesson_31.md) | [课程 MD](../docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E6%95%B0%E6%8D%AE%E9%9B%86%E6%9E%84%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83.md) |
| 32 yolov26模型部署(从0到1版) · 导出onnx与rknn模型并板端推理 | [Python](lesson_32.py) | [操作 MD](notes/lesson_32.md) | [课程 MD](../docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E5%AF%BC%E5%87%BAonnx%E4%B8%8Erknn%E6%A8%A1%E5%9E%8B%E5%B9%B6%E6%9D%BF%E7%AB%AF%E6%8E%A8%E7%90%86.md) |
| 33 yolov8模型部署(优化加速版) | [Python](lesson_33.py) | [操作 MD](notes/lesson_33.md) | [课程 MD](../docs/31_yolov8%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BC%98%E5%8C%96%E5%8A%A0%E9%80%9F%E7%89%88%29.md) |
| 34 Deepseek · Qwen大模型部署 | [Python](lesson_34.py) | [操作 MD](notes/lesson_34.md) | [课程 MD](../docs/32_Deepseek_Qwen%E5%A4%A7%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md) |

## 运行普通电脑实验

从仓库根目录执行以下命令：

    python3 examples/lesson_00.py
    python3 examples/lesson_02.py
    python3 examples/lesson_10.py
    python3 examples/lesson_14.py
    python3 examples/lesson_02.py
    python3 examples/lesson_03.py
    python3 -m unittest discover -s examples/tests -v

Windows 可以使用 py -3 替代 python3。

必须提供真实文件的实验：

    python3 examples/lesson_09.py --onnx model.onnx --output build/model.rknn
    python3 examples/lesson_11.py --jobs jobs.json
    python3 examples/lesson_18.py generate-key --key-file build/test.key
    python3 -m pip install onnx
    python3 examples/lesson_12.py --onnx model.onnx
    python3 examples/lesson_31.py --labels dataset/labels/train

第 18 讲新增对文件的真实 Fernet 加密/解密（非 RKNN 原生模型加密格式）；第 08 讲调用实际 Demo，不再生成虚拟推理数据。

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


## 第26讲：真正的零拷贝 C API（设备专用）

已提供 [rknn_zero_copy.cpp](hardware/rknn_zero_copy.cpp)；它将真实模型载入 RKNPU2，调用 `rknn_create_mem`、`rknn_set_io_mem` 绑定输入输出缓冲，执行 `rknn_run` 并清理资源。该示例**仅适用于满足 uint8 NHWC 输入与所用 RKNN Runtime 兼容要求的单输入单输出模型**。它需要按 SDK 查询的 `size_with_stride` 准备含对齐填充的 raw 输入，而不是普通图像文件。

```bash
python3 examples/lesson_26.py --model model.rknn \
  --input-raw padded_input.raw --execute \
  --include /sdk/include --library /sdk/librknnrt.so --runs 20
```

GitHub CI 仅执行与官方 RK3588 SDK `rknn_api.h` 的 **C++ 语法/接口检查**。只有在你的开发板上真正运行后，才能进一步声称 SDK 接口适配与性能指标已验收；编译通过本身不代表零拷贝性能收益。

## 生成真实图片输入与检查差异

上面 Lite2 和 ONNX Runtime 的 input.npy 不能随意填充，必须从真实图片生成，并与具体模型的预处理保持一致。需要安装 Pillow、NumPy：

    python3 -m pip install numpy pillow
    python3 examples/hardware/prepare_image.py --image test.jpg --width 224 --height 224 --color RGB --layout NHWC --dtype uint8 --output input.npy --raw input_tensor.raw

若模型真正要求 float32 NCHW，且训练输入按 0–1 做标准化，应把 --dtype 设置为 float32、--layout 设为 NCHW、--scale 设为 0.0039215686，并按该模型的 mean/std 传参数。不要对已经由 RKNN config 完成归一化的输入再重复执行这些变换。

比较真正推理产生的两个 NPZ 文件：

    python3 examples/hardware/compare_outputs.py --reference reference.npz --candidate board.npz --atol 0.01 --rtol 0.01

差异输出可用于排错，但量化模型不能仅凭逐元素 allclose 作为任务精度结论；检测模型还需使用匹配后处理比较 mAP 和漏检。

## 代码与测试状态

- 35 个课程 Python 源码已独立实现各自实验目标，不再通过 labs.py 按课号统一分发；部分仍依赖厂商 SDK、其他二进制或真实模型，不能视为 35 套均通过板端验收的项目。
- Python 自测：python3 -m unittest discover -s examples/tests -v
- GitHub Actions：.github/workflows/examples-ci.yml 负责编译语法和测试 Python 入口。
- hardware/ 是实际 SDK 代码，但没有所需模型/板卡就无法确认运行结果。本仓库未提供声称实测通过的 C++ 二进制、模型权重或产测日志。
- 特定 SDK API 的行为请以官方发布版本的 rknn_api.h、RKNN-Toolkit2 文档为准。

官方参考：https://github.com/airockchip/rknn-toolkit2
模型示例：https://github.com/airockchip/rknn_model_zoo

## C++ RKNPU2 输入绑定对照与 RGA 前处理

- [同模型普通输入/绑定输入比较](hardware/rknn_compare_input_io.cpp)
- [librga RGB888 缩放与黑边](hardware/rga_letterbox_rgb888.cpp)
- [ROCK 5B 编译、运行和数据校验手册](../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md)

当前 C++ 对照只支持单输入单输出分类模型，不支持 YOLOv8 的多个输出；SDK 绑定输入仍先经 CPU memcpy，不能称为完整零拷贝。

## 原生 C++ 优化版 YOLOv8 多输出检测

- [C++ FP32 DFL 解码、按类 NMS](hardware/yolov8_postprocess.cpp)
- [实际 RKNPU2 C API 多输出模型推理](hardware/rknn_yolov8_raw.cpp)
- [C++ 纯 CPU 张量离线解码](hardware/yolov8_decode_files.cpp)
- [同源 640 RGB 数据准备工具](../tools/prepare_yolov8_rgb.py)
- [ROCK 5B 原生编译、V4L2 DMA-BUF 检查及验收手册](../boards/radxa-rock5b/CPP_YOLOV8_NATIVE.md)

当前原生 C++ 主程序使用预处理好的 RGB raw，不是 V4L2 摄像头图像直送 NPU；CI mock 不代表真实 NPU 结果。
