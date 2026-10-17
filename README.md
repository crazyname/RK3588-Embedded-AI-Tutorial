# RK3588 嵌入式 AI 教程

本仓库是一套围绕 **Rockchip RK3588 / RKNPU** 的中文嵌入式 AI 教学资料，从基础理论、RKNN 工具链到目标检测部署与边缘大模型实践。

## 学习路线与完成范围

- [课程完工清单（P0/P1/P2、六条实验链路与板端验收）](COURSE_COMPLETION_CHECKLIST.md)
- 建议路径：先读 [环境准备](SETUP.md) → [ONNX 工具链](engineering/onnx-toolchain.md) → [Python 图片分类](engineering/mobilenet-image.md) → [C++ 分类](engineering/cpp-rknn-classify.md) → [YOLOv8 摄像头](engineering/yolov8-camera.md) → [RKLLM 文本生成](engineering/rkllm-native.md)。RGA 视频链路作为检测后的进阶实验。
- 当前课程文件为 **00–32 共 35 份**（30 讲拆分为三份）；`examples/lesson_00.py` 至 `lesson_34.py` 是源码顺序编号。不要将“第 34 个源码入口”误当“第 34 讲”。
- GitHub CI 的 PC 检查不代表 ROCK 5B 已上板验收；详见完工清单的证据标准。

## 零基础复现实验：环境、模型和质量检查

- [Windows / Ubuntu 环境准备与安全安装](SETUP.md)
- [模型资源清单与 SHA256 校验](models/README.md)
- [RKNN SDK、内核和板端 Runtime 版本记录](requirements/COMPATIBILITY.md)
- [课程 HTML/MD 链接完整性校验](tools/validate_repo.py)
- [在线发布课件（需手动启用 GitHub Pages）](courseware/DEPLOY.md)
- [源码与课程许可审核](LICENSE_POLICY.md)

PC 可先生成仓库自带的真实 ONNX Tiny CNN 并运行 ONNX Runtime。RKNPU 和 RKLLM 仍需要匹配的开发板、SDK 与模型。

## 课程与源码工程同步总览（17 项工程）

- [连续滚动的 17 项工程 HTML 实验索引](engineering/index.html)
- [工程映射清单：源码、专门实验 MD、测试与验收入口](engineering/manifest.json)
- [工程源码与实验文档映射检查](tools/audit_engineering.py)

在仓库根目录执行 `python3 tools/audit_engineering.py --strict`。GitHub Actions 同步检查映射，以免后续添加 `boards/radxa-rock5b/apps|tools` 或 `examples/hardware` 工程时忘记建立实验手册。**注意：机器审计只检查文件映射与必要章节，不检查测试是否真的运行了 NPU，也不证明已有工程完全具备行为覆盖。** 部分 C++ 示例的自动化测试使用 Fake SDK，硬件正确性仍应依据真实板端结果验收。

## ROCK 5B 16GB：官方手册驱动的板级实战

以 **Radxa ROCK 5B（原版，非 5B+）16GB** 作为参考目标板，并依据 Radxa 官方中文文档、系统镜像、电源要求、RKNN 安装和 YOLOv8/MobileNet 部署教程编写了板级实践。

- [ROCK 5B 硬件清单和完整入口](boards/radxa-rock5b/README.md)
- [官方手册对照索引](boards/radxa-rock5b/MANUAL_MAP.md)
- [从 SD 启动到首次真实 NPU 结果的步骤](boards/radxa-rock5b/FIRST_BOOT.md)
- [只读设备审计与 USB 摄像头检查](boards/radxa-rock5b/tools/)
- [ROCK 5B MobileNet 图片分类源码](boards/radxa-rock5b/apps/mobilenet_image_lite.py)
- [下一阶段硬件专题项目与验收条件](boards/radxa-rock5b/NEXT_PROJECTS.md)

**明确边界：** 这些脚本已按官方手册具体化，但仍需实际开发板运行并保存真实日志。不要把 GitHub CI 的离线测试误称为 RK3588 NPU 实机验收。

## 课程实操源码

包含 [35 个可执行 Python 课程入口](examples/)、[公共算法实现](examples/labs.py)、[自动化测试](examples/tests/) 以及 [ONNX 转换、真实模型推理与 C++ 示例](examples/hardware/)。**这些不是 35 个全部完成的板端项目**：部分课次的代码是可以在普通电脑运行的数学/系统实验，RKNN/YOLO/RKLLM 等专用硬件功能需要真实 SDK、模型和设备。

- [从零运行示例的完整指南](examples/README.md)
- [最小真实 ONNX 模型生成器](examples/hardware/create_tiny_onnx.py)
- [GitHub Actions 自动测试](.github/workflows/examples-ci.yml)

**快速体验：** 在仓库根目录运行 `python3 examples/lesson_00.py --output build/lesson00/environment.json`、`python3 examples/lesson_02.py`，再运行 `python3 -m unittest discover -s examples/tests -v`。详见代码说明中对纯 Python、ONNX Runtime 和 RK3588 板端三个执行环境的区分。

