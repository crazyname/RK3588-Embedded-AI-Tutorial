# 第04讲｜瑞芯微github仓库介绍

> RK3588 嵌入式 AI 自学重编版：按顺序阅读原理、做实验、记录证据，再完成自测。课程内容为原创教学组织，原始视频转写保存于文末供核对。

**学前要求：** Linux 终端与 Python 基础；本节需板端操作时，先确认型号、SDK/驱动版本和数据备份。

## 学习目标

- 区分 RKNN-Toolkit2、RKNN-Toolkit-Lite2 与 RKNPU2
- 识别模型示例库的用途
- 建立官方版本与示例的检索习惯

## 为什么学本讲

undefined

## 技术原理精讲

### 找到真正维护的官方资料

历史教程常引用 rockchip-linux/rknn-toolkit2，但该仓库已说明不再维护并迁移到 airockchip/rknn-toolkit2。查阅时应从新仓库根目录、README、doc、rknn-toolkit2、rknn_toolkit_lite2、rknpu2 与 CHANGELOG 入手。下载 wheel、lib 与源码必须避免多个年份版本混搭。

**判断是否理解：** 遇到教程链接过期，先定位维护仓库和 release tag，再决定是否跟随旧教程。

### SDK、模型动物园和训练项目的区别

RKNN-Toolkit2 提供模型转换与主机调试；RKNN Model Zoo 提供 MobileNet、YOLO 等模型与具体平台转换/编译/运行示例；Ultralytics 等训练框架负责权重训练与 ONNX 导出。即使都放在 GitHub，也不是同一个功能仓库。阅读 README 首先区分平台支持列表、输入格式、构建参数和预期结果。

**判断是否理解：** 知道模型要去哪找、转换脚本去哪找、C++ 推理示例去哪找。

### 用版本固定避免‘昨天能跑’

示例工程随上游更新可能改变参数与输出张量顺序。学习报告里至少记录仓库 URL、commit/tag、模型文件校验值、运行时版本和本地修改。需要排查问题时，优先回到固定版本的最小示例，排除动态更新造成的环境漂移。

**判断是否理解：** 复现实验优先记录 commit SHA，而不是只写‘下载最新版’。

## 跟做实验与验收证据

### 实验 1：建立参考仓库清单

打开官方 Toolkit2、Model Zoo、RKLLM 和 ONNX 四个项目；分别写出其职责与使用阶段。

**预期检查：** 四个入口链接和对应的任务没有混淆。

### 实验 2：复刻一个官方案例阅读

在 rknn_model_zoo/examples/yolov5/README.md 查找 Linux build、转换脚本、预训练模型和结果预期章节。

**预期检查：** 找到具体输入和运行方式，不照搬不同目标芯片的路径。

### 实验 3：记录仓库版本

用 git clone 获取官方仓库，执行 git rev-parse HEAD、git status --short 和 git remote -v，保存到环境表。

**预期检查：** 版本、远程来源与本地修改状态可被重现。

### 实验参考片段

```bash
git clone https://github.com/airockchip/rknn-toolkit2.git
git -C rknn-toolkit2 rev-parse HEAD
git -C rknn-toolkit2 remote -v
# 示例只读取版本信息；安装步骤请跟随与本机匹配的 release。
```

> 参考片段不承诺适用于所有板卡版本；运行前先理解命令是否会写入系统及其前置条件。

## 故障诊断

### 明明照官方命令仍提示参数缺失

- 可能原因：读取的是另一版本 SDK 的 README 或示例。
- 诊断动作：记录当前 commit 并核对同一版本下的 Quick Start、changelog 与命令帮助。

### 复制了不支持 RK3588 的工程

- 可能原因：混淆 RKNPU1 旧平台与 RKNPU2 芯片支持。
- 诊断动作：先查看 Model Zoo 的 supported platform 和 cpp/rknpu2 目录。

## 自学案例分析

**情境：** 某博客说 Toolkit2 只能用于 Ubuntu 20.04，但官方新版本提供了更新的 wheel。该相信谁？

**分析路径：** 先分清发布日期和 SDK tag，再核对官方 release 包、quick start 支持矩阵与实际 wheel 文件名。旧教程有助于理解思路，却不一定是当前环境安装的正确依据。

**应交付证据：** 官方仓库 commit、wheel 文件名、系统/Python 版本匹配表。

## 课堂自测（先答后看解析）

**题目：** 板端 C++ 推理该优先查看什么？

- A. RKNPU2 示例
- B. Netron 安装包
- C. Python 主题库

<details><summary>展开答案与解释</summary>

**答案：A。** C API 的头文件、库与示例在对应板端套件里。

