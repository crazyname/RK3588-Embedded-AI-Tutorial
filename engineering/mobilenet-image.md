# 实验 B｜ROCK 5B MobileNet 图片分类（RKNNLite）

目标：读取一张真实图片，在板端运行兼容 MobileNet RKNN 模型，输出 Top-5 索引、分数和标签。没有模型文件时先学预处理，不假装 NPU 输出。

## 对应课程讲义与 HTML 课件

- [第24讲 RKNNLite 教材](../docs/24_RKNN-ToolkitLite2基本使用.md) · [HTML](../courseware/lessons/24_RKNN-ToolkitLite2基本使用.html)
- [第27讲 MobileNet 教材](../docs/27_mobilenet模型部署.md) · [HTML](../courseware/lessons/27_mobilenet模型部署.html)

## 源码清单

- [mobilenet_image_lite.py](../boards/radxa-rock5b/apps/mobilenet_image_lite.py)
- [板端准备与模型说明](../boards/radxa-rock5b/CAMERA_MOBILENET.md)

## 环境与输入

原版 ROCK 5B、适配系统/驱动/Runtime、ARM64 RKNN-Toolkit-Lite2、NumPy/Pillow、真实图片、匹配模型及可选标签列表。此入口限定 RGB uint8 HWC/NHWC、224×224 输入，且模型已经处理对应 mean/std。标签数须与输出类别数相符。

## 实验命令

~~~bash
python3 -c "from rknnlite.api import RKNNLite; print('Lite2 import OK')"
python3 boards/radxa-rock5b/apps/mobilenet_image_lite.py --model /path/to/mobilenet.rknn --image /path/to/test.jpg --labels /path/to/labels.txt --width 224 --height 224 --topk 5 --runs 1 --warmup 0 --confirm-rgb-uint8-nhwc
~~~

第二条只能在确认模型真实输入协议后使用；标签文件不是必须的，没有对应标签时省略 --labels，程序仍返回类别 index。读取图片后使用 RGB 和 stretch resize，输入 shape 为 (224,224,3)；Lite2 调用 load_rknn → init_runtime → inference → release。

## 自动化测试

- [板端工具离线检查](../boards/radxa-rock5b/tests/test_board_tools.py)

该测试只检查相关脚本接口，不能替代本实验的真实推理。

## 验收标准

保存一张合法输入图片的实测 JSON；能解释每个 Top-5 class_index/model_score，且与模型实际标签映射一致。若标签数不等，先排查标签文件，不能通过硬改索引掩盖问题。

## 验证边界

没有真实 ROCK 5B 日志之前，状态为待上板。模型原始分数不一定是 softmax 概率，不能直接把 score 解读为置信概率。

