# 实例 26：零拷贝输入的布局预检

理论与技术背景：[RKNPU2—零拷贝C API](../../docs/26_RKNPU2%E2%80%94%E9%9B%B6%E6%8B%B7%E8%B4%9DC%20API.md)。本页不复写原理，只包含**依赖、启动、产物、验收**。

## 环境

实际 RKNN 模型、raw tensor，以及 SDK 查询得到的 native size_with_stride。

## 执行

```bash
python3 examples/lesson_26.py --model m.rknn --input-raw x.raw --native-input-bytes 150528
```

完整参数运行 `python3 examples/lesson_26.py --help` 查看，命令里的文件名必须换成实际路径。

## 验收与限制

检查实际 buffer 字节大小和校验和；不将其冒充零拷贝加速工程。无实际板卡或 SDK 时，不能输出假定的硬件结论。

## 错误处理

首先检查依赖安装、系统架构、模型/输入格式与命令返回码。缺失模型或不符合 tensor 大小时程序会失败，而非产生虚假样本。

## 零拷贝实际 NPU 推理（需 RK3588 开发板）

另见 [C++ 输入内存绑定源码](../hardware/rknn_zero_copy.cpp)，代码实际调用 `rknn_create_mem`、`rknn_set_io_mem`、`rknn_run` 与 `rknn_destroy_mem`。用真实 SDK 头文件和动态库编译，支持单输入单输出 uint8 NHWC 分类模型。请先在板端通过 `rknn_query` 核实输入原生 stride 与 size，再构造包含填充的数据文件。

```bash
python3 examples/lesson_26.py --model model.rknn --input-raw padded_input.raw \
  --execute --include /sdk/include --library /sdk/lib/librknnrt.so --runs 20
```

SDK 可能要求额外的 cache sync、native stride 对齐或专用图像预处理；当前仓库**尚未拿真实 RK3588 与匹配模型跑过这一实现**。编译/运行失败时需要保存返回码、tensor query、driver/runtime 版本。不能以源码存在就宣称零拷贝性能提高。源码运行时间仅覆盖 `rknn_run`，不包含调用前的数据拷贝。

## 进阶：绑定输入与 RGA 缩放验收

- [C++ 常规输入 vs SDK 内存绑定](../hardware/rknn_compare_input_io.cpp)
- [librga RGB888 缩放及黑边](../hardware/rga_letterbox_rgb888.cpp)
- [OpenCV 同图像素差异校验](../../tools/compare_rga_letterbox.py)
- [ROCK 5B 原生编译与验收指南](../../boards/radxa-rock5b/CPP_RGA_IO_BENCHMARK.md)

**严格区分**：SDK 输入绑定依然使用 CPU memcpy，librga 虚拟地址导入和黑边合成也仍有 CPU 内存操作。现有代码不是 V4L2 摄像头 DMA-BUF → RGA → NPU 的端到端零拷贝；只在板端 SDK/驱动匹配后才能评估性能。
