# 实验 F｜RKLLM C++ 流式文本生成

目标：在 ROCK 5B 运行与当前 SDK 匹配的 .rkllm 小模型，从 C++ 回调获取文字并正确判断生成结束。

## 对应课程讲义与 HTML 课件

- [第32讲大模型部署](../docs/32_Deepseek_Qwen大模型部署.md) · [HTML](../courseware/lessons/32_Deepseek_Qwen大模型部署.html)

## 源码清单

- [C++ 原生 RKLLM 调用](../examples/hardware/rkllm/rkllm_stream.cpp)
- [完整 RKLLM 运行指南](../boards/radxa-rock5b/RKLLM_NATIVE.md)

## 环境与输入

需要真实 ROCK 5B、匹配的 librkllmrt.so/头文件、兼容的 .rkllm 模型及一个本地 UTF-8 提示词文件。模型转换由对应 RKLLM Toolkit 完成；仓库没有内置真实模型，也不能替代模型许可审核。

## 实验命令

~~~bash
cmake -S examples/hardware/rkllm -B build/rkllm-native -DRKLLM_INCLUDE_DIR=/actual/rkllm/include -DRKLLM_LIB=/actual/arm64/librkllmrt.so
cmake --build build/rkllm-native -j2
printf '请简单解释 RK3588 的 NPU 是什么。\n' > /tmp/rkllm_prompt.txt
./build/rkllm-native/rkllm_stream --model /path/to/model.rkllm --prompt-file /tmp/rkllm_prompt.txt --context 2048 --max-new 128 --report /tmp/rkllm_run.json
~~~

关键流程：rkllm_createDefaultParam → rkllm_init → rkllm_run(同步) → callback 按块输出文字 → RKLLM_RUN_FINISH → rkllm_destroy。模型路径和参数必须替换为真实值。报告默认不保存提示词或生成文本内容；生成文本显示在终端。

## 自动化测试

- [明确标注为 Fake SDK 的回调测试](../examples/hardware/rkllm/tests/test_native_stream.py)

可在 PC 上执行：

~~~bash
python3 -m unittest discover -s examples/hardware/rkllm/tests -p test_native_stream.py -v
~~~

## 验收标准

真实板端能够生成可读文本且收到完成回调，退出码为零；记录模型/运行库版本、输入提示词和实际输出。文本 chunk 数不能直接视为 token 数，首个文本块时间也不必然等于准确 TTFT。

## 验证边界

Fake SDK 验证的是回调与资源处理，不是 RK3588 上模型生成。没有实机日志前保持待验证状态。

