---
sidebar_position: 3
title: Tuning Process
---

# 执行模型微调 (Tuning Process)

准备好数据后，您可以通过两种方式启动 LLM 微调流程：直接使用命令行或在 Python 代码中调用相应函数。

## 方式一：通过命令行启动

对于快速实验和自动化脚本，命令行是最便捷的方式。

**基础命令格式**：

```bash
python codes/tune_llm.py --llm_path [模型路径] --dataset_path [数据集路径] --tuning_mode [模式]
````

**参数详解**：

| 参数 | 描述 | 默认值 |
| :--- | :--- | :--- |
| `--tuning_mode` | 微调模式，可选值为 `"sft"` 或 `"ppo"`。 | `"sft"` |
| `--llm_path` | 基础模型的路径（Hugging Face 格式）。 | **（必需）** |
| `--dataset_path` | 指向包含训练数据的 JSON 文件的路径。 | **（必需）** |
| `--experiment_name` | 本次实验在 MLflow 中显示的名称。 | `"llm_tuning"` |
| `--tracking_uri` | MLflow 服务器的 URI 地址。 | `"./mlruns"` |
| `--devices` | 指定使用的 CUDA 设备 ID，多个设备用逗号分隔（例如 `"0,1"`）。 | `"0"` |

**示例**：

```bash
# 使用 SFT 模式微调
python codes/tune_llm.py \
    --llm_path /path/to/your/model \
    --dataset_path /path/to/dataset.json \
    --tuning_mode sft \
    --experiment_name "sft_experiment_1"

# 使用 PPO 模式并在指定 GPU 上运行
python codes/tune_llm.py \
    --llm_path /path/to/your/model \
    --dataset_path /path/to/ppo_data.json \
    --tuning_mode ppo \
    --devices "0,1"
```

## 方式二：通过 Python 代码调用

如果您需要将微调功能集成到更复杂的应用中，可以直接导入并调用 `run_tuning` 函数。

**函数导入**：

```python
from llm_tuning.codes.tune_llm import run_tuning
```

**调用示例**：

```python
# 1. 使用最简参数进行 SFT 微调
run_tuning(
    tuning_mode="sft",
    llm_path="/path/to/your/model",
    dataset_path="/path/to/dataset.json"
)

# 2. 自定义所有参数进行 PPO 微调
run_tuning(
    tuning_mode="ppo",
    llm_path="/path/to/your/model",
    dataset_path="/path/to/ppo_data.json",
    experiment_name="custom_ppo_experiment",
    tracking_uri="http://localhost:5000",
    devices="0,1"
)
```

## 训练完成后的产物

当微调任务执行完毕后，系统会自动处理以下事项：

1.  **保存模型适配器**：训练得到的 LoRA 适配器（Adapter）权重会被保存到 `models/<model_id>/` 目录下，其中 `<model_id>` 是本次训练生成的唯一标识。
2.  **注册模型**：新训练好的模型信息会被自动添加到模型注册表 `models/registry.json` 中，方便统一管理和后续部署。
3.  **记录到 MLflow**：整个训练过程的超参数、性能指标和产物路径都会被记录在 MLflow 中，详情请参考 [评估与跟踪实验](<./evaluation.md>) 页面。

## 部署微调后的模型

您可以使用 `launch_llm.sh` 脚本来加载基础模型和微调后的 LoRA 适配器，以启动一个推理服务。

**部署命令**：

```bash
bash config/llm/launch_llm.sh <port> <gpu_id> <model_path> [lora_path]
```

  - `port`: 服务端口号。
  - `gpu_id`: 使用的 GPU 设备 ID。
  - `model_path`: 基础模型的路径。
  - `lora_path`: （可选）微调后生成的 LoRA 适配器路径。

