# LLM Tuning

This project provides tools for fine-tuning large language models. It supports two modes: SFT (Supervised Fine-Tuning) and PPO (Proximal Policy Optimization).

## How to Use

### Direct Execution

You can run the fine-tuning program directly from the command line:

```bash
python codes/tune_llm.py --llm_path /path/to/your/model --tuning_mode sft --dataset_path /path/to/dataset.json
```

Parameter descriptions:
- `--tuning_mode`: Fine-tuning mode, options are "sft" or "ppo", defaults to "sft"
- `--llm_path`: Path to the base model
- `--dataset_path`: Path to the dataset, pointing to the collected decision data JSON file
- `--experiment_name`: MLflow experiment name, defaults to "llm_tuning"
- `--tracking_uri`: MLflow tracking URI, defaults to "./mlruns"
- `--devices`: CUDA devices to use, defaults to "0"

### Calling from Other Code

In other Python code, you can call the `run_tuning` function by importing it:

```python
from llm_tuning.codes.tune_llm import run_tuning

# Use default parameters
run_tuning(tuning_mode="sft", llm_path="/path/to/your/model", dataset_path="/path/to/dataset.json")

# Customize all parameters
run_tuning(
    tuning_mode="ppo",
    llm_path="/path/to/your/model",
    dataset_path="/path/to/dataset.json",
    experiment_name="custom_experiment",
    tracking_uri="./custom_mlruns",
    devices="0,1"
)
```

## Data Preparation Process

### Data Collection
The system automatically collects decision data from the simulation environment and saves it to a unified location:
- Path: `src/envs/<env_name>/datasets/decisions_<timestamp>.json`
- Format: Contains necessary fields such as prompt, output, and reward.


## Training Results

After training is complete:
1. The model adapter is saved to the `models/<model_id>/` directory.
2. MLflow records the training process and metrics.
3. The model is automatically registered in the model library (`models/registry.json`).

## MLflow Configuration

### 1. Set Environment Variables

```bash
# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000
```

### 2. Start MLflow Server

```bash
# Start local MLflow server
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns
```

### 3. View Experiment Results

Open your browser and go to `http://localhost:5000` to:
- View all experiments and runs
- Compare metrics of different runs
- Download trained models

## Model Deployment

After training, the model can be deployed using the `config/llm/launch_llm.sh` script:

```bash
bash config/llm/launch_llm.sh <port> <gpu_id> <model_path> [lora_path]
```

Parameter descriptions:
- `port`: Server port
- `gpu_id`: GPU device ID
- `model_path`: Model path
- `lora_path`: (Optional) LoRA adapter path
