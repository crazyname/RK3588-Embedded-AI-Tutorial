# RK3588 嵌入式 AI HTML 教学规划

课程目标：从 RK3588 体系结构出发，掌握 RKNN 环境、模型转换、精度/性能/内存分析、C/C++ API、YOLO 项目及 RKLLM 大模型的板端部署。

## 授课方法

课堂按场景导入（10%）、理论与架构（30%）、教师示范及学员实践（40%）、错误诊断与互动问答（10%）、学习验收与作业（10%）安排。理论课可用结构图推演代替真实上机。

## 课程表

| 序号 | 模块 | 主题 | 建议时长 |
|---|---|---|---:|
| 01 | 基础认知 | [导学](lessons/00_%E5%AF%BC%E5%AD%A6.html) | 45 分钟 |
| 02 | 基础认知 | [快速了解rk3588](lessons/01_%E5%BF%AB%E9%80%9F%E4%BA%86%E8%A7%A3rk3588.html) | 60 分钟 |
| 03 | 基础认知 | [NPU原理及对比](lessons/02_NPU%E5%8E%9F%E7%90%86%E5%8F%8A%E5%AF%B9%E6%AF%94.html) | 60 分钟 |
| 04 | 基础认知 | [RKNPU推理软件架构与模型部署流程](lessons/03_RKNPU%E6%8E%A8%E7%90%86%E8%BD%AF%E4%BB%B6%E6%9E%B6%E6%9E%84%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E6%B5%81%E7%A8%8B.html) | 60 分钟 |
| 05 | 基础认知 | [瑞芯微github仓库介绍](lessons/04_%E7%91%9E%E8%8A%AF%E5%BE%AEgithub%E4%BB%93%E5%BA%93%E4%BB%8B%E7%BB%8D.html) | 60 分钟 |
| 06 | 环境与入门 | [搭建rknn · toolkit2开发环境](lessons/05_%E6%90%AD%E5%BB%BArknn_toolkit2%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83.html) | 90 分钟 |
| 07 | 环境与入门 | [设备端npu环境搭建与npu驱动更新](lessons/06_%E8%AE%BE%E5%A4%87%E7%AB%AFnpu%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8Enpu%E9%A9%B1%E5%8A%A8%E6%9B%B4%E6%96%B0.html) | 90 分钟 |
| 08 | 环境与入门 | [查看和调整CPU · NPU · DDR频率](lessons/07_%E6%9F%A5%E7%9C%8B%E5%92%8C%E8%B0%83%E6%95%B4CPU_NPU_DDR%E9%A2%91%E7%8E%87.html) | 90 分钟 |
| 09 | 环境与入门 | [快速体验rknn · demo](lessons/08_%E5%BF%AB%E9%80%9F%E4%BD%93%E9%AA%8Crknn_demo.html) | 90 分钟 |
| 10 | 模型转换与优化 | [rknn模型转换](lessons/09_rknn%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2.html) | 90 分钟 |
| 11 | 模型转换与优化 | [均值和标准差](lessons/10_%E5%9D%87%E5%80%BC%E5%92%8C%E6%A0%87%E5%87%86%E5%B7%AE.html) | 90 分钟 |
| 12 | 模型转换与优化 | [模型转换工具rknn · convert](lessons/11_%E6%A8%A1%E5%9E%8B%E8%BD%AC%E6%8D%A2%E5%B7%A5%E5%85%B7rknn_convert.html) | 90 分钟 |
| 13 | 模型转换与优化 | [Netron的基本使用](lessons/12_Netron%E7%9A%84%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.html) | 90 分钟 |
| 14 | 模型转换与优化 | [rknn-toolkit2模型推理](lessons/13_rknn-toolkit2%E6%A8%A1%E5%9E%8B%E6%8E%A8%E7%90%86.html) | 90 分钟 |
| 15 | 模型转换与优化 | [模型量化精度分析](lessons/14_%E6%A8%A1%E5%9E%8B%E9%87%8F%E5%8C%96%E7%B2%BE%E5%BA%A6%E5%88%86%E6%9E%90.html) | 90 分钟 |
| 16 | 模型转换与优化 | [模型性能评估](lessons/15_%E6%A8%A1%E5%9E%8B%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.html) | 90 分钟 |
| 17 | 模型转换与优化 | [模型内存评估](lessons/16_%E6%A8%A1%E5%9E%8B%E5%86%85%E5%AD%98%E8%AF%84%E4%BC%B0.html) | 90 分钟 |
| 18 | 模型转换与优化 | [模型剪枝](lessons/17_%E6%A8%A1%E5%9E%8B%E5%89%AA%E6%9E%9D.html) | 75 分钟 |
| 19 | 模型转换与优化 | [模型加密](lessons/18_%E6%A8%A1%E5%9E%8B%E5%8A%A0%E5%AF%86.html) | 75 分钟 |
| 20 | 高级 API | [多Batch处理](lessons/19_%E5%A4%9ABatch%E5%A4%84%E7%90%86.html) | 75 分钟 |
| 21 | 高级 API | [多输入模型](lessons/20_%E5%A4%9A%E8%BE%93%E5%85%A5%E6%A8%A1%E5%9E%8B.html) | 75 分钟 |
| 22 | 高级 API | [动态shape输入](lessons/21_%E5%8A%A8%E6%80%81shape%E8%BE%93%E5%85%A5.html) | 75 分钟 |
| 23 | 高级 API | [ONNX模型编辑](lessons/22_ONNX%E6%A8%A1%E5%9E%8B%E7%BC%96%E8%BE%91.html) | 75 分钟 |
| 24 | 高级 API | [自动生成部署C代码](lessons/23_%E8%87%AA%E5%8A%A8%E7%94%9F%E6%88%90%E9%83%A8%E7%BD%B2C%E4%BB%A3%E7%A0%81.html) | 75 分钟 |
| 25 | 高级 API | [RKNN-ToolkitLite2基本使用](lessons/24_RKNN-ToolkitLite2%E5%9F%BA%E6%9C%AC%E4%BD%BF%E7%94%A8.html) | 120 分钟 |
| 26 | 高级 API | [RKNPU2—通用C API](lessons/25_RKNPU2%E2%80%94%E9%80%9A%E7%94%A8C%20API.html) | 120 分钟 |
| 27 | 高级 API | [RKNPU2—零拷贝C API](lessons/26_RKNPU2%E2%80%94%E9%9B%B6%E6%8B%B7%E8%B4%9DC%20API.html) | 120 分钟 |
| 28 | 项目实战 | [mobilenet模型部署](lessons/27_mobilenet%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.html) | 120 分钟 |
| 29 | 项目实战 | [mobilenet模型代码封装](lessons/28_mobilenet%E6%A8%A1%E5%9E%8B%E4%BB%A3%E7%A0%81%E5%B0%81%E8%A3%85.html) | 120 分钟 |
| 30 | 项目实战 | [yolov5模型部署实战](lessons/29_yolov5%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%E5%AE%9E%E6%88%98.html) | 120 分钟 |
| 31 | 项目实战 | [yolov26模型部署(从0到1版) · windows环境搭建与模型预测分析](lessons/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_windows%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E9%A2%84%E6%B5%8B%E5%88%86%E6%9E%90.html) | 120 分钟 |
| 32 | 项目实战 | [yolov26模型部署(从0到1版) · 数据集构建与模型训练](lessons/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E6%95%B0%E6%8D%AE%E9%9B%86%E6%9E%84%E5%BB%BA%E4%B8%8E%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83.html) | 120 分钟 |
| 33 | 项目实战 | [yolov26模型部署(从0到1版) · 导出onnx与rknn模型并板端推理](lessons/30_yolov26%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BB%8E0%E5%88%B01%E7%89%88%29_%E5%AF%BC%E5%87%BAonnx%E4%B8%8Erknn%E6%A8%A1%E5%9E%8B%E5%B9%B6%E6%9D%BF%E7%AB%AF%E6%8E%A8%E7%90%86.html) | 120 分钟 |
| 34 | 项目实战 | [yolov8模型部署(优化加速版)](lessons/31_yolov8%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2%28%E4%BC%98%E5%8C%96%E5%8A%A0%E9%80%9F%E7%89%88%29.html) | 120 分钟 |
| 35 | 项目实战 | [Deepseek · Qwen大模型部署](lessons/32_Deepseek_Qwen%E5%A4%A7%E6%A8%A1%E5%9E%8B%E9%83%A8%E7%BD%B2.html) | 90 分钟 |

总建议时长为 3180 分钟（约 53.0 小时），未计入课后独立实验和大型模型训练时间。

## 考核方式

- 概念理解 20%：CPU/NPU/模型格式/软件架构。
- 环境可复现 25%：版本、配置、日志和真实输出。
- 精度与性能 25%：转换、量化、时延、内存记录。
- 工程实践 20%：C/C++、资源管理、检测后处理。
- 综合报告 10%：对照实验、问题复盘和演示。

## 教学环境

需要 RK3588 开发板（具备配套固件）、供电与散热、串口或网络连接、x86_64 Linux 主机、对应版本 Python/Conda 与 C/C++ SDK。Windows 模型训练课程需额外准备训练主机环境。

课件内容源于本仓库 Markdown 讲义与原始视频口播，部分演示设计和课堂测验为教学性补充。仓库未包含视频中的全部源码、模型和数据集；所有操作应核对当前 SDK 与硬件说明，尤其是刷写固件及定频。
