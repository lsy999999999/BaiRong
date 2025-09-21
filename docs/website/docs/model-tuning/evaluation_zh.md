---
sidebar_position: 4
title: Evaluation Methods
---

# 评估与跟踪实验 (Evaluation Methods)

为了系统地管理和比较不同微调实验的效果，我们集成了 MLflow 作为实验跟踪工具。MLflow 提供了一个强大的可视化界面，让您能够清晰地监控和分析训练过程。

## 训练结果与指标

在训练过程中，关键的指标（如损失 `loss`、奖励 `reward` 等）会被自动记录。训练结束后，您可以在 MLflow 界面中查看这些指标的变化曲线，从而评估模型的收敛情况和性能。

## MLflow 配置与启动

在使用之前，您需要配置并启动一个 MLflow tracking server。

### 步骤 1：设置环境变量（可选）

如果您希望将日志发送到远程服务器而不是本地，可以设置以下环境变量。

```bash
# 设置 MLflow tracking server 的地址
export MLFLOW_TRACKING_URI=http://localhost:5000
```

如果未设置，则默认使用本地文件系统路径 `./mlruns`。

### 步骤 2：启动 MLflow 服务

为了获得最佳的体验，建议启动一个独立的 MLflow 服务。

```bash
# 启动一个本地 MLflow 服务器
mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --default-artifact-root ./mlruns
```

  - `--default-artifact-root`: 指定一个位置来存储训练产物（如模型文件、日志等）。

### 步骤 3：查看实验结果

服务启动后，在您的浏览器中打开 `http://localhost:5000`。

在 MLflow UI 中，您可以执行以下操作：

  - ✅ **查看所有实验**：在左侧导航栏找到您通过 `--experiment_name` 参数指定的实验。
  - 📊 **比较多次运行**：勾选同一次实验下的多次运行（Runs），点击 "Compare" 按钮，可以并排比较它们的参数和指标。
  - 📈 **分析指标曲线**：点击进入某一次运行，可以查看 `loss`、`reward` 等指标随训练步数变化的详细图表。
  - 📦 **下载模型产物**：在运行详情页的 "Artifacts" 部分，您可以找到并下载保存的模型适配器。

通过有效地利用 MLflow，您可以系统地优化超参数、比较不同微调策略，并最终选择性能最佳的模型。

