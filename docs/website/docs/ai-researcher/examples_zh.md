---
sidebar_position: 5
title: Usage Examples
---

# 用法示例 (Examples)

本页提供了 `AI Social Researcher` 工具包的具体用法示例，包括命令行调用和Python API。

---

## 准备工作: 模型配置

在使用任何一个模块之前，你需要先配置好所使用的 LLM 模型。

-   配置文件通常位于 `config/model_config.json`。
-   你需要通过两个命令行参数来指定模型：
    -   `--model_config <path/to/config.json>`: 指向你的模型配置文件。
    -   `--model_name <model_name>`: 使用配置文件中定义的具体模型名称（例如 `gpt-4o`）。

所有示例都假设你已在 `config/model_config.json` 中配置好了名为 `gpt-4o` 的模型。

---

## 1. 实验环境设计 (Environment Design)

使用 `src/researcher/env_design.py` 从一个想法生成 ODD 协议和环境。

### 命令行示例

这是一个完整的示例，它会创建一个关于“错误信息传播”的研究场景，并进行评估。

```bash
# 运行以下命令 (请确保在项目根目录)
python src/researcher/env_design.py \
    --topic "Investigating the spread of misinformation in online social networks" \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    --save \
    --assess
```

**参数说明**:

-   `--topic`: 定义了研究的核心思想。
-   `--scene_name`: 将在 `src/envs/` 下创建名为 `misinformation_spread` 的目录。
-   `--model_name`: 使用名为 `gpt-4o` 的模型配置来驱动所有 Agent。
-   `--save`: 保存 `inspiration_output.json` 等中间文件，便于调试。
-   `--assess`: 在生成 ODD 协议后，额外运行 `AssessorAgent` 进行质量评估。

### Python API 示例

你也可以在自己的 Python 脚本中调用此功能。

```python
from pathlib import Path
from src.researcher.env_design import Coordinator
from src.onesim.models import get_model_manager

# 假设项目根目录是当前工作目录
project_root = Path.cwd()
model_config_file = project_root / "config" / "model_config.json"

if not model_config_file.exists():
    raise FileNotFoundError(f"Model config not found at {model_config_file}")

# 加载模型配置
model_manager = get_model_manager()
model_manager.load_model_configs(str(model_config_file))

# 初始化并运行设计协调器
design_coordinator = Coordinator(
    scene_name="misinformation_spread_api",
    model_name="gpt-4o",
    save_intermediate=True
)

# 运行核心流程
# detailed_spec 将包含 ODD 协议等信息
detailed_spec = design_coordinator.run("A study on misinformation spread dynamics")

print("Environment design complete!")
print(f"Check outputs in: src/envs/misinformation_spread_api/")

# 也可以单独调用评估功能
# assessment_results = design_coordinator.assess(scene_name="misinformation_spread_api")
# print(assessment_results)
```

---

## 2. 研究报告生成 (Report Generation)

使用 `src/researcher/report_generation.py` 为一个已存在的场景生成报告。

### `full` 命令 (推荐)

这是最常用、最完整的命令，执行从分析到生成带 3 轮迭代优化的最终 PDF 报告的全流程。

```bash
# 确保 'misinformation_spread' 场景已存在并包含模拟数据
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    full \
    --report_title "Analysis of Misinformation Spread Dynamics" \
    --report_author "AI Research Team" \
    --iterations 3
```

**子命令参数说明**:

  - `full`: 指定执行全流程。
  - `--report_title`: 设置 PDF 报告的标题。
  - `--report_author`: 设置 PDF 报告的作者。
  - `--iterations`: 指定审阅和修订的次数。`3`表示 1 次初稿 + 2 次修订。

### 分步子命令示例

你也可以分步执行任务，这在调试时非常有用。

#### 第 1 步: 分析数据 `analyze`

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    analyze
```

> 这会生成 `src/envs/misinformation_spread/research/analysis_result.md`。

#### 第 2 步: 生成大纲 `outline`

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    outline
```

> 这会生成 `src/envs/misinformation_spread/research/report_outline.md`。

#### 第 3 步: 生成报告 `report`

此命令会利用已有的分析和提纲文件来撰写报告。

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    report \
    --report_title "My Report" \
    --iterations 3
```

#### 单独审阅 `review`

如果你想对一个已有的 `.tex` 文件进行审阅。

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    review \
    --latex_file "src/envs/misinformation_spread/research/report/simulation_report_iter1.tex"
```

> 这会在同目录下生成一个 `review_...json` 文件，包含审阅意见。

