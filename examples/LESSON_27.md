# 第 27 讲：MobileNet 真正可执行的部署实验

课程源码：[lesson_27.py](lesson_27.py)，模型来源：[RKNN Model Zoo 官方 MobileNet 目录](https://github.com/airockchip/rknn_model_zoo/tree/main/examples/mobilenet)。

## 1. 不使用开发板，先验证真实推理

在开发机安装依赖：

```bash
python3 -m pip install numpy pillow onnx onnxruntime
```

如果还没有下载 MobileNet 权重，可以先用已有的 [create_tiny_onnx.py](hardware/create_tiny_onnx.py) 生成具有真实卷积与全局平均池化算子的测试模型：

```bash
python3 examples/hardware/create_tiny_onnx.py --onnx build/tiny.onnx --input-npy build/tiny.npy
python3 -c "from PIL import Image; Image.new('RGB', (4,4), (128,64,0)).save('build/test.png')"
printf 'red\ngreen\n' > build/labels.txt
python3 examples/lesson_27.py --backend onnx \
  --model build/tiny.onnx --image build/test.png --labels build/labels.txt \
  --width 4 --height 4 --normalize none --topk 2 --output-json build/lesson27.json
```

此测试确实调用 ONNX Runtime 运行卷积网络，但模型是教学用小网络，**不是 MobileNet，也不能代表 RK3588 NPU 推理**。

## 2. PC 上运行真正的 MobileNetV2

依照 [Model Zoo MobileNet README](https://github.com/airockchip/rknn_model_zoo/blob/main/examples/mobilenet/README.md) 获取 `mobilenetv2-12.onnx`、`bell.jpg` 和配套的 `synset.txt`。模型来源和类别顺序必须一致。

```bash
python3 examples/lesson_27.py --backend onnx \
  --model mobilenetv2-12.onnx --image bell.jpg --labels synset.txt \
  --color RGB --width 224 --height 224 --normalize imagenet \
  --topk 5 --runs 5 --output-json result_onnx.json
```

**注意：** 使用的是显式 RGB、224×224 直接缩放、float32 NCHW、ImageNet mean/std。不同模型的颜色约定、裁剪或归一化可能不同，必须优先核对导出训练协议。

## 3. RK3588 上使用 RKNNLite

先使用与你的板卡、固件和 Python 匹配的 Toolkit2/Lite2。要用正确的均值方差转换该 MobileNet 模型：官方 MobileNet 示例在 RKNN config 中使用 RGB 像素域约定的 `255*[0.485, 0.456, 0.406]` 与 `255*[0.229, 0.224, 0.225]`，而不是随意沿用 YOLO 常见的 [0,0,0]/[255,255,255]。

```bash
python3 examples/lesson_27.py --backend rknn \
  --model mobilenetv2-12.rknn --image bell.jpg --labels synset.txt \
  --width 224 --height 224 --color RGB --topk 5 \
  --runs 20 --warmup 5 --output-json result_rknn.json
```

RKNN 路径默认准备 uint8 NHWC 的输入，避免把已经写入 RKNN config 的归一化再次执行一次；如果你使用的 .rknn 模型实际输入要求不同，需要先核对转换脚本和 SDK 支持条件。本环境没有 RK3588 实物，**板端推理仍属于待上板验证**。

## 4. 验收要求

- 模型、图片和 labels 均为真实文件，版本来源可追溯。
- 推理输出维度与类别数一致，程序对标签长度不符会明确报错。
- 结果应记录 Top-K、模型路径、输入 shape/dtype 和计时边界。
- 在真正的 MobileNetV2 测试里，`bell.jpg` 的 Top-5 应与官方 README 的预期语义相符；数值允许因版本和硬件存在差异。
- 课后可尝试 `--color BGR` 的错误输入对照，但不能将错误结果冒充精度基准。

## 5. 源码范围与使用说明

原 `lesson_27.py` 只是转发 `labs.main(27)`，再对硬编码分数进行排序，**不是部署代码**。新版已经替换该入口；其他课程是否具备完整板端工程仍应独立审计，不能以 35 个 Python 文件的数量判断完成度。

## 6. 摄像头连续推理（进阶，需 ROCK 5B）

在静态图片实验验收之后，按 [USB UVC 摄像头 → RKNNLite 实验指南](../boards/radxa-rock5b/CAMERA_MOBILENET.md) 使用 [camera_mobilenet_lite.py](../boards/radxa-rock5b/apps/camera_mobilenet_lite.py) 进行连续帧推理，记录 JSON、JSONL、FPS 与 p50/p95 统计。此处无需复制教材原理，且不将模拟 SDK 单元测试误称实机性能。
