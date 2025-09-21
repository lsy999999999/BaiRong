---
sidebar_position: 4
title: CLI Command Reference
---

# CLI Command Reference

Command line tool usage instructions for YuLan-OneSim.

## Examples

### Quick Start

```bash
# Run a simulation with default settings
yulan-onesim-cli --config config/config.json --model_config config/model_config.json --mode single --env labor_market_matching_process
```

### Distributed Mode Example

#### 1. Start the Master node
```bash
yulan-onesim-cli --config config/config.json --model_config config/model_config.json --mode master --expected_workers 2 --env labor_market_matching_process
```

#### 2. Start the Worker node (assuming the master is at 192.168.1.100:50051)
```bash
yulan-onesim-cli --config config/config.json --model_config config/model_config.json --mode worker --master_address 192.168.1.100 --master_port 50051 --env labor_market_matching_process
```

**Or you can ...**

#### 3. Start distributed mode in one command

```
# Use the distributed script to launch master + 2 workers in one step
bash scripts/distributed/distributed.sh \
  --address 127.0.0.1 \
  --port 10051 \
  --workers 2 \
  --config config/config.json \
  --model config/model_config.json
```

> Note：
> - When running in distributed mode, start the master node first, then the worker nodes.
> - `--master_address` and `--master_port` must match the actual master node’s address and port.

