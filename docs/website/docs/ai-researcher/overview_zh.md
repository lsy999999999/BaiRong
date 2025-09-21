---
sidebar_position: 1
title: AI Researcher Overview
---

# 概述 (Overview)

欢迎使用 **AI Social Researcher** 子系统！这是一个旨在通过大语言模型（LLM）自动化社会科学模拟研究中关键阶段的强大工具。

`AI Social Researcher` 的核心使命是解放研究人员，让他们能更专注于高层次的科学构想、实验设计和结果解读，而不是耗费大量时间在繁琐的协议撰写、环境配置和报告编写上。通过将自然语言的研究想法转化为标准化的模拟协议和最终的研究报告，本子系统能够显著提升研究效率和规范性。

---

## 核心功能

本子系统主要由两大核心组件构成，覆盖了从研究构想到成果发布的完整流程：

1.  **实验环境设计 (Environment Design)**: 将一个模糊的自然语言研究主题，通过多智能体协作，系统性地转化为一个详尽的、遵循 ODD (Overview, Design Concepts, Details) 规范的模拟协议，并自动创建对应的模拟环境目录结构。

2.  **研究报告生成 (Report Generation)**: 读取模拟结束后的输出数据（包括 ODD 协议、场景信息、指标数据和图表），全自动地生成一篇结构完整、内容详实的 PDF 格式研究报告，并支持通过多轮审阅进行迭代优化。

---

## 适用人群

本子系统特别适合以下用户：
-   **社会科学研究者**: 希望加速模拟实验流程，特别是简化 ODD 协议制定和报告撰写的研究人员。
-   **计算社会科学学生**: 学习和实践社会模拟方法，需要一个标准化工具来辅助完成课程项目或论文研究。
-   **AI Agent开发者**: 探索 LLM 在科研自动化领域的应用，本子系统提供了一个完整的端到端参考实现。

---

## 项目结构概览

为了更好地使用本工具，了解其关键目录的组织方式非常重要。所有操作都应在项目根目录下执行。

```
<project_root>/
├── config/
│   └── model_config.json      # LLM 模型配置的默认位置
├── src/
│   ├── envs/
│   │   └── <scene_name>/          # 单个模拟环境的根目录
│   │       ├── scene_info.json    # 环境核心信息 (包含 ODD)
│   │       ├── code/              # 模拟所需的代码
│   │       ├── metrics_plots/     # 模拟生成的图表
│   │       └── research/          # AI Researcher 生成的所有文档
│   └── researcher/
│       ├── env_design.py        # 实验设计的总入口脚本
│       ├── report_generation.py # 报告生成的总入口脚本
│       ├── env_design/          # 实验设计功能模块
│       └── report_generation/   # 报告生成功能模块
└── ...
```

---

## 下一步

-   要了解工具包的整体工作流程，请查阅 **[研究工作流 (Research Workflow)](<./research-workflow.md>)**。
-   要深入学习如何从一个想法生成模拟环境，请查阅 **[实验环境设计 (Environment Design)](<./environment-design.md>)**。
-   要学习如何自动生成研究报告，请查阅 **[研究报告生成 (Report Generation)](<./report-generation.md>)**。
-   要查看具体的命令行和代码示例，请直接前往 **[用法示例 (Examples)](<./examples.md>)**。

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
