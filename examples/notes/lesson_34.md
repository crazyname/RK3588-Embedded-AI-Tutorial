# 实例 34：RKLLM 原生 C API 推理与外部 Demo 记录

[对应课程教材](../../docs/32_Deepseek_Qwen%E5%A4%A7%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md) 负责 RKLLM 原理和内存预算；这里仅记录源码、运行方法、产物和故障排查。

## 推荐：本仓库原生 C++

- [RKLLM C++ 源码](../hardware/rkllm/rkllm_stream.cpp) 直接调用官方 `rkllm_init / rkllm_run / rkllm_destroy`。
- [独立 CMake](../hardware/rkllm/CMakeLists.txt) 在 ARM64 板端编译。
- [完整 ROCK 5B 上板流程](../../boards/radxa-rock5b/RKLLM_NATIVE.md)：真实模型准备、SDK release 对应、CMake 编译、JSON 指标、结果隐私。

从仓库根目录，在具备匹配 SDK 的板卡：

    cmake -S examples/hardware/rkllm -B build/rkllm-native \
      -DRKLLM_INCLUDE_DIR=/sdk/rkllm/include \
      -DRKLLM_LIB=/sdk/rkllm/aarch64/librkllmrt.so
    cmake --build build/rkllm-native -j
    ./build/rkllm-native/rkllm_stream --model /data/models/model.rkllm \
      --prompt-file boards/radxa-rock5b/results/prompt.txt \
      --report boards/radxa-rock5b/results/rkllm_run.json

这些 SDK/模型路径是示例占位值，不是自动下载的真实文件。只有匹配 Runtime、模型与平台才能成功运行。

## 旧版外部 Demo 启动器

旧的 [lesson_34.py](../lesson_34.py) 仍可用于**确实采用它所假设的标准输入协议**的官方演示程序：

    python3 examples/lesson_34.py --program /path/to/compatible/demo \
      --model /path/to/model.rkllm --prompt 你好

但官方 Demo CLI 在不同 release 间存在差异，需按它自己的 `--help`/源代码确认是否使用标准输入；旧包装器只能记录 stdout/stderr 与墙钟，**不能**凭借输出文字推出 token/s。

## 测试与验收边界

GitHub Actions 使用官方头文件和独立 Fake Runtime 测编译、回调、指标和失败路径；有真实设备和模型时再比较 SDK tokens/s、首次文本延迟、温度、长时间运行和系统内存。Fake 回调字符串不是真正的模型预测。
