# RKLLM 原生 C API 流式生成：独立工程实验与验收

> 工程编号：`rkllm-native`。本页面向实际操作，与课程 `docs/` 中的概念讲解区分；所有设备测试须由使用者在真实 ROCK 5B 上执行。

## 对应课程讲义与 HTML 课件

- [Markdown：docs/32_Deepseek_Qwen大模型部署.md](../docs/32_Deepseek_Qwen大模型部署.md) · [HTML 连续滚动课件](../courseware/lessons/32_Deepseek_Qwen大模型部署.html)

## 源码清单

- [`examples/hardware/rkllm/rkllm_stream.cpp`](../examples/hardware/rkllm/rkllm_stream.cpp)

## 环境与准备

在仓库根目录操作。普通 PC 可检查 CLI、纯数学及假 SDK 回归；需要 RKNN、RGA 或摄像头能力的环节必须准备原版 ROCK 5B、适配系统及对应 SDK。记录模型和源文件 SHA256、系统镜像、驱动/Runtime 版本。绝不将模拟环境的通过记录为硬件验收。

## 实验命令

```bash
python3 -m unittest discover -s examples/hardware/rkllm/tests -p test_native_stream.py -v
```

正式板端调用参数和外部模型文件以源码的 `--help`、板级手册及 SDK 对应 release 为准；构建命令只能证明编译步骤，不自动证明硬件运行。留存 stdout、stderr、运行时间和版本信息，不要向公开仓库推送隐私图片或提示词。

## 上板执行路径

在 ROCK 5B 准备来自**相同 RKLLM SDK 版本**、明确支持 RK3588 的已转换模型及 `librkllmrt.so`。先读 [板端 RKLLM 完整操作指南](../boards/radxa-rock5b/RKLLM_NATIVE.md)，其中包含 C++ 构建参数和 runtime/模型匹配说明；本页不臆造编译器路径、模型文件名或不存在的发行包。

```bash
python3 -m unittest discover -s examples/hardware/rkllm/tests -p test_native_stream.py -v
grep -n 'rkllm_init\|rkllm_run\|rkllm_destroy\|callback' examples/hardware/rkllm/rkllm_stream.cpp
```

前一条只检查离线模拟回调；真实验收需运行编译出的板端程序，保留模型路径、实际提示词、首段输出、结束状态、生成文本及设备信息。回调收到的 `chunk` 不一定对应一个 token，不能据此计算 tok/s。

## C++ 板端构建与真实生成命令

安装和当前 ROCK 5B 镜像匹配的 RKLLM SDK/ARM64 运行库，准备其支持的真实 .rkllm 模型。命令来自本仓库 CMake 工程，实际 SDK 路径须替换：

~~~bash
cmake -S examples/hardware/rkllm -B build/rkllm-native -DRKLLM_INCLUDE_DIR=/actual/rkllm/include -DRKLLM_LIB=/actual/arm64/librkllmrt.so
cmake --build build/rkllm-native -j2
printf '请简单介绍 RK3588 的 CPU 和 NPU 区别。\n' > /tmp/rkllm_prompt.txt
./build/rkllm-native/rkllm_stream --model /path/to/compatible-model.rkllm --prompt-file /tmp/rkllm_prompt.txt --context 2048 --max-new 128 --report /tmp/rkllm_run.json
~~~

观察输出、退出码和 finished_callback；first_text_chunk_ms 是首次文字回调时间，不一定等于真实首 token 延迟。完整转换、SDK 匹配细节见 [板端 RKLLM 指南](../boards/radxa-rock5b/RKLLM_NATIVE.md)。

## 自动化测试

对应可审查的测试文件（某些为共用测试文件；**不保证每个子功能都已覆盖**）：

- [`examples/hardware/rkllm/tests/test_native_stream.py`](../examples/hardware/rkllm/tests/test_native_stream.py)

离线检查和 SDK/真实设备检查必须分开记录。如果对应测试只覆盖入口或相邻模块，还需要补充本工程的功能、错误输入和边界情况测试；不得写成已经实现全覆盖。

## 验收标准

真实板端必须记录模型、提示词、SDK 版本、生成文本、回调结束标志和时延指标。保存成功与失败示例、真实输入、输出及复现实验的设备信息；对涉及性能的项目至少记录实际采样次数和 p50/p95，不能根据无硬件测试推断 NPU 性能。

## 验证边界

Fake runtime 的 callback 测试不等于硬件运行；文本 chunks 非 tokens。**默认状态：源码/离线检查可用，硬件结果待上板核验**；此页面不是实测报告，也不包含伪造 FPS 或 mAP。