## 35 节重编自学教材

全部 HTML 与 Markdown 已按自学需求重编：原理讲解、3 个实操任务、预期检查、故障诊断、完整案例、课堂测试及官方参考。HTML 采用整篇连续滚动，MD 在末尾保留原始视频转写。实验片段并未全部在实际 RK3588 上运行验证，应按 SDK 版本核对。

- [12 周自学路线与实验日志模板](courseware/SELF_STUDY_GUIDE.md)
- [官方资料与推荐书目](courseware/REFERENCES.md)

## HTML 互动课件

已为全部 **35 节课** 制作可离线使用的 HTML 互动课件：采用单页长文、上下滚动的阅读方式，支持章节目录锚点跳转、课堂案例、知识流程、操作步骤、课堂测验、讲师提示、验收清单和上一讲/下一讲导航。

- [打开 HTML 课件总入口](courseware/index.html)
- [查看详细教学规划、建议课时与考核方案](courseware/TEACHING_PLAN.md)
- [浏览全部 HTML 课件](courseware/lessons/)

**使用方法：** 克隆或下载整个仓库，保持 `courseware/assets/` 与 `courseware/lessons/` 相对路径不变，然后使用浏览器打开 `courseware/index.html`。课件使用原生 HTML/CSS/JavaScript，不要求运行后端服务器。每一讲只需向下滚动即可阅读全部内容，不再使用逐页翻页播放器。

**注意：** GitHub 的文件查看页不等同于在线 HTML 演示。需要直接通过浏览器打开本地文件，或另行部署到静态站点托管服务。课件里的示范步骤并非全都完成真实板端验证。

## 如何学习

建议按章节顺序阅读 `docs/` 下的 Markdown 讲义。**课程共 35 份 `.md` 教学文件**，第 30 讲按三个主题分别整理。

每份讲义包括学习目标、核心知识、实验步骤、验收标准、常见问题和课后练习，并在末尾通过折叠区域保留该节视频的完整原始字幕（含时间戳）。原始字幕仅保留在 Markdown 折叠附录中，便于核对内容来源。

> **使用提示：** 源材料是视频自动转写，软件名称、命令和数字存在可能的识别误差。讲义提供了技术背景与风险提醒，35 个课程程序各有独立入口，但仓库没有内置所有第三方预训练模型、数据集或系统镜像；实际操作须以所用 SDK 版本和板卡厂商文档为准。

## 课程目录

### 第一部分：基础认知

- [第00讲 · 导学](docs/00_%E5%AF%BC%E5%AD%A6.md)
- [第01讲 · 快速了解rk3588](docs/01_%E5%BF%AB%E9%80%9F%E4%BA%86%E8%A7%A3rk3588.md)
- [第02讲 · NPU原理及对比](docs/02_NPU%E5%8E%9F%E7%90%86%E5%8F%8A%E5%AF%B9%E6%AF%94.md)
- [第03讲 · RKNPU推理软件架构与模型部署流程](docs/03_RKNPU%E6%8E%A8%E7%90%86%E8%BD%AF%E4%BB%B6%E6%9E%B6%E6%9E%84%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E6%B5%81%E7%A8%8B.md)
- [第04讲 · 瑞芯微github仓库介绍](docs/04_%E7%91%9E%E8%8A%AF%E5%BE%AEgithub%E4%BB%93%E5%BA%93%E4%BB%8B%E7%BB%8D.md)

### 第二部分：环境搭建与体验

- [第05讲 · 搭建rknn — toolkit2开发环境](docs/05_%E6%90%AD%E5%BB%BArknn_toolkit2%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83.md)
- [第06讲 · 设备端npu环境搭建与npu驱动更新](docs/06_%E8%AE%BE%E5%A4%87%E7%AB%AFnpu%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8Enpu%E9%A9%B1%E5%8A%A8%E6%9B%B4%E6%96%B0.md)
- [第07讲 · 查看和调整CPU — NPU — DDR频率](docs/07_%E6%9F%A5%E7%9C%8B%E5%92%8C%E8%B0%83%E6%95%B4CPU_NPU_DDR%E9%A2%91%E7%8E%87.md)
- [第08讲 · 快速体验rknn — demo](docs/08_%E5%BF%AB%E9%80%9F%E4%BD%93%E9%AA%8Crknn_demo.md)

### 第三部分：模型转换、精度与优化

