---
sidebar_position: 5
title: Usage Examples
---

# Usage Examples

This page provides specific usage examples for the `AI Social Researcher` toolkit, including command-line calls and the Python API.

---

## Preparation: Model Configuration

Before using any module, you first need to configure the LLM model you will be using.

-   The configuration file is typically located at `config/model_config.json`.
-   You need to specify the model using two command-line arguments:
    -   `--model_config <path/to/config.json>`: Points to your model configuration file.
    -   `--model_name <model_name>`: Uses a specific model name defined in the configuration file (e.g., `gpt-4o`).

All examples assume you have already configured a model named `gpt-4o` in `config/model_config.json`.

---

## 1. Environment Design

Use `src/researcher/env_design.py` to generate an ODD protocol and environment from an idea.

### Command-Line Example

This is a complete example that creates a research scenario about "misinformation spread" and assesses it.

```bash
# Run the following command (ensure you are in the project root directory)
python src/researcher/env_design.py \
    --topic "Investigating the spread of misinformation in online social networks" \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    --save \
    --assess
```

**Argument Descriptions**:

-   `--topic`: Defines the core idea of the research.
-   `--scene_name`: Will create a directory named `misinformation_spread` under `src/envs/`.
-   `--model_name`: Uses the model configuration named `gpt-4o` to drive all Agents.
-   `--save`: Saves intermediate files like `inspiration_output.json` for easier debugging.
-   `--assess`: After generating the ODD protocol, additionally runs the `AssessorAgent` for a quality assessment.

### Python API Example

You can also call this functionality from your own Python scripts.

```python
from pathlib import Path
from src.researcher.env_design import Coordinator
from src.onesim.models import get_model_manager

# Assume the project root is the current working directory
project_root = Path.cwd()
model_config_file = project_root / "config" / "model_config.json"

if not model_config_file.exists():
    raise FileNotFoundError(f"Model config not found at {model_config_file}")

# Load the model configuration
model_manager = get_model_manager()
model_manager.load_model_configs(str(model_config_file))

# Initialize and run the design coordinator
design_coordinator = Coordinator(
    scene_name="misinformation_spread_api",
    model_name="gpt-4o",
    save_intermediate=True
)

# Run the core process
# detailed_spec will contain the ODD protocol and other information
detailed_spec = design_coordinator.run("A study on misinformation spread dynamics")

print("Environment design complete!")
print(f"Check outputs in: src/envs/misinformation_spread_api/")

# You can also call the assessment function separately
# assessment_results = design_coordinator.assess(scene_name="misinformation_spread_api")
# print(assessment_results)
```

---

## 2. Report Generation

Use `src/researcher/report_generation.py` to generate a report for an existing scene.

### `full` Command (Recommended)

This is the most common and complete command, executing the full workflow from analysis to generating the final PDF report with 3 rounds of iterative optimization.

```bash
# Ensure the 'misinformation_spread' scene exists and contains simulation data
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    full \
    --report_title "Analysis of Misinformation Spread Dynamics" \
    --report_author "AI Research Team" \
    --iterations 3
```

**Subcommand Argument Descriptions**:

  - `full`: Specifies that the full workflow should be executed.
  - `--report_title`: Sets the title of the PDF report.
  - `--report_author`: Sets the author of the PDF report.
  - `--iterations`: Specifies the number of review and revision cycles. `3` means 1 initial draft + 2 revisions.

### Step-by-Step Subcommand Examples

You can also execute the tasks step-by-step, which is very useful for debugging.

#### Step 1: Analyze Data (`analyze`)

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    analyze
```

> This will generate `src/envs/misinformation_spread/research/analysis_result.md`.

#### Step 2: Generate Outline (`outline`)

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    outline
```

> This will generate `src/envs/misinformation_spread/research/report_outline.md`.

#### Step 3: Generate Report (`report`)

This command uses the existing analysis and outline files to write the report.

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    report \
    --report_title "My Report" \
    --iterations 3
```

#### Standalone Review (`review`)

If you want to review an existing `.tex` file.

```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_name "gpt-4o" \
    review \
    --latex_file "src/envs/misinformation_spread/research/report/simulation_report_iter1.tex"
```

> This will generate a `review_...json` file in the same directory containing the review comments.

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
