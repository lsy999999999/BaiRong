# OneSim Scripts Guide

This directory contains various scripts for running the OneSim system.

## Basic Run Script

### `run.sh`

Basic script to run the OneSim system in single-node mode.

```bash
bash scripts/run.sh
```

Uses `config/config.json` as the configuration file and `config/model_config.json` as the model configuration file by default, running the labor market matching process simulation environment.

## Distributed Run Scripts

### `distributed/distributed.sh`

Used to start the OneSim system in distributed mode, including one master node and multiple worker nodes.

```bash
bash scripts/distributed/distributed.sh [options]
```

**Options:**
- `-a, --address MASTER_ADDRESS` - Master node address (default: 127.0.0.1)
- `-p, --port MASTER_PORT` - Master node port (default: 10051)
- `-w, --workers NUM_WORKERS` - Number of worker nodes (default: 2)
- `-c, --config CONFIG_PATH` - Configuration file path (default: config/config.json)
- `-m, --model MODEL_CONFIG_PATH` - Model configuration file path (default: config/model_config.json)
- `-h, --help` - Display help information

The script will start one master node and the specified number of worker nodes, with all logs saved in the `logs/` directory.

### `distributed/kill_distributed.sh`

Used to stop all OneSim processes running in distributed mode.

```bash
bash scripts/distributed/kill_distributed.sh
```

## Model Service Scripts

### `model/launch_llm.sh`

Start a single LLM server using vLLM as the backend.

```bash
bash scripts/model/launch_llm.sh <port> <GPU_ID> <model_path> [lora_dir]
```

**Parameters:**
- `port` - Port for the API server to listen on
- `GPU_ID` - GPU ID to use
- `model_path` - Path to the large language model
- `lora_dir` - (Optional) Directory for LoRA parameters

### `model/launch_all_llm.sh`

Start multiple LLM servers simultaneously, allocated to different GPUs.

```bash
bash scripts/model/launch_all_llm.sh
```

By default, uses ports 9881-9888 and GPUs 0-7 to start 8 Qwen2.5-7B-Instruct model servers.
To modify the configuration, edit the `port_list`, `gpu_list`, and `model_path` variables in the script.

### `model/kill_llm.sh`

Stop all running LLM servers.

```bash
bash scripts/model/kill_llm.sh
```

### `model/embedding_vllm_setup.sh`

Set up vLLM service for embeddings.

```bash
bash scripts/model/embedding_vllm_setup.sh
```
