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

新增 [独立 C++ 源码](../hardware/rknn_zero_copy.cpp)，代码实际调用 `rknn_create_mem`、`rknn_set_io_mem`、`rknn_run` 与 `rknn_destroy_mem`。用真实 SDK 头文件和动态库编译，支持单输入单输出 uint8 NHWC 分类模型。请先在板端通过 `rknn_query` 核实输入原生 stride 与 size，再构造包含填充的数据文件。

```bash
python3 examples/lesson_26.py --model model.rknn --input-raw padded_input.raw \
  --execute --include /sdk/include --library /sdk/lib/librknnrt.so --runs 20
```

SDK 可能要求额外的 cache sync、native stride 对齐或专用图像预处理；当前仓库**尚未拿真实 RK3588 与匹配模型跑过这一实现**。编译/运行失败时需要保存返回码、tensor query、driver/runtime 版本。不能以源码存在就宣称零拷贝性能提高。源码运行时间仅覆盖 `rknn_run`，不包含调用前的数据拷贝。
