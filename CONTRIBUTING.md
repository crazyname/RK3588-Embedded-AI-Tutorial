# 课程开发与贡献规则

所有功能变更需区分 PC 算法功能、SDK 模型功能与 RK3588 实机测试。仅脚本能执行 --help 不代表模型推理正确。

从仓库根目录运行：

    python3 examples/audit_course.py --strict
    python3 tools/validate_repo.py
    python3 -m unittest discover -s examples/tests -v

修改某节课程时，同步检查 docs/ 的教学正文、courseware/lessons/ 的连续滚动 HTML、examples/lesson_NN.py 的真实代码和 examples/notes/ 中不重复的运行说明。不要恢复七行课号转发入口。

提供实机结果须附板型/PCB 修订、镜像、Kernel、Driver、SDK、模型 SHA256、预处理、输入输出、温度、p50/p95、运行次数，并注明是否为模拟器。未经许可不提交第三方权重、私人图像、硬件序列号、密钥或数据集。
