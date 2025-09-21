---
sidebar_position: 1
title: Model Tuning Overview
---

# Overview

Welcome to the LLM-Tuning submodule! This module is designed to provide a complete, easy-to-use solution for fine-tuning Large Language Models (LLMs) for simulation processes. Whether you want the model to learn new simulation knowledge or optimize its performance in specific simulation scenarios, this submodule offers powerful support.

## Core Features

- **Multiple Fine-Tuning Modes**: Built-in support for two mainstream fine-tuning techniques to suit different application scenarios:
    - **SFT (Supervised Fine-Tuning)**: Suitable for using high-quality, labeled "instruction-response" datasets to teach the model specific conversational styles, knowledge, or task formats.
    - **PPO (Proximal Policy Optimization)**: Uses reinforcement learning to get reward signals from human expert annotators or evaluation models to further optimize the model's output, making it better align with human preferences or specific goals.

- **Flexible Invocation Methods**:
    - **Command-Line Interface**: Start training tasks with simple commands, facilitating rapid experimentation and script integration.
    - **Python Function Calls**: Can be easily integrated as a library into your existing Python projects for more complex logical control.

- **Automated Workflow**:
    - **Automatic Data Collection**: Seamlessly integrates with the simulation environment to automatically capture decision-making data.
    - **Automatic Results Logging**: Training artifacts (like model adapters) are saved automatically, and experiment metrics are tracked throughout the process with MLflow.
    - **Automatic Model Registration**: Completed models are automatically registered in the model repository for subsequent unified management and invocation.

- **Powerful Experiment Tracking**:
    - **MLflow Integration**: Provides a visual experiment management interface, allowing you to easily compare the metrics, parameters, and results of different training runs.

This series of documents will guide you through the entire process, from data preparation and model fine-tuning to results evaluation and best practices.

