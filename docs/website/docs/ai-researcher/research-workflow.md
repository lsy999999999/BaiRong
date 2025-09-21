---
sidebar_position: 2
title: Research Workflow
---

# Research Workflow

The `AI Social Researcher` toolkit abstracts the complex social simulation research process into two main stages, forming an automated closed loop from inspiration to report. Understanding this workflow is key to using this tool effectively.

---

## Overall Workflow Diagram

The entire workflow begins with a simple natural language idea and ends with a formal PDF research report.

**Research Idea (Natural Language)**
> "I want to study the impact of social media on political polarization."

⬇

### **Stage 1: Environment Design**
* **Goal**: To make an abstract idea concrete and standardized.
* **Process**:
    1.  **Inspiration**: An LLM Agent generates multiple potential, more specific research questions and scenarios based on the initial topic.
    2.  **Evaluation & Selection**: Another Agent assesses these scenarios for their scientific value, feasibility, and novelty, then selects the best option.
    3.  **Detailing**: A core Agent expands the selected scenario into a complete **ODD (Overview, Design Concepts, Details) protocol**. The ODD protocol is a standard document in the field of social simulation that precisely describes the simulation's purpose, entities, processes, and scheduling.
    4.  **Environment Setup**: Based on the ODD protocol, the system automatically creates a new scene folder, `<scene_name>`, in the `src/envs/` directory and generates core configuration files like `scene_info.json` (which contains the ODD protocol in JSON format).
* **Output**: A structured, standardized simulation environment folder, ready for the subsequent simulation experiment.
* **Details**: [Environment Design Documentation](<./environment-design.md>)

⬇

**(Intermediate Step: User Runs the Simulation)**
> In this step, the user needs to use the environment configuration generated in Stage 1 to run the actual social simulation program. `AI Social Researcher` **does not execute** the simulation itself but handles the work before and after the simulation. The simulation process should produce quantitative metrics and visual plots.

⬇

### **Stage 2: Report Generation**
* **Goal**: To consolidate scattered simulation data and plots into a coherent, professional academic report.
* **Process**:
    1.  **Data Analysis**: An LLM Agent reads the ODD protocol from `scene_info.json`, the metric calculation logic from `metrics.py`, and all the plots in the `metrics_plots/` directory to perform a comprehensive analysis of the simulation results, extracting key findings and insights.
    2.  **Outline Construction**: Based on the insights from the analysis, the Agent generates a logically clear report outline, covering standard sections like Introduction, Methods, Results, and Discussion.
    3.  **Report Writing & Compilation**: The system fills in the content chapter by chapter according to the outline, compiling the text, plots, and methodological descriptions from the ODD protocol into a complete LaTeX draft.
    4.  **(Optional) Review & Iteration**: A `ReviewerAgent` can, like a peer reviewer, check the draft report for clarity, logic, and completeness, and provide suggestions for revision. The system automatically modifies the report based on these suggestions, a process that can be repeated multiple times to continuously improve the report's quality.
* **Output**: A `simulation_report_final.pdf` file stored in the `research/report/` directory.
* **Details**: [Report Generation Documentation](<./report-generation.md>)

---

Through these two stages, `AI Social Researcher` achieves an automated leap from a vague concept to a polished report.

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
