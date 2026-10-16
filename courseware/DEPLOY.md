# GitHub Pages 课件网站发布指南

本仓库新增了手动发布工作流 [课程发布工作流](https://github.com/crazyname/RK3588-Embedded-AI-Tutorial/blob/main/.github/workflows/pages.yml)。运行它不会上传模型权重或自动安装板端 NPU 驱动。

## 初次启用

1. 仓库管理者打开 GitHub Settings → Pages，选择 Source → GitHub Actions；该设置要求仓库相应管理权限。
2. 进入 Actions → Publish course website，点击 Run workflow，选择 main 分支后确认。
3. 等待 GitHub Pages 部署任务成功，点击 Actions/Pages 返回的实际站点 URL，不要根据猜测判断网站是否上线。

当 Pages 正式启用并按 GitHub 默认 project site 地址部署，通常会使用以下形式：

    https://crazyname.github.io/RK3588-Embedded-AI-Tutorial/

这是预期地址格式，目前**并未确认站点已发布**。如果未启用 Pages，手动运行可能失败，请先完成设置。

## 打包范围

工作流会保留相对路径，包含 courseware/、docs/、examples/、boards/、requirements/、models/ 和 tools/，并从站点根目录跳转到 courseware/index.html。课程 HTML 依旧单篇连续向下滚动，不进行幻灯片分页。

网页只能展示 Python/C++ 代码和讲义，不能在浏览器中执行 RKNN 或替代 ROCK 5B 板端实验。
