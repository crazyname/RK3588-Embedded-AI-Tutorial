# 官方模型和数据资源索引

本目录登记来源与校验信息，不打包预训练权重或数据集。官方项目网页不等于二进制直链。需要按照具体 SDK 版本获取官方模型、labels 和后处理，并审核各自许可证。

## 用本仓库生成可运行的 ONNX 实验模型

    python3 examples/hardware/create_tiny_onnx.py --onnx build/fixtures/tiny.onnx --input-npy build/fixtures/input.npy
    python3 examples/hardware/onnx_reference.py --onnx build/fixtures/tiny.onnx --input-npy build/fixtures/input.npy --output build/fixtures/out.npz
    python3 tools/verify_assets.py --id tiny-conv-onnx --strict

该 Tiny CNN 是工具链验证模型，不是预训练分类模型。

## 模型、数据与版权

见 [manifest.json](manifest.json)：记录 Model Zoo、RKLLM 等官方项目主页。实验者应为真实本地模型填写 source release、输入协议、SHA256 与权重许可证，保持同版本转换器和后处理。没有实物设备时不把 RKNN 兼容性视为已确认。

本地权重放到被忽略的 downloads/、build/ 或 data/，避免意外提交大文件。用于模型评估的测试集不能参与训练和 INT8 校准。
