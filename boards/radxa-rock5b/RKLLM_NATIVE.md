# 第34讲进阶：RK3588 / ROCK 5B 原生 RKLLM C API 推理和性能测量

这不是在 Python 里简单调用官方可执行程序。项目自己使用 `rkllm.h` 的 `rkllm_createDefaultParam`、`rkllm_init`、`rkllm_run`、回调和 `rkllm_destroy` 完成**单次真实语言模型生成**。但必须在有实际 ARM64 RKLLM Runtime 和匹配 `.rkllm` 的板端运行；仓库 CI 的 Fake Runtime 只验证调用与指标逻辑。

## 官方依据与兼容边界

- [官方 RKLLM Runtime C API 头文件](https://github.com/airockchip/rknn-llm/blob/main/rkllm-runtime/Linux/librkllm_api/include/rkllm.h)
- [官方 rkllm_api_demo](https://github.com/airockchip/rknn-llm/tree/main/examples/rkllm_api_demo)：RKLLMParam、RKLLMCallback、RKLLM_RUN_NORMAL/FINISH/ERROR、RKLLMResult.perf。
- [官方示例编译路径](https://github.com/airockchip/rknn-llm/blob/main/examples/rkllm_api_demo/deploy/CMakeLists.txt)。

一定要同时记录官方 SDK commit / release、板端 `librkllmrt.so`、模型来源与 SHA256、RK3588 BSP 和 CPU 架构；模型必须来自具备合法使用许可的来源。本仓库**不**附带第三方 `.rkllm`，也不会自动刷机或修改 CPU/NPU 频率。

## 源码结构

- [原生 C++ 代码](../../examples/hardware/rkllm/rkllm_stream.cpp) - 一个模型、一个提示词、一次同步推理；结果从真正的 SDK callback 接收。
- [独立 CMake 工程](../../examples/hardware/rkllm/CMakeLists.txt) - 需要 ARM64 SDK 的头文件和共享库。
- [离线 Fake SDK 源码](../../examples/hardware/rkllm/tests/mock_rkllm_runtime.cpp) - 仅作 CI 测试，不属于真实推理。
- [回归测试](../../examples/hardware/rkllm/tests/test_native_stream.py) - 校验回调、性能值、没有 SDK 指标时输出 null、错误返回码及敏感文本默认不落盘。

## 设备端编译

确认真实 RKLLM 的匹配版本后，在 ROCK 5B 或正确配置的 ARM64 交叉编译主机上：

    cmake -S examples/hardware/rkllm -B build/rkllm-native \
      -DRKLLM_INCLUDE_DIR=/sdk/rkllm/include \
      -DRKLLM_LIB=/sdk/rkllm/aarch64/librkllmrt.so
    cmake --build build/rkllm-native -j

必须把 `/sdk/...` 换成真实存在的官方 SDK 文件。不要把 CI 用的 `mock_rkllm_runtime.cpp` 链接到真实板卡程序。CMake 使用单独的模型工程，不影响现有 RKNPU2 分类器构建。

## 模型和提示词

请准备真实的 `.rkllm` 模型（小模型优先）、对应匹配的 runtime，并记录哈希：

    sha256sum /data/models/model.rkllm

为避免命令行参数泄露提示词，先在本地创建一个不提交 Git 的文件：

    mkdir -p boards/radxa-rock5b/results
    printf '请用三句话解释 RK3588 的 NPU 与 CPU 区别。\n' > boards/radxa-rock5b/results/prompt.txt

默认生成输出写 stdout，JSON **不包含提示词原文或生成文本**：

    ./build/rkllm-native/rkllm_stream \
      --model /data/models/model.rkllm \
      --prompt-file boards/radxa-rock5b/results/prompt.txt \
      --context 2048 --max-new 128 \
      --report boards/radxa-rock5b/results/rkllm_run.json

只有你明确决定允许保存输出内容时才加 `--save-text`；生成文本可能包含输入中的个人信息。建议只在本地查看，不公开上传提示词和响应。

## 报告到底能证明什么？

| 字段 | 计量边界 |
|---|---|
| initialized_ms | `rkllm_init` 的墙钟耗时，不是 NPU prefill latency |
| run_wall_ms | 整次同步 `rkllm_run` 墙钟耗时，不含模型初始化 |
| first_text_chunk_ms | 到第一次非空文本回调的时间；**不一定等于真正首 token 延迟 TTFT** |
| text_chunks | 回调分片数量，绝不当作 token 数 |
| sdk_generate_tokens / sdk_generate_time_ms | 仅当官方 Runtime `RKLLMResult.perf` 提供有效值时记录 |
| sdk_tokens_per_sec | `generate_tokens / generate_time_ms * 1000`；两个数任意一项缺失便是 null |
| sdk_peak_memory_mb | 来自 SDK perf 内存字段，不是通用 `ps RSS` 全程测量 |

正式性能对照还需要重复运行、记录热节流、温度、电源、GPU/NPU 负载、模型量化参数与上下文。代码没有接入 token callback 的**真实 token ID 逐条时序**时，不可根据文本 chunk 推断 TTFT；可通过精确 SDK release 的性能字段或进一步 instrumentation 实现严格测量。

## 验收状态

CI 对照公开的官方 RKLLM 头文件做语法编译，并链接**明确命名为 Fake 的 SDK**来测试 API 结构、回调事件、空性能数据和错误分支；这是自动化质量证据，**不是 RK3588 实机通过**。真实板端部署后还需填写 release、模型 SHA256、初始空闲内存、生成输出、运行日志、重复次数和温度。
