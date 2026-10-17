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

## 自动化测试

- [新增专项行为测试](../tools/tests/test_engineering_image_io.py)
- [`tools/tests/test_resource_tools.py`](../tools/tests/test_resource_tools.py)

上列测试为现有交叉参考入口，**不能据此断言该 C++ 工程已有专属功能测试**。必须补实际硬件测试，涉及代码行为的离线单元测试应逐步新增。

## 验收标准
板端同模型同图对比标准输入与 I/O 绑定输出，记录 SDK、模型 SHA256、分类/张量误差和 p95 延迟。将对照值、测试样本和期望结果存储在本地 results 目录，区分成功、失败和未测试状态。

## 验证边界
现有通用资源测试并不是 C++ RKNPU2 功能测试；必须另做板端编译、推理与结果回归。**硬件验收状态：待实际 ROCK 5B 日志**。模拟/编译/CLI 成功不是板端验收。