## Configuration Options

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--config` | `str` |  ✅| — | PPath to the configuration file. |
| `--model_config` | `str` | ✅  | — | Model configuration file. |
| `--env` | `str` | — | None | Simulation environment. |
| `--mode` | `str` | — | `single` | Operating mode: single, master, or worker. |
| `--master_address` | `str` | — | `localhost` | Address of the master node. |
| `--master_port` | `int` | — | `50051` | Master node port. |
| `--worker_address` | `str` | — | None | Worker node address (for master mode) |
| `--worker_port` | `int` | — | `0` | Worker node port (0 for auto-assign) |
| `--node_id` | `str` | — | auto | Node identifier (generated if not provided) |
| `--expected_workers` | `int` | — | `1` | Number of worker nodes to wait for (for master mode) |
| `--enable_db` | `flag` | — | `False` | Enable database component. |
| `--enable_observation` | `flag` | — | `False` |Enable observation system. |

## Script Explanations

| Script                                  | Main Function Description                                                      |
|-----------------------------------------|---------------------------------------------------------------------------------|
| `scripts/run.sh`                          | Quickly run a simulation (typically single-node / for testing)                  |
| `scripts/distributed/distributed.sh`      | Launch distributed simulation environment (auto-manage master/worker)           |
| `scripts/distributed/kill_distributed.sh` | Terminate distributed simulation processes                                      |
| `scripts/model/launch_llm.sh`             | Launch the LLM (large language model) service                                   |
| `scripts/model/kill_llm.sh`               | Terminate the LLM service                                                       |
| `scripts/model/launch_all_llm.sh`         | Launch all LLM services                                                         |
| `scripts/model/embedding_vllm_setup.sh`   | Launch/configure the embedding vLLM service                                     |

### `run.sh`

#### Usage

```bash
bash scripts/run.sh
```

#### Process overview

Launch directly with default settings

#### Use cases

* Rapid local iterations of the full simulation flow



### `scripts/distributed/distributed.sh`

#### Usage

```bash
bash scripts/distributed/distributed.sh [options]
```

#### Optional variables

`--address, -a`: Master address (default `127.0.0.1`)\
`--port, -p`: Master port (default `10051`)\
`--workers, -w`: Number of worker nodes (default `2`)\
`--config, -c`: Path to the global configuration file\
`--model, -m`: Path to the model configuration file\
`--help, -h`: Show help message

#### Process overview

1. Parse command-line arguments to override defaults.
2. Print startup summary (master address, port, config paths, worker count).
3. Create `logs/` directory if missing.
4. Launch the master node.
5. Wait briefly (`sleep 2`) for the master node to initialize.
6. Loop through workers (0 to `NUM_WORKERS-1`).
7. Print process IDs for master and workers, and suggest monitoring commands.

#### Use cases

* Running large-scale simulations requiring parallel computation.


### `scripts/distributed/kill_distributed.sh`

#### Usage

```bash
bash scripts/distributed/kill_distributed.sh [options]
```

#### Optional variables

`--graceful, -g`: Use SIGTERM instead of SIGKILL for graceful termination (default: SIGKILL)
`--show-only, -s`: List processes without killing them (default: false)
`--help, -h`: Show help message

#### Process overview

1. Parse command-line arguments (`--graceful`, `--show-only`, `--help`).
2. Locate OneSim master and worker processes using `pgrep`.
3. Display found processes with `ps`.
4. Count total processes; if `--show-only`, report counts and exit.
5. Prompt user for confirmation to kill processes.
6. Send specified signal (`SIGKILL` or `SIGTERM`) to each worker, then master process.
7. Report the number of killed processes.
8. Pause briefly and verify no remaining OneSim processes are running.

#### Use cases

* Quickly terminate all running OneSim simulations in bulk.
* Perform a dry-run to review processes before killing.

### `scripts/model/launch_llm.sh`

#### Usage

```bash
bash scripts/model/launch_llm.sh <port> <gpu_id> <model_path> [lora_dir]
```

#### Required arguments

`<port>`: Port to host the vLLM API server on
`<gpu_id>`: CUDA device ID for `CUDA_VISIBLE_DEVICES`
`<model_path>`: Path to the LLM model directory or file

#### Optional Variables:

`[lora_dir]`: Optional directory for LoRA adapters

#### Process overview

1. Exit on errors (`set -e`).
2. Validate that at least three positional arguments are provided; exit with usage if not.
3. Assign input arguments to `port`, `gpuid`, `model_path`, and optional `lora_dir`.
4. Export environment variables:
   * `CUDA_VISIBLE_DEVICES` set to `gpuid`.
   * `VLLM_ATTENTION_BACKEND` set to `XFORMERS` for memory-efficient inference.
5. Determine script directory (`current_dir`), define `LOG_FILE` and `PID_FILE` in that directory.
6. Append startup metadata (timestamp, port, GPU ID, model path, LoRA directory if provided) to `llms.log`.
7. Check port availability using `lsof`; abort with an error if the port is in use.
8. Construct the vLLM server command (`python -m vllm.entrypoints.openai.api_server`) with flags for model, port, dtype, pipeline parallelism, caching, decoding backend, tokenizer mode, seed, request logging, multiprocessing, and GPU memory utilization.
9. If `lora_dir` is provided or an `adapter_config.json` exists in `model_path`, enable LoRA flags in the command.
10. Launch the constructed command in the background, redirecting output to the log file; capture the launcher PID.
11. Sleep for 5 seconds to allow the server to initialize.
12. Identify the actual server PID by searching for the child process of the launcher.
13. Record the server PID in `llms.pid`.
14. Log a successful startup message with port and PID.

#### Use cases

* Deploy a vLLM-based API server on a specific GPU for development or testing.
* Integrate optional LoRA adapters for fine-tuning experiments.

### `scripts/model/kill_llm.sh`

#### Usage

```bash
bash scripts/model/kill_llm.sh
```

#### Process overview

1. Exit immediately on any error (`set -e`).
2. Determine the script directory (`current_dir`), and define `PID_FILE` and `LOG_FILE` within it.
3. If the PID file does not exist, report and exit (nothing to stop).
4. Read each PID from `llms.pid`:
   * If the process is running, send `SIGKILL` to terminate it.
   * Report if any PID is not found.
5. Remove the PID file and log file to clean up.
6. Confirm that all vLLM servers have been stopped.

#### Use cases

* Clean up after testing or development runs of vLLM servers.

### `scripts/model/launch_all_llm.sh`

#### Usage

```bash
bash scripts/model/launch_all_llm.sh
```

#### Process overview

1. Determine the script directory (`script_dir`).
2. Define the arrays:
   * `port_list`: list of ports to use (e.g., 9881–9888).
   * `gpu_list`: corresponding GPU IDs for each server (0–7).
   * `model_path`: path to the pretrained model directory.
3. Loop over each index of `port_list`:
   * Extract `port` and `gpu_id` by index.
   * Invoke `launch_llm.sh` with `port`, `gpu_id`, and `model_path` in the background.
4. Use `wait` to block until all background server processes have started.
5. Print a confirmation message once all LLM API servers are running.

#### Use cases

* Concurrently launch a fleet of LLM API servers across multiple GPUs and ports.

### `scripts/model/embedding_vllm_setup.sh`

#### Usage

```bash
bash scripts/model/embedding_vllm_setup.sh [-m model_name_or_path] [-p port]
```

#### Optional variables

`-m`: Model name or path (default: `openai/gpt-3.5-turbo`)
`-p`: Port to host the embedding API server (default: `9890`)

#### Process overview

1. Exit on errors (`set -e`).
2. Parse flags using `getopts`:
   * `-m` for `model_name_or_path`.
   * `-p` for `port`.
3. Export `CUDA_VISIBLE_DEVICES=7` to use GPU 7.
4. Determine script directory and set `LOG_FILE` and PID file paths.
5. Append startup metadata (timestamp, model path, port, GPU ID) to the log file.
6. Check port availability with `lsof`; abort if in use.
7. Construct the vLLM embedding server command (`python3 -m vllm.entrypoints.openai.api_server`) with flags for embedding task, dtype, parallelism, remote code trust, seed, request logging, multiprocessing, and GPU memory utilization.
8. Launch the server in the background, logging output to `vllm_embedding.log`; capture the launcher PID.
9. Wait briefly (`sleep 5`) for initialization.
10. Identify the actual server PID and write it to `vllm_embedding.pid`.
11. Log and echo a success message with port and PID.

#### Use cases

* Serve embedding requests via the vLLM API for downstream vectorization tasks.
* Experiment with different LLM-backed embedding models on a dedicated GPU.

