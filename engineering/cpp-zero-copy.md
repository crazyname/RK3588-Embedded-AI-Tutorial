# RKNPU2 C++ 张量绑定与零拷贝边界：独立工程实验与验收

## 源码清单
- [`examples/hardware/rknn_zero_copy.cpp`](../examples/hardware/rknn_zero_copy.cpp)

## 环境和输入
准备与 Rockchip 官方 release 匹配的 SDK、对应目标板与真实模型，固定输入图像、转换参数、模型 SHA256 和板端 Runtime 版本。不要将构建示例中的 SDK 路径作为实际存在的默认路径。

## 实验命令
```bash
cmake -S examples/hardware -B build/native-rknn -DRKNN_INCLUDE_DIR=/actual/rknn/include -DRKNN_LIB=/actual/arm64/librknnrt.so
```

板端编译与执行必须结合 [ROCK 5B 手册](../boards/radxa-rock5b/README.md) 和 [C++ RGA 输入对照](../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md)。构建前替换 SDK include/lib 为实际 ARM64 文件；保留 stdout、stderr、输入图、模型哈希及错误日志。

## 自动化测试
- [`boards/radxa-rock5b/tests/test_board_tools.py`](../boards/radxa-rock5b/tests/test_board_tools.py)

上列测试为现有交叉参考入口，**不能据此断言该 C++ 工程已有专属功能测试**。必须补实际硬件测试，涉及代码行为的离线单元测试应逐步新增。

## 验收标准
检查输入输出 tensor attr、stride、memory 绑定、缓存同步及推理结果；比较标准 API 与绑定 API 的正确性和真实延迟。将对照值、测试样本和期望结果存储在本地 results 目录，区分成功、失败和未测试状态。

## 验证边界
现有测试仅具间接环境覆盖，尚无专属端到端硬件回归；SDK buffer 内的 memcpy 不等于摄像头全链路零拷贝。**硬件验收状态：待实际 ROCK 5B 日志**。模拟/编译/CLI 成功不是板端验收。