- [第09讲 · rknn模型转换](docs/09_rknn%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2.md)
- [第10讲 · 均值和标准差](docs/10_%E5%9D%87%E5%80%BC%E5%92%8C%E6%A0%87%E5%87%86%E5%B7%AE.md)
- [第11讲 · 模型转换工具rknn — convert](docs/11_%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2%E5%B7%A5%E5%85%B7rknn_convert.md)
- [第12讲 · Netron的基本使用](docs/12_Netron%E7%9A%84%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md)
- [第13讲 · rknn-toolkit2模型推理](docs/13_rknn-toolkit2%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86.md)
- [第14讲 · 模型量化精度分析](docs/14_%E6%A8%A1%E5%9E%8B%E9%87%8F%E5%8C%96%E7%B2%BE%E5%BA%A6%E5%88%86%E6%9E%90.md)
- [第15讲 · 模型性能评估](docs/15_%E6%A8%A1%E5%9E%8B%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.md)
- [第16讲 · 模型内存评估](docs/16_%E6%A8%A1%E5%9E%8B%E5%86%85%E5%AD%98%E8%AF%84%E4%BC%B0.md)
- [第17讲 · 模型剪枝](docs/17_%E6%A8%A1%E5%9E%8B%E5%89%AA%E6%9E%9D.md)
- [第18讲 · 模型加密](docs/18_%E6%A8%A1%E5%9E%8B%E5%8A%A0%E5%AF%86.md)

### 第四部分：高级功能与 C API

- [第19讲 · 多Batch处理](docs/19_%E5%A4%9ABatch%E5%A4%84%E7%90%86.md)
- [第20讲 · 多输入模型](docs/20_%E5%A4%9A%E8%BE%93%E5%85%A5%E6%A8%A1%E5%9E%8B.md)
- [第21讲 · 动态shape输入](docs/21_%E5%8A%A8%E6%80%81shape%E8%BE%93%E5%85%A5.md)
- [第22讲 · ONNX模型编辑](docs/22_ONNX%E6%A8%A1%E5%9E%8B%E7%BC%96%E8%BE%91.md)
- [第23讲 · 自动生成部署C代码](docs/23_%E8%87%AA%E5%8A%A8%E7%94%9F%E6%88%90%E9%83%A8%E7%BD%B2C%E4%BB%A3%E7%A0%81.md)
- [第24讲 · RKNN-ToolkitLite2基本使用](docs/24_RKNN-ToolkitLite2%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.md)
- [第25讲 · RKNPU2—通用C API](docs/25_RKNPU2%E2%80%94%E9%80%9A%E7%94%A8C%20API.md)
- [第26讲 · RKNPU2—零拷贝C API](docs/26_RKNPU2%E2%80%94%E9%9B%B6%E6%8B%B7%E8%B4%9DC%20API.md)

### 第五部分：部署实战与大模型

- [第27讲 · mobilenet模型部署](docs/27_mobilenet%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md)
- [第28讲 · mobilenet模型代码封装](docs/28_mobilenet%E6%A8%A1%E5%9E%8B%E4%BB%A3%E7%A0%81%E5%B0%81%E8%A3%85.md)
- [第29讲 · yolov5模型部署实战](docs/29_yolov5%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E5%AE%9E%E6%88%98.md)
- [第30讲 · yolov26模型部署(从0到1版) — windows环境搭建与模型预测分析](docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_windows%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%A2%84%E6%B5%8B%E5%88%86%E6%9E%90.md)
- [第30讲 · yolov26模型部署(从0到1版) — 数据集构建与模型训练](docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E6%95%B0%E6%8D%AE%E9%9B%86%E6%9E%84%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83.md)
- [第30讲 · yolov26模型部署(从0到1版) — 导出onnx与rknn模型并板端推理](docs/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E5%AF%BC%E5%87%BAonnx%E4%B8%8Erknn%E6%A8%A1%E5%9E%8B%E5%B9%B6%E6%9D%BF%E7%AB%AF%E6%8E%A8%E7%90%86.md)
- [第31讲 · yolov8模型部署(优化加速版)](docs/31_yolov8%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BC%98%E5%8C%96%E5%8A%A0%E9%80%9F%E7%89%88%29.md)
- [第32讲 · Deepseek — Qwen大模型部署](docs/32_Deepseek_Qwen%E5%A4%A7%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.md)

## 推荐实验路线

1. **入门验收（00–08）**：弄清 NPU、环境、驱动与官方 demo 的基本分工。
2. **模型转换（09–18）**：从 ONNX 生成 RKNN，确保输入预处理、精度和性能验证可复现。
3. **工程部署（19–29）**：掌握批量/多输入、板端 Python、C API、零拷贝、MobileNet 和 YOLOv5。
4. **完整项目（30–32）**：执行数据标注/训练、YOLO 模型转板、优化加速及 RKLLM 体验。

## 参考资料

- [Rockchip NPU 官方工具与示例](https://github.com/airockchip)
- [Netron 模型结构可视化](https://netron.app/)
- [课程视频](https://www.bilibili.com/video/BV11DjT6uEhc)

## 课程内容与来源

- `docs/`：35 份可自学的 Markdown 教学讲义（包含原始字幕附录）。
- `courseware/`：35 份单页连续滚动的 HTML 课件。
- 讲义示例、术语与实践检查为教学性整理；API 命令、SDK 安装包及兼容性在真实项目中应再次核对。
