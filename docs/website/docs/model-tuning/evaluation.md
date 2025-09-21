---
sidebar_position: 4
title: Evaluation Methods
---

# Evaluation Methods

To systematically manage and compare the results of different fine-tuning experiments, we have integrated MLflow as an experiment tracking tool. MLflow provides a powerful visual interface that allows you to clearly monitor and analyze the training process.

## Training Results and Metrics

During the training process, key metrics (such as `loss`, `reward`, etc.) are automatically logged. After training is complete, you can view the change curves of these metrics in the MLflow interface to evaluate the model's convergence and performance.

## MLflow Configuration and Startup

Before you begin, you need to configure and start an MLflow tracking server.

### Step 1: Set Environment Variables (Optional)

If you want to send logs to a remote server instead of locally, you can set the following environment variable.

```bash
# Set the address of the MLflow tracking server
export MLFLOW_TRACKING_URI=http://localhost:5000
```

If this is not set, it will default to using the local file system path `./mlruns`.

### Step 2: Start the MLflow Service

For the best experience, it is recommended to start a standalone MLflow service.

```bash
# Start a local MLflow server
mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --default-artifact-root ./mlruns
```

  - `--default-artifact-root`: Specifies a location to store training artifacts (such as model files, logs, etc.).

### Step 3: View Experiment Results

Once the service has started, open `http://localhost:5000` in your browser.

In the MLflow UI, you can perform the following actions:

  - ✅ **View All Experiments**: Find the experiments you specified with the `--experiment_name` parameter in the left-hand navigation bar.
  - 📊 **Compare Multiple Runs**: Check the boxes for multiple runs under the same experiment and click the "Compare" button to see a side-by-side comparison of their parameters and metrics.
  - 📈 **Analyze Metric Curves**: Click on a specific run to view detailed charts of how metrics like `loss` and `reward` change with the training steps.
  - 📦 **Download Model Artifacts**: In the "Artifacts" section of a run's detail page, you can find and download the saved model adapters.

By effectively using MLflow, you can systematically optimize hyperparameters, compare different fine-tuning strategies, and ultimately select the best-performing model.

