# AI Social Researcher

## Overview

The `AI Social Researcher` toolkit automates key stages of the social simulation research workflow using Large Language Models (LLMs). It consists of two main components:

1.  **Environment Design**: Transforms a natural language research topic into a detailed ODD (Overview, Design Concepts, Details) protocol and sets up the simulation environment structure.
2.  **Report Generation**: Takes simulation outputs (including the ODD protocol/scene information, metrics, and visualizations) to automatically generate a comprehensive research report in PDF format, with an optional iterative review process.

This toolkit aims to enhance research efficiency, standardization, and allows researchers to focus on high-level concepts while automating laborious documentation and reporting tasks.

## Core Components & Workflow

### 1. Experimental Design (Natural Language -> ODD Protocol & Environment)

This component uses a series of LLM-powered agents to refine a vague research idea into a concrete simulation plan.

-   **Main Script**: `src/researcher/env_design.py`
-   **Key Agents** (located in `src/researcher/env_design/`):
    -   `InspirationAgent`: Generates potential research questions and scenarios from the initial topic.
    -   `EvaluatorAgent`: Evaluates the generated scenarios and selects the most promising one.
    -   `DetailerAgent`: Elaborates the selected scenario into a detailed ODD protocol (Markdown and JSON formats) and extracts key scene information.
    -   `AssessorAgent`: (Optional) Assesses the quality of the generated ODD protocol based on relevance, fidelity, feasibility, and significance.
-   **Workflow**:
    1.  User provides a research topic (e.g., "the impact of social media on political polarization").
    2.  The `Coordinator` in `env_design.py` orchestrates the agents.
    3.  A `scene_name` is determined (either user-provided or generated).
    4.  The necessary directory structure is created under `src/envs/<scene_name>/` (relative to project root).
    5.  Outputs are saved in `src/envs/<scene_name>/research/env_design/`, including:
        -   `inspiration_output.json`: Potential research questions.
        -   `evaluator_output.json`: Selected scenario and rationale.
        -   `detailed_specification.md`: The ODD protocol in Markdown.
        -   `odd_protocol.json`: The ODD protocol in JSON.
        -   `final_output_summary.json`: Summary of the design process.
    6.  A `scene_info.json` is saved in `src/envs/<scene_name>/`.
    7.  (Optional) An assessment of the ODD protocol can be run, producing `assessment_results.json`.

### 2. Automated Report Generation (Simulation Data -> PDF Report)

This component takes the outputs from a simulation run (based on an environment typically set up by the Experimental Design component) and generates a full research report.

-   **Main Script**: `src/researcher/report_generation.py`
-   **Key Agents** (located in `src/researcher/report_generation/`):
    -   `DataAnalysisAgent`: Analyzes simulation data (from `scene_info.json`, metric calculation functions, and image plots) to extract insights.
    -   `OutlineWritingAgent`: Generates a structured report outline based on the analysis.
    -   `ReviewerAgent`: (Optional) Reviews the drafted report and provides feedback for iterative improvement.
-   **Report Writing Process**: Managed by `src/researcher/report_generation/writing_process/generate_full_report.py`, which compiles LaTeX.
-   **Workflow**:
    1.  User specifies a `scene_name` that corresponds to an existing environment in `src/envs/`.
    2.  The script automatically locates `scene_info.json`, metric calculation functions (expected at `src/envs/<scene_name>/code/metrics/metrics.py`), and the latest metric plot images from `src/envs/<scene_name>/metrics_plots/`.
    3.  **Data Analysis**: Generates `analysis_result.md` in `src/envs/<scene_name>/research/`.
    4.  **Outline Generation**: Generates `report_outline.md` in `src/envs/<scene_name>/research/`.
    5.  **Report Drafting & Compilation**: A LaTeX draft is created.
    6.  **(Optional) Review & Iteration**: The `ReviewerAgent` can assess the draft, and the report can be iteratively refined.
    7.  **Final PDF**: The final report (e.g., `simulation_report_final.pdf`) is saved in `src/envs/<scene_name>/research/report/`.

## Directory Structure (Key Files, relative to project root)