</details>

## 完成本讲的标准

- [ ] 能根据转换/板端 Python/板端 C 需求找到正确仓库
- [ ] 能识别不同套件的 CPU 架构和运行位置

## 课后任务

- 制作工具套件、主机平台和语言接口三列表

## 参考资料与深入阅读

- [新版 RKNN-Toolkit2](https://github.com/airockchip/rknn-toolkit2)
- [RKNN Model Zoo](https://github.com/airockchip/rknn_model_zoo)
- [Rockchip RKLLM](https://github.com/airockchip/rknn-llm)

> 资料阅读优先级：官方 SDK 版本与实例 > 数据格式的官方文档 > 理论教材。外部资料可能随版本变化，不应将本讲示例理解为已在你的开发板上实测通过。

## 源码精读：关键 API、张量与验收

第 04 讲学会定位 Rockchip 相关官方仓库、固定真实 commit/release，而不是把网上任意 SDK 文件混装。lesson_04.py 使用 git ls-remote 读取四个仓库的远端引用。

**数据路径：** `选择官方仓库` → `git ls-remote` → `commit SHA / ref` → `源码与 SDK 版本记录` → `按 release 阅读 README`。

### 1. REPOS：按项目职责选择仓库

**输入：** toolkit2、model_zoo、rknpu2、rkllm 之一。**输出：** 对应官方 Git 地址。

Toolkit2 是模型转换，Model Zoo 是官方部署样例，RKNPU2 是底层 C API/Runtime，RKLLM 是语言模型工具链；换模型类型不能沿用不匹配的 SDK。

```bash
python3 examples/lesson_04.py --repo toolkit2 --ref HEAD --output build/upstream.json
```

### 2. git ls-remote：读取真实远端版本

**输入：** 可联网的 git、远端 URL 与 ref 名称。**输出：** SHA/ref 列表写入 JSON。

它不下载整套 SDK，也不保证某个 commit 与当前 BSP 一定兼容。记录 SHA 后，还需阅读对应版本的 release、wheel 以及 Runtime 兼容表。

```bash
git ls-remote https://github.com/airockchip/rknn-toolkit2.git HEAD
```

### 3. 正确的版本定位顺序

**输入：** 板卡型号、BSP/内核、工具链、运行库、模型格式。**输出：** 可重复查询的版本与文件来源清单。

应固定主机 Toolkit2、板端 Lite2/librknnrt.so、Model Zoo 源码提交的组合；只说“最新版”无法复现。

```bash
python3 examples/lesson_00.py --output build/lesson00/environment.json
python3 examples/lesson_04.py --repo model_zoo --ref HEAD
```

**数据例题：** 两个不同 commit 的同名 yolov8.rknn 可能有不同输出 shape；模型和后处理必须来自匹配版本。git ls-remote 成功只证明远端可访问。

**验收边界：** 明确列出四个仓库的用途、实际 HEAD commit、目标板 BSP/Runtime 来源，并保存查到的结果；无网络时记录此项待完成。

## 配套可运行源码

- [本讲独立 Python 实例](../examples/lesson_04.py) · [操作手册与参数说明](../examples/notes/lesson_04.md)
- [通用依赖与课程代码说明](../examples/README.md)

在仓库根目录运行：

```bash
python3 examples/lesson_04.py --repo toolkit2 --ref HEAD --output build/upstream.json
```

**如何验收：** 联网读取实际 Rockchip 工具仓库 HEAD commit，不自动安装 SDK。

## 原始字幕（仅供核对）

<details>
<summary>展开含时间戳的原始转写稿</summary>

```text
04_瑞芯微github仓库介绍
Coder-Dawn
https://www.bilibili.com/video/BV11DjT6uEhc

[0:00] 这节课我们来讲最新微原厂NPU的资料介绍那首先的话就是我们打开它的这个GITHUB的一个官网的一个地址那打开之后可以看到里面有六个部分还有r k n toget two model zl l m
[0:18] 还有RGA嗯优了V8 优了V5 那其实从这些名字上面我们可能也能呃听出来一些它的功能吧那接下来我来一个一个讲一下我们首先打开这个还可以看到这个i k n topic to 它里面还有三个比较重要比较核心的套件
[0:43] 那第一个还是我们的r k n token two啊这里大家需要注意和区分一下这个toget to是包含在它之内的就是包含在它之内的它里面还有一个token to tcket list to
[0:58] 还有一个r k n p o two 那这三个套件它到底是什么功能呢啊这个这个r k n toget to 它主要就是进行模型的一个转换的那其中它指是在我们PC上面进行一个呃运行和转换的
[1:19] 然后使用的也是Python的一个代码那这个like to 还有这个r k n p o two的话那它他们两个可以归为一类他们是在他们都只能在开发板上面进行一个运行那其中上面这个LF它调用的是Python接口啊
[1:41] 下面这个NPO的话他调用的是C语言C加加的一个接口好吧这个就是呃它的一个功能那上面这个它就可以用于哎我们的一个简单的一个测试验证然后下面这个的话我们可以对它进行一个工程的一个部署因为大家也知道像这个AC语言
[2:04] 它的一个性能是比Python的好一些的啊这个的话就是rk n token two的一个简单介绍那接下来我们来看第二个就是r k n model ro 那model也是我们官方就是把市面上一些常见的一些模型
[2:23] 进行了一个整理好在这里我可以点一下这个简体中文我看一下它的一个read me 那他也可以看到就是保留了包含了目前主流的一个战法的一个部署的一个历程然后C语言的Python的也都有哎
[2:41] 就是它像有呃mobile net 然后Rest net dodo系列啊包括还有下面的人脸检测车牌识别文字检测包括还有一些语音相关的模型就这个库是瑞星微自己做好了就是供大家去啊进行一个学习和使用嘛
[3:05] 那在这里我也是点开一个比如说呃点开一个这个吧 MOBNET还可以看到它也是有有C加加版本的啊然后也有Python版本的哦但是它的一个缺点就是可能你看这个Python呢它就一个文件然后像这个C加加的
[3:29] 其实他也就呃加上这个man 加上点H它也就是两三个文件那就搞定了啊这种其实就是适合我们快速的验证啊适合我们学习我们在真正的项目开发当中肯定是需要进行封装啊这些操作和处理的那这个就是我们的model o
[3:53] 那如果说大家有一款开发版然后玩一玩试一试这些模型呃学习一些模型那这个也是一个非常不错的一个平台那第三个的话我们来看一下这个LLM 也是看一下他的一个REN点哎这个的话和我们前面的一个NA部署
[4:15] 也是类似的也就是它主要是针对我们的一个大模型进行一个部署的啊比如说像千万deep DC呃联网啊等等这些模型它也可以进行一个转换也使用RKLMTKE进行转换转换成我们大模呃卫星为支持的大模型的一个格式
[4:39] 然后就可以进行一个部署了啊在我们这套课程的最后也会带着大家去部署一个music的一个模型啊其中我们这个RK3588的话叫4B7B模型其实都是可以部署的那这个就是这个仓库那接下来我们再看一下这个IDA操作
[5:04] 那这个仓库的话是一个独立的 2D的一个硬件加速器还可以用于加速点线绘制执行图像的缩放旋转啊等等就是进行一些常见的2D操作那额他的一个主要功能额有两个方面吧第一个可能是在我们进行一些媒体呃
[5:28] 音视频媒体方面处理可能会使用它去进行一些处理和加速那第二个就是我们在进行这个AI部署的时候我们也是可以采用RGA的方式去进行加速的如果说我们的某一个模型在它里面涉及到了比较多的像这些图像的旋转缩放
[5:50] 然后点线的绘制等等也就是说模型和它的相关度比较高的话我们使用RTA加速的话可能也会有一个比较好的一个效果那这个就是RTA 然后面两个的话也是瑞星微的官方对他进行了一些适配就是做了一个demo供我们学习去使用呢
[6:13] 看一下这个read me也是有中文的就是他简单的介绍了一下这个呃YUE呃当然现在已经26了就是有这些呃这个模性能的一个图片然后包括怎么样快速去呃使用这个东西那当然这个也是来自于他这个ULTRALI这个官网呢
[6:43] 但是他的这些方法的话其实比较适合我们的快速验证啊可能大家照着官网去做的时候呃可能会出一些问题小的问题可能还需要去手动的修改一下啊这个是呃这个优路V8的这个V5的打开应该也差不多吧
[7:09] 额可以看到也差不多就都是这么一个形式额这个的话就是我们这个瑞星微这个官方资料的一个介绍那在下面的话也是呃写的比较详细就是它里面每个部分的一个功能吧呃在下面也都有描述看看哦
[7:37] 那这个内容的话呃我就不再给大家去读了啊大家下来的话可以看看这个文档啊就是了解一下就可以了那截止到这节课为止呃和大家讲的这些东西都是呃理论上面的一些东西可能也比较枯燥比较无聊那大家的话就是可以呃这个快速的听一下
[8:02] 然后了解一下或者说直接看看这个文档如果说具备一定基础的话就是直接跳过的话其实也都是不影响我们的学习的啊说完这个的话这节课的话我们也就讲完了也是感谢大家的一个观看
```

</details>
