---
sidebar_position: 4
title: Report Generation Module
---

# 研究报告生成 (Report Generation)

本模块是 `AI Social Researcher` 工作流的最后一环。它负责读取已经完成的模拟实验所产生的数据和图表，并自动撰写一篇全面、专业的研究报告。

---

## 先决条件 (Prerequisites)

在运行报告生成之前，你 **必须** 拥有一个由“实验环境设计”模块创建或手动配置的场景 (scene)。这个场景目录必须包含以下内容：

1.  **场景信息文件**:
    -   路径: `src/envs/<scene_name>/scene_info.json`
    -   内容: 包含实验的 ODD 协议和元数据。这是分析模块理解“方法论”部分的关键。

2.  **指标计算代码 (可选但推荐)**:
    -   路径: `src/envs/<scene_name>/code/metrics/metrics.py`
    -   内容: 包含用于计算模拟核心指标的 Python 函数。`DataAnalysisAgent` 会读取此文件以理解指标的含义。

3.  **指标图表**:
    -   路径: `src/envs/<scene_name>/metrics_plots/`
    -   内容: 存储模拟过程中生成的各种指标图表（如 `.png` 文件）。这些图表将被自动嵌入到最终报告的“结果”部分。

---

## 核心逻辑与流程

报告生成功能由主脚本 `src/researcher/report_generation.py` 驱动。它通过一系列子命令来管理不同的任务，其内部同样由 LLM 智能体驱动。

### 关键智能体与过程

-   **`DataAnalysisAgent` (数据分析智能体)**
    -   **职责**: 综合分析所有输入信息（ODD 协议、指标代码、图表），从模拟结果中提取关键的发现、趋势和洞察。
    -   **产出**: `analysis_result.md`，一份对模拟结果的详细文字分析。

-   **`OutlineWritingAgent` (大纲编写智能体)**
    -   **职责**: 基于 `analysis_result.md` 的内容，构建一份符合学术规范的报告大纲。
    -   **产出**: `report_outline.md`，定义了报告的章节结构（如引言、相关工作、方法、结果、讨论、结论）。

-   **报告撰写过程 (Writing Process)**
    -   由 `src/researcher/report_generation/writing_process/generate_full_report.py` 模块处理。
    -   **职责**: 依据生成的大纲，调用 LLM 逐节填充内容，并将所有文字、代码片段、图表引用整合到一个 `.tex` 文件中。最后，调用 LaTeX 编译器生成 PDF。

-   **`ReviewerAgent` (审阅智能体 - 可选)**
    -   **职责**: 对生成的 `.tex` 报告草稿进行评审，检查其逻辑、清晰度、流畅性和完整性。
    -   **产出**: 对报告的修改建议（JSON 格式），供下一轮迭代使用。

---

## 工作流程与产出物

1.  **指定场景**: 用户通过 `--scene_name` 参数告诉脚本要为哪个实验生成报告。
2.  **执行子命令**: 用户选择一个子命令（如 `full`）来启动整个流程。
3.  **分析与大纲**: `DataAnalysisAgent` 和 `OutlineWritingAgent` 首先运行，生成分析和提纲文件。
4.  **撰写与编译**: 系统根据大纲撰写报告初稿 (`.tex`) 并编译为 PDF。
5.  **迭代优化 (可选)**: 如果启用，`ReviewerAgent` 将对报告进行审查，然后系统根据反馈进行修改并重新编译。此过程可重复多次。
6.  **最终产出**: 所有报告相关文件都保存在 `src/envs/<scene_name>/research/report/` 目录中。

**主要输入**:
-   一个准备就绪的场景目录 (`src/envs/<scene_name>/`)

**主要输出文件**:
-   `src/envs/<scene_name>/research/analysis_result.md`: 数据分析报告。
-   `src/envs/<scene_name>/research/report_outline.md`: 最终报告的大纲。
-   `src/envs/<scene_name>/research/report/simulation_report_final.pdf`: **最终的PDF研究报告**。
-   `src/envs/<scene_name>/research/report/simulation_report.tex`: 最终报告的 LaTeX 源码。
-   `src/envs/<scene_name>/research/report/review_*.json`: (若启用) 每次迭代的审阅意见。

---

## 如何使用 (子命令)

`report_generation.py` 脚本通过子命令来执行特定任务。所有子命令都必须提供 `--scene_name`。

-   `analyze`: 仅执行数据分析。
-   `outline`: 仅生成报告大纲（依赖分析结果）。
-   `report`: 撰写和编译报告（可迭代），默认跳过分析和提纲步骤。
-   `full`: **最常用的命令**。执行从分析、大纲到最终报告的全流程。
-   `review`: 对一个已有的 `.tex` 报告文件进行单次审阅。

**查看所有子命令的详细用法和参数，请前往 [用法示例 (Examples)](<./examples.md>)。**

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