```
<project_root>/
├── config/
│   └── model_config.json        # Default location for LLM configurations
├── src/
│   ├── envs/
│   │   └── <scene_name>/            # Root for a specific simulation environment
│   │       ├── scene_info.json      # General info, ODD, metrics metadata
│   │       ├── code/
│   │       │   └── metrics/
│   │       │       └── metrics.py   # Python functions for metric calculations
│   │       ├── metrics_plots/       # Directory for simulation output plots
│   │       │   └── round_*/         # Plots aggregated by rounds
│   │       │       └── scene_metrics/
│   │       │           └── <metric_name>/
│   │       │               └── *.png
│   │       └── research/
│   │           ├── env_design/      # Outputs from experimental design
│   │           │   ├── detailed_specification.md
│   │           │   ├── odd_protocol.json
│   │           │   ├── inspiration_output.json
│   │           │   ├── evaluator_output.json
│   │           │   └── assessment_results.json (optional)
│   │           ├── analysis_result.md # Output from report_generation data analysis
│   │           ├── report_outline.md  # Output from report_generation outline
│   │           └── report/            # Outputs from report_generation
│   │               ├── simulation_report.tex
│   │               ├── simulation_report_final.pdf
│   │               └── review_*.json (if review is enabled)
│   └── researcher/
│       ├── __init__.py
│       ├── base_agent.py
│       ├── env_design.py         # Main script for experimental design
│       ├── report_generation.py  # Main script for report generation
│       ├── env_design/           # Modules for experimental design agents & logic
│       │   ├── __init__.py
│       │   ├── inspiration_agent.py
│       │   ├── evaluator_agent.py
│       │   ├── detailer_agent.py
│       │   └── assessor_agent.py
│       ├── report_generation/    # Modules for report generation agents & logic
│       │   ├── __init__.py
│       │   ├── data_analysis_agent.py
│       │   ├── outline_writing_agent.py
│       │   ├── reviewer_agent.py
│       │   └── writing_process/
│       │       ├── __init__.py
│       │       └── generate_full_report.py # Handles LaTeX compilation
│       └── test/
│           └── my_model_config.json # Fallback location for model_config.json
└── ... (other project files like README.md for the main project)
```

## Usage Instructions

All commands should be run from the project's root directory (e.g., `YuLan-OneSim/`).

### Global Setup: Model Configuration

Both `env_design.py` and `report_generation.py` load LLM configurations from a JSON file. You need to specify the path to this file and the desired model configuration name from within that file.

-   **`--model_config <path_to_config.json>`**: This argument tells the scripts where to find your model configuration file. All paths are relative to the project root.
    -   For `env_design.py`: Defaults to `config/model_config.json`.
    -   For `report_generation.py`: If not provided, it first tries `config/model_config.json`, then falls back to `src/researcher/test/my_model_config.json`.
-   **`--model_name <model_name_from_json>`**: This argument specifies which configuration *within* the JSON file to use (e.g., `gpt-4o`).

### 1. Experimental Design (Natural Language -> ODD & Environment)

Use `src/researcher/env_design.py` to generate an ODD protocol and environment structure from a research topic.

**Command-Line Example:**
```bash
python src/researcher/env_design.py \
    --topic "Investigating the spread of misinformation in online social networks" \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    --save
```
-   `--topic <string>`: (Required) The initial research topic.
-   `--scene_name <string>`: (Optional) Desired name for the environment directory (e.g., "misinformation_spread"). If not provided, one will be generated. This will be created under `src/envs/`.
-   `--model_config <path>`: (Optional) Path to your model configuration JSON file. Defaults to `config/model_config.json`.
-   `--model_name <string>`: (Optional, but usually needed) The `config_name` from your model JSON to use for LLM agents.
-   `--save`: (Optional) Save intermediate outputs from each agent.
-   `--assess`: (Optional) After generation, run an assessment on the created ODD protocol. If used without `--topic`, it attempts to assess an existing scene specified by `--scene_name`.

