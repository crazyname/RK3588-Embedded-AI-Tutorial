# 实验 C｜RKNPU2 C++ 图片分类与内存绑定

本实验用 C++ 读取已经准备好的 RAW 张量，调用真实 RKNPU2 C API，并与 Python Lite2 的同图结果对照。RAW 不是 JPEG 文件。

## 对应课程讲义与 HTML 课件

- [第25讲 RKNPU2 C API](../docs/25_RKNPU2—通用C API.md) · [HTML](../courseware/lessons/25_RKNPU2—通用C API.html)
- [第28讲 MobileNet 封装](../docs/28_mobilenet模型代码封装.md) · [HTML](../courseware/lessons/28_mobilenet模型代码封装.html)

## 源码清单

- [单输入分类 C++](../examples/hardware/rknn_classify.cpp)
- [常规输入与 SDK 内存绑定比较](../examples/hardware/rknn_compare_input_io.cpp)
- [张量输出比较工具](../examples/hardware/compare_outputs.py)

## 环境与输入

ROCK 5B ARM64 编译环境、rknn_api.h、匹配的 librknnrt.so、模型与测试图片。下面使用 RGB uint8 NHWC 224×224 且将归一化编译入模型的输入协议。若实际模型不同，应修改预处理而不是强行输入字节。

## 实验命令

~~~bash
cmake -S examples/hardware -B build/native-rknn -DRKNN_INCLUDE_DIR=/actual/rknn/include -DRKNN_LIB=/actual/arm64/librknnrt.so
cmake --build build/native-rknn --target rknn_classifier -j2
python3 examples/hardware/prepare_image.py --image /path/to/test.jpg --output build/classify_input.npy --raw build/classify_input.raw --width 224 --height 224 --color RGB --layout NHWC --dtype uint8
./build/native-rknn/rknn_classifier /path/to/mobilenet.rknn build/classify_input.raw
~~~

核心调用流程：rknn_init → rknn_query(输入/输出属性) → rknn_inputs_set → rknn_run → rknn_outputs_get(want_float=1) → rknn_outputs_release → rknn_destroy。观察查询输出的 input.size、type、fmt 和 dims，再读取 Top-5 index/score。

## 自动化测试

- [本地资源测试](../tools/tests/test_resource_tools.py)
- [真实图像 I/O 行为测试](../tools/tests/test_engineering_image_io.py)
- [假 SDK 下的 C++ 控制流测试](../examples/hardware/tests/test_native_classification.py)

## 验收标准

用同一个 RKNN 模型、同一图片、同一预处理协议分别跑 Python 和 C++，核对类别索引及数值差异。普通版本与 SDK 内存绑定的比较属于后续第 26 讲，可复用本实验输入。

## 验证边界

PC 上编译通过和假 SDK 测试不等于板端 NPU 实测，必须独立执行 ARM64 程序。这里也没有宣称摄像头到 NPU 端到端零拷贝。

