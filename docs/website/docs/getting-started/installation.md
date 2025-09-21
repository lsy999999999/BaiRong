---
sidebar_position: 2
title: Installation Guide
---

# Installation Guide

Detailed installation steps including dependency installation for YuLan-OneSim.

## Quick Installation(Docker Image)

### 🎯 Prerequisites

All you need is Docker:  
- **Windows:** Download [Docker Desktop](https://www.docker.com/products/docker-desktop)  
- **Mac:** Download [Docker Desktop](https://www.docker.com/products/docker-desktop)  
- **Linux:** Run  
  ```bash
  curl -fsSL https://get.docker.com | sh

### ⚡ Quick Start

```bash
# 1. Pull the Docker image
docker pull ptss/yulan-onesim

# 2. Clone the repository and navigate to the directory
git clone https://github.com/RUC-GSAI/YuLan-OneSim
cd YuLan-OneSim

# 3. Configure your settings in the config directory first
# Make sure to set up config/config.json and config/model_config.json

# 4. Start the container with config mounted
docker run -d --name yulan-onesim -p 8000:80 -v ./config:/app/config ptss/yulan-onesim:latest

# 5. Open your browser and go to:
http://localhost:8000
```

> **Important:** Make sure to configure your `config/config.json` and `config/model_config.json` files before starting the Docker container, as the application requires proper configuration to function correctly.

That’s it! 🎉

## Development Installation

```bash
# Clone the repository
git clone https://github.com/RUC-GSAI/YuLan-OneSim
cd YuLan-OneSim

# Install in editable mode
pip install -e .

# Install with tuning dependencies if needed
pip install -e .[tune]
```

## Dependency Management

### Essential dependencies

```txt
aiofiles>=24.1.0
asyncpg>=0.30.0
dataclasses_json>=0.6.7
fastapi>=0.115.12
grpcio>=1.70.0
httpx>=0.28.1
loguru>=0.6.0
matplotlib>=3.10.3
networkx>=3.4.2
numpy>=2.2.5
pandas>=2.2.3
Protobuf>=6.30.2
pydantic>=2.11.4
pyvis>=0.3.2
seaborn>=0.13.2
setuptools>=75.6.0
tqdm>=4.67.1
uvicorn>=0.34.2
faiss-cpu>=1.9.0
pyyaml
openai
volcengine-python-sdk
```

### Extra dependencies for finetuning the LLM
```txt
mlflow
torch==2.6.0
peft>=0.15.1
transformers>=4.51.1
trl>=0.16.0
vllm>=0.8.4
```