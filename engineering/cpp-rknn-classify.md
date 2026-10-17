# RKNPU2 C++ 分类和输入绑定对照：独立工程实验与验收

## 对应课程讲义与 HTML 课件

- [Markdown：docs/25_RKNPU2—通用C API.md](../docs/25_RKNPU2—通用C API.md) · [HTML 连续滚动课件](../courseware/lessons/25_RKNPU2—通用C API.html)
- [Markdown：docs/28_mobilenet模型代码封装.md](../docs/28_mobilenet模型代码封装.md) · [HTML 连续滚动课件](../courseware/lessons/28_mobilenet模型代码封装.html)

## 源码清单
- [`examples/hardware/rknn_classify.cpp`](../examples/hardware/rknn_classify.cpp)
- [`examples/hardware/rknn_compare_input_io.cpp`](../examples/hardware/rknn_compare_input_io.cpp)
- [`examples/hardware/compare_outputs.py`](../examples/hardware/compare_outputs.py)

## 环境和输入
准备与 Rockchip 官方 release 匹配的 SDK、对应目标板与真实模型，固定输入图像、转换参数、模型 SHA256 和板端 Runtime 版本。不要将构建示例中的 SDK 路径作为实际存在的默认路径。

## 实验命令
```bash
cmake -S examples/hardware -B build/native-rknn -DRKNN_INCLUDE_DIR=/actual/rknn/include -DRKNN_LIB=/actual/arm64/librknnrt.so
```

板端编译与执行必须结合 [ROCK 5B 手册](../boards/radxa-rock5b/README.md) 和 [C++ RGA 输入对照](../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md)。构建前替换 SDK include/lib 为实际 ARM64 文件；保留 stdout、stderr、输入图、模型哈希及错误日志。

## 最短 C++ 实操顺序

先用第 24/27 讲的同一张图片和同一个 RKNN 模型跑通 Python Lite2，记录输入协议和 Top-K；再在 ROCK 5B 用匹配的 RKNPU2 ARM64 头文件、`librknnrt.so` 完成 CMake 构建。

```bash
cmake -S examples/hardware -B build/native-rknn \
  -DRKNN_INCLUDE_DIR=/actual/rknn/include \
  -DRKNN_LIB=/actual/arm64/librknnrt.so
cmake --build build/native-rknn -j2
```

用 `cmake --build` 输出确认生成的分类程序路径，按 [板端 C++ 教程](../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md) 提供的参数运行。理解 `rknn_init`→输入张量属性查询→`rknn_inputs_set`→`rknn_run`→`rknn_outputs_get/release`→`rknn_destroy`。比较相同输入的 Python/C++ 结果，输出 dtype/shape、预处理协议或类别不一致则先排查，不做虚构性能对比。

## 图片变成真正的 C++ 输入张量

在已构建好 rknn_classifier 的 ROCK 5B 上，模型必须明确接受 RGB uint8 NHWC 224×224（归一化在 RKNN 转换时配置）；本示例采用 stretch resize：

~~~bash
python3 examples/hardware/prepare_image.py --image /path/to/test.jpg --output build/classify_input.npy --raw build/classify_input.raw --width 224 --height 224 --color RGB --layout NHWC --dtype uint8
./build/native-rknn/rknn_classifier /path/to/mobilenet_compatible.rknn build/classify_input.raw
~~~

C++ 输入不是 JPG，而是紧密排列的张量 bytes。首先看查询输出的输入 size/dtype/layout，再看 output index/score；用同图运行 Python Lite2 分类对照 Top-K。标签应来自该模型的类别列表，程序不会自行猜测标签。RAW 字节数不匹配时先核对模型输入协议。

## 自动化测试

- [原生 C++ 分类/内存绑定假 SDK 行为测试](../examples/hardware/tests/test_native_classification.py)：编译真实 C++ 主程序，在显式 FAKE SDK 上运行成功和错误输入路径；不代表实机 NPU

- [新增专项行为测试](../tools/tests/test_engineering_image_io.py)
- [`tools/tests/test_resource_tools.py`](../tools/tests/test_resource_tools.py)

上列测试为现有交叉参考入口，**不能据此断言该 C++ 工程已有专属功能测试**。必须补实际硬件测试，涉及代码行为的离线单元测试应逐步新增。

## 验收标准
板端同模型同图对比标准输入与 I/O 绑定输出，记录 SDK、模型 SHA256、分类/张量误差和 p95 延迟。将对照值、测试样本和期望结果存储在本地 results 目录，区分成功、失败和未测试状态。

## 验证边界
现有通用资源测试并不是 C++ RKNPU2 功能测试；必须另做板端编译、推理与结果回归。**硬件验收状态：待实际 ROCK 5B 日志**。模拟/编译/CLI 成功不是板端验收。
