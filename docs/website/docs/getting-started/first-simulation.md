---
sidebar_position: 3
title: First Simulation
---

# Your First Simulation

15-minute quick experience tutorial to get you started with YuLan-OneSim.

## Prerequisites

- Node.js 18+ (for frontend, if running locally)
- For full LLM features, valid API keys or local LLM deployment are required.
- (Optional)  For distributed or database features: PostgreSQL (if enabled in config)

Or

- (Optional) Docker installed for one-command deployment

## Configure Model Settings

Before running your first simulation, you need to configure the models in `config/model_config.json`. This file specifies which LLMs and embedding models the simulator will use.

**Essential fields you must configure:**

- **Chat models**: At minimum, configure one chat model with:
  - `provider`: The LLM provider (e.g., "openai", "vllm")
  - `config_name`: A unique identifier for this model configuration
  - `model_name`: The specific model to use
  - `api_key`: Your API key (for cloud providers like OpenAI)

- **Embedding models**: Configure at least one embedding model with:
  - `provider`: The embedding backend type(e.g., "openai", "vllm")
  - `config_name`: A unique identifier for this embedding configuration
  - `model_name`: The embedding model to use
  - `api_key`: Your API key (for cloud providers like OpenAI)

For detailed configuration options and examples, see the [Model Configuration Guide](../configuration/model-config.md).

## Run a Simulation: Two Options

### CLI mode

```bash
# Run a simulation with default settings
yulan-onesim-cli --config config/config.json --model_config config/model_config.json --mode single --env labor_market_matching_process
```

### Web Interface

Start the backend API:

```bash
yulan-onesim-server
```

In a new terminal, start the frontend:

```bash
cd src/frontend
npm install
npm run dev
```

Alternatively, if you have Docker installed, you can run the entire application with a single command.

Use the `make run` command:
```bash
make run
```

Or, use the `docker run` command directly:
```bash
docker run -d --name yulan-onesim -p 8000:80 -v ./config:/app/config ptss/yulan-onesim:latest
```

### Understanding the Results

- The simulation output will be shown in the terminal (CLI) or on the web interface.
- You can explore agent behaviors, scenario logs, and visualizations.