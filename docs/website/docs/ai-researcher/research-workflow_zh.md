---
sidebar_position: 2
title: Research Workflow
---

# 研究工作流 (Research Workflow)

`AI Social Researcher` 工具包将复杂的社会模拟研究流程抽象为两个主要阶段，形成一个从灵感到报告的自动化闭环。理解这个工作流是高效使用本工具的关键。

---

## 整体流程示意

整个工作流始于一个简单的自然语言想法，终于一份正式的 PDF 研究报告。

**研究想法 (Natural Language Idea)**
> "我想研究社交媒体对政治极化的影响。"

⬇

### **阶段一: 实验环境设计 (Environment Design)**
* **目标**: 将抽象的想法具体化、规范化。
* **过程**:
    1.  **灵感激发**: LLM Agent 根据初始主题，生成多个潜在的、更具体的研究问题和场景。
    2.  **评估筛选**: 另一个 Agent 评估这些场景的科研价值、可行性和新颖性，并选出最佳方案。
    3.  **细节详述**: 核心 Agent 将选定的场景，扩展为一份完整的 **ODD (Overview, Design Concepts, Details) 协议**。ODD 协议是社会模拟领域的标准文档，它精确描述了模拟的目的、实体、过程和调度。
    4.  **环境搭建**: 系统根据 ODD 协议，自动在 `src/envs/` 目录下创建一个新的场景文件夹 `<scene_name>`，并生成 `scene_info.json` (包含 ODD 协议的 JSON 格式) 等核心配置文件。
* **产出**: 一个结构化、标准化的模拟环境文件夹，准备好用于后续的模拟实验。
* **详情**: [实验环境设计文档](<./environment-design.md>)

⬇

**(中间步骤: 用户运行模拟)**
> 在这一步，用户需要利用阶段一生成的环境配置，运行实际的社会模拟程序。`AI Social Researcher` **不执行**模拟本身，而是处理模拟前和模拟后的工作。模拟过程应产生量化指标（metrics）和可视化图表（plots）。

⬇

### **阶段二: 研究报告生成 (Report Generation)**
* **目标**: 将分散的模拟数据和图表，整合成一篇连贯、专业的学术报告。
* **过程**:
    1.  **数据分析**: LLM Agent 读取 `scene_info.json` 中的 ODD 协议、`metrics.py` 中的指标计算逻辑、以及 `metrics_plots/` 目录下的所有图表，对模拟结果进行综合分析，提取核心发现和洞察。
    2.  **大纲构建**: 基于分析得出的洞察，Agent 生成一份逻辑清晰的报告大纲，涵盖引言、方法、结果、讨论等标准章节。
    3.  **报告撰写与编译**: 系统根据大纲，逐章填充内容，将文字、图表和 ODD 协议中的方法论描述，编译成一份完整的 LaTeX 草稿。
    4.  **（可选）审阅与迭代**: `ReviewerAgent` 可以像同行评审一样，检查报告草稿的清晰度、逻辑性和完整性，并提出修改建议。系统根据这些建议自动修改报告，此过程可重复多次，以持续提升报告质量。
* **产出**: 一份存储在 `research/report/` 目录下的 `simulation_report_final.pdf` 文件。
* **详情**: [研究报告生成文档](<./report-generation.md>)

---

通过以上两个阶段，`AI Social Researcher` 实现了从一个模糊概念到一份精美报告的自动化飞跃。

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
