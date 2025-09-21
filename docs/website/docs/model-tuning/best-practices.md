---
sidebar_position: 5
title: Best Practices
---

# Best Practices

Following these best practices can help you complete your LLM fine-tuning tasks more efficiently and successfully.

## 1. Choose the Right Fine-Tuning Mode

- **Prioritize SFT (Supervised Fine-Tuning)**:
  - **Scenario**: When you have high-quality, "textbook-style" example data (e.g., standard question-answer pairs, instructions with ideal outputs).
  - **Purpose**: To have the model learn specific knowledge, formats, or styles. SFT is a foundational step in building a reliable baseline model.
  - **Recommendation**: Train a solid model with SFT before attempting PPO. A good SFT baseline model is a prerequisite for successful PPO optimization.

- **Use PPO (Proximal Policy Optimization) Appropriately**:
  - **Scenario**: When the definition of "good" is difficult to describe with a static dataset but can be quantified by human expert scores or a model. For example, improving the safety or interestingness of the output, or adhering to complex rules.
  - **Purpose**: To further "polish" the model on top of SFT based on a reward signal, making its output better align with specific preferences.
  - **Recommendation**: PPO's training dynamics are more complex and sensitive to hyperparameters and reward design. Ensure your reward signal is stable and meaningful.

## 2. Manage Experiments Effectively

- **Name Your Experiments**: Always use the `--experiment_name` parameter to give each of your attempts a meaningful name (e.g., `sft-base-model-v1` or `ppo-reward-scaling-test`). This allows you to quickly locate and group experiments in MLflow.
- **Start Simple, Then Scale**: Before running large-scale, lengthy training sessions, first conduct a quick test with a small subset of data (e.g., 10%) to ensure the entire pipeline (data loading, training, saving) is bug-free.
- **Log Key Information**: Although MLflow automatically logs parameters, you can record the "hypothesis" and "conclusion" of each experiment in your code or notes, for example, "Increasing the learning rate caused the model to overfit prematurely."

## 3. Focus on Data Quality

- **Garbage In, Garbage Out**: The upper limit of a model's performance is largely determined by data quality.
- **SFT Data**: Ensure your instructions are clear and diverse, and that the responses are accurate and high-quality. Avoid noise and factual errors in the data.
- **PPO Data**: The `prompt` should be representative and capable of eliciting diverse outputs from the model, so that the reward model can effectively distinguish between good and bad responses.

## 4. Resources and Efficiency

- **Allocate GPUs Wisely**: Use the `--devices` parameter to specify the GPUs you want to use. If you have multiple cards, you can run several experiments in parallel to increase efficiency.
- **Monitor Resource Usage**: During training, use tools like `nvitop` to monitor GPU usage, ensuring that resources are not being wasted or depleted.

