---
sidebar_position: 3
title: Tuning Process
---

# Tuning Process

Once your data is ready, you can start the LLM fine-tuning process in two ways: directly using the command line or by calling the corresponding function in your Python code.

## Method 1: Launch via Command Line

The command line is the most convenient method for quick experiments and automated scripts.

**Basic Command Format**:

```bash
python codes/tune_llm.py --llm_path [MODEL_PATH] --dataset_path [DATASET_PATH] --tuning_mode [MODE]
```

**Parameter Details**:

| Parameter | Description | Default Value |
| :--- | :--- | :--- |
| `--tuning_mode` | Fine-tuning mode. Options are `"sft"` or `"ppo"`. | `"sft"` |
| `--llm_path` | Path to the base model (Hugging Face format). | **(Required)** |
| `--dataset_path` | Path to the JSON file containing the training data. | **(Required)** |
| `--experiment_name` | The name for this experiment displayed in MLflow. | `"llm_tuning"` |
| `--tracking_uri` | The URI for the MLflow server. | `"./mlruns"` |
| `--devices` | Specifies the CUDA device IDs to use. Separate multiple devices with a comma (e.g., `"0,1"`). | `"0"` |

**Examples**:

```bash
# Fine-tune using SFT mode
python codes/tune_llm.py \
    --llm_path /path/to/your/model \
    --dataset_path /path/to/dataset.json \
    --tuning_mode sft \
    --experiment_name "sft_experiment_1"

# Fine-tune using PPO mode and run on specified GPUs
python codes/tune_llm.py \
    --llm_path /path/to/your/model \
    --dataset_path /path/to/ppo_data.json \
    --tuning_mode ppo \
    --devices "0,1"
```

## Method 2: Invoke via Python Code

If you need to integrate the fine-tuning functionality into more complex applications, you can directly import and call the `run_tuning` function.

**Function Import**:

```python
from llm_tuning.codes.tune_llm import run_tuning
```

**Usage Examples**:

```python
# 1. SFT fine-tuning with minimal parameters
run_tuning(
    tuning_mode="sft",
    llm_path="/path/to/your/model",
    dataset_path="/path/to/dataset.json"
)

# 2. PPO fine-tuning with all custom parameters
run_tuning(
    tuning_mode="ppo",
    llm_path="/path/to/your/model",
    dataset_path="/path/to/ppo_data.json",
    experiment_name="custom_ppo_experiment",
    tracking_uri="http://localhost:5000",
    devices="0,1"
)
```

## Post-Training Artifacts

When the fine-tuning task is complete, the system automatically handles the following:

1.  **Save Model Adapter**: The trained LoRA adapter weights are saved to the `models/<model_id>/` directory, where `<model_id>` is a unique identifier generated for the training run.
2.  **Register Model**: Information about the newly trained model is automatically added to the model registry file, `models/registry.json`, for unified management and subsequent deployment.
3.  **Log to MLflow**: All hyperparameters, performance metrics, and artifact paths from the training process are logged in MLflow. For details, please refer to the [Evaluation Methods](<./evaluation.md>) page.

## Deploying the Fine-Tuned Model

You can use the `launch_llm.sh` script to load the base model and the fine-tuned LoRA adapter to launch an inference service.

**Deployment Command**:

```bash
bash config/llm/launch_llm.sh <port> <gpu_id> <model_path> [lora_path]
```

  - `port`: Service port number.
  - `gpu_id`: GPU device ID to use.
  - `model_path`: Path to the base model.
  - `lora_path`: (Optional) Path to the LoRA adapter generated after fine-tuning.

