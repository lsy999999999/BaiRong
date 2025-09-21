---
sidebar_position: 3
---

# Scenario Structure

Understanding the structure of a scenario is crucial for both using and customizing simulations. All scenarios reside within the `src/envs` directory. Here, we'll use the `labor_market_matching_process` scenario as an example to break down the typical structure.

## Example: `labor_market_matching_process`

A scenario directory is organized as follows:

```
labor_market_matching_process/
├── __init__.py
├── actions.json
├── code/
│   ├── __init__.py
│   ├── Employer.py
│   ├── JobSeeker.py
│   ├── RecruitmentChannel.py
│   ├── SimEnv.py
│   └── ...
├── env_data.json
├── events/
├── log/
├── metrics_plots/
├── profile/
│   ├── data/
│   │   ├── Employer.json
│   │   └── JobSeeker.json
│   └── schema/
│       ├── Employer.json
│       └── JobSeeker.json
└── scene_info.json
```

### Key Directories and Files

- **`__init__.py`**: Makes the scenario directory a Python package.
- **`actions.json`**: Defines the actions available to agents in the scenario.
- **`code/`**: Contains the core logic of the simulation.
    - `SimEnv.py`: Implements the main environment class, controlling the simulation's flow and rules.
    - `Employer.py`, `JobSeeker.py`: Define the different types of agents in the scenario. Each file implements an agent's behavior, state, and interactions.
    - `metrics/metrics.py`: Defines the metrics of the scenario.
- **`env_data.json`**: Stores environment-specific settings and initial state data.
- **`events/`**: Contains event logs from previous simulation runs.
- **`log/`**: Stores logs generated during scenario creation and execution for debugging purposes.
- **`metrics_plots/`**: Saves the output of the simulation, including metric data (JSON) and visualizations (PNG), often organized by rounds or steps.
- **`profile/`**: Holds the data and schemas for the agents and other entities in the scenario.
    - **`data/`**: Contains JSON files with the actual data for populating agents (e.g., a list of job seekers with their attributes).
    - **`schema/`**: Contains JSON schema files that define the structure and data types for the profiles.
- **`scene_info.json`**: A metadata file containing a description, name, and other information about the scenario.
