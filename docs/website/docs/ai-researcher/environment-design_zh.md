---
sidebar_position: 3
title: Environment Design Module
---

# 实验环境设计 (Environment Design)

本模块负责将研究者的初始自然语言想法，转化为一个结构化、标准化的模拟实验环境。它的核心产出是一份详尽的 **ODD (Overview, Design Concepts, Details) 协议** 和相应的目录结构。

---

## 核心逻辑

实验设计功能由主脚本 `src/researcher/env_design.py` 驱动。该脚本扮演着“协调员”的角色，依次调用一系列专门的大模型智能体（LLM Agents），引导它们协作完成从概念到协议的转化过程。

---

## 关键智能体 (Key Agents)

这些智能体位于 `src/researcher/env_design/` 目录中，各司其职：

-   **`InspirationAgent` (灵感智能体)**
    -   **职责**: 接收用户输入的宽泛研究主题（如 "社交媒体对政治极化的影响"）。
    -   **产出**: 生成多个具体的、可执行的研究问题和场景设想，为后续步骤提供丰富的选项。

-   **`EvaluatorAgent` (评估智能体)**
    -   **职责**: 对 `InspirationAgent` 产生的多个场景进行评估。
    -   **评估维度**: 主要考量研究场景的相关性、可行性、新颖性和潜在影响力。
    -   **产出**: 选出最具有研究潜力的一个场景，并说明选择的理由。

-   **`DetailerAgent` (详述智能体)**
    -   **职责**: 这是本阶段的核心。它接收 `EvaluatorAgent` 选定的场景。
    -   **产出**: 将该场景扩展成一份非常详细的 ODD 协议，内容严格遵循 ODD 规范。同时生成两种格式的协议 (`.md` 和 `.json`)，并提取关键场景信息。

-   **`AssessorAgent` (评估智能体 - 可选)**
    -   **职责**: 对 `DetailerAgent` 生成的 ODD 协议进行质量评估。
    -   **评估维度**: 检查协议的完整性、清晰度、逻辑一致性和可操作性。
    -   **产出**: 一份评估报告，帮助研究者判断生成的协议是否达到了可用于研究的标准。

---

## 工作流程与产出物

当你运行 `env_design.py` 脚本时，系统会执行以下步骤：

1.  **接收输入**: 获取用户提供的 `--topic` 和可选的 `--scene_name`。
2.  **目录创建**: 在 `src/envs/` 路径下创建名为 `<scene_name>` 的新目录，作为本次模拟环境的根目录。
3.  **智能体协作**: 按顺序执行上述智能体链，每一步的输出都作为下一步的输入。
4.  **保存结果**: 所有中间和最终产物都被保存在 `src/envs/<scene_name>/research/env_design/` 目录下。

**主要输入**:
-   `--topic`: 一个描述研究兴趣的字符串。

**主要输出文件**:
-   `src/envs/<scene_name>/scene_info.json`: **最重要的输出文件**。它包含了整个环境的元数据，尤其是以 JSON 格式存储的完整 ODD 协议，供后续的报告生成模块使用。
-   `src/envs/<scene_name>/research/env_design/detailed_specification.md`: Markdown 格式的 ODD 协议，具有良好的可读性，方便研究者直接查看和修改。
-   `src/envs/<scene_name>/research/env_design/odd_protocol.json`: ODD 协议的 JSON 格式副本。
-   `src/envs/<scene_name>/research/env_design/inspiration_output.json`: `InspirationAgent` 生成的潜在研究问题列表。
-   `src/envs/<scene_name>/research/env_design/evaluator_output.json`: `EvaluatorAgent` 筛选出的场景及其理由。
-   `src/envs/<scene_name>/research/env_design/assessment_results.json` (可选): `AssessorAgent` 对 ODD 协议的评估结果。

---

## 如何使用

该模块主要通过命令行使用。你需要提供研究主题，并指定一个场景名称。

**基本用法**:
```bash
python src/researcher/env_design.py \
    --topic "你的研究主题" \
    --scene_name "你的场景名称" \
    --model_name "gpt-4o"
```
-   `--topic <string>`: **(必需)** 你的研究主题。
-   `--scene_name <string>`: (可选) 为环境指定的文件夹名称。若不提供，将自动生成一个。
-   `--assess`: (可选) 在生成后，对 ODD 协议进行质量评估。
-   `--save`: (可选) 保存每个智能体的中间输出文件。

**查看完整的命令行和API示例，请前往 [用法示例 (Examples)](<./examples.md>)。**