**Python API Example:**
```python
from pathlib import Path
from src.researcher.env_design import Coordinator
from src.onesim.models import get_model_manager

# Setup model manager (assuming project root is current dir or script is adjusted)
project_root = Path.cwd() # Or Path(__file__).resolve().parent.parent.parent if structure is fixed
model_config_file = project_root / "config" / "model_config.json"

if not model_config_file.exists():
    print(f"Model config not found at {model_config_file}")
else:
    model_manager = get_model_manager()
    model_manager.load_model_configs(str(model_config_file))

    design_coordinator = Coordinator(
        scene_name="misinformation_spread_api",
        model_name="gpt-4o", # Ensure this config_name exists in your model_config.json
        save_intermediate=True
    )
    # Note: The Coordinator will use the globally configured ModelManager
    detailed_spec = design_coordinator.run("Misinformation spread dynamics")
    # Outputs will be in <project_root>/src/envs/misinformation_spread_api/research/env_design/

    # To assess an existing scene:
    # assessment_results = design_coordinator.assess(scene_name="misinformation_spread_api")
```

### 2. Automated Report Generation (Simulation Data -> PDF)

Use `src/researcher/report_generation.py` to generate a research report for an *existing* simulation environment (scene).

**Prerequisites**: Ensure the target scene directory under `src/envs/<scene_name>/` exists and contains necessary files like `scene_info.json`, and ideally metric data/plots.

**Command-Line (Full Workflow Example):**
```bash
python src/researcher/report_generation.py \
    --scene_name "misinformation_spread" \
    --model_config "config/model_config.json" \
    --model_name "gpt-4o" \
    full \
    --report_title "Analysis of Misinformation Spread Dynamics" \
    --report_author "AI Research Team" \
    --iterations 2
```

**Subcommands for `report_generation.py`**: 
All subcommands require `--scene_name`. Also provide `--model_config` and `--model_name` as needed.

-   **`analyze`**: Performs data analysis.
    ```bash
    python src/researcher/report_generation.py --scene_name "<scene_name>" --model_config "config/model_config.json" --model_name "<model_config_name>" analyze
    ```
    Outputs: `src/envs/<scene_name>/research/analysis_result.md`

-   **`outline`**: Generates a report outline (requires `analysis_result.md` to exist).
    ```bash
    python src/researcher/report_generation.py --scene_name "<scene_name>" --model_config "config/model_config.json" --model_name "<model_config_name>" outline
    ```
    Outputs: `src/envs/<scene_name>/research/report_outline.md`

-   **`report`**: Generates a report. By default, it assumes analysis and outline steps are done (i.e., `--skip_analysis` and `--skip_outline` are effectively true). It will perform review iterations.
    ```bash
    python src/researcher/report_generation.py --scene_name "<scene_name>" --model_config "config/model_config.json" --model_name "<model_config_name>" report \
                                             --report_title "My Report" --iterations 3
    ```

-   **`full`**: Executes the complete pipeline: analysis -> outline -> report with iterations.
    ```bash
    python src/researcher/report_generation.py --scene_name "<scene_name>" --model_config "config/model_config.json" --model_name "<model_config_name>" full \
                                             --report_title "Full Workflow Report" \
                                             --iterations 3 \
                                             # --skip_analysis (optional, defaults to false for full)
                                             # --skip_outline (optional, defaults to false for full)
                                             # --skip_review (optional)
    ```
    Outputs: Files in `src/envs/<scene_name>/research/report/`, including `simulation_report_final.pdf`.

-   **`review`**: Reviews an existing LaTeX report.
    ```bash
    python src/researcher/report_generation.py --scene_name "<scene_name>" --model_config "config/model_config.json" --model_name "<model_config_name>" review \
                                             --latex_file "src/envs/<scene_name>/research/report/simulation_report_iter1.tex"
    ```

**Common Optional Arguments for `full` and `report` subcommands:**
-   `--report_title <string>`: Title for the report. Defaults to a formatted scene name.
-   `--report_author <string>`: Author(s). Defaults to "AI Social Researcher".
-   `--iterations <int>`: Number of review-and-revision iterations (default: 3 for `full` and `report`).
-   `--skip_review`: Skip the review and iterative improvement process.
-   `--skip_analysis` (for `full`): Skip data analysis, use existing results. (Defaults to `true` for `report` subcommand).
-   `--skip_outline` (for `full`): Skip outline generation, use existing results. (Defaults to `true` for `report` subcommand).
