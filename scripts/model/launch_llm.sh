#!/bin/bash

set -e

# --- 参数校验 ---
if [ $# -lt 3 ]; then
    echo "Usage: $0 <port> <gpu_id> <model_path> [lora_dir]"
    exit 1
fi

# --- 参数读取 ---
port="$1"
gpuid="$2"
model_path="$3"
lora_dir="$4"

# --- 环境变量设置 ---
export CUDA_VISIBLE_DEVICES="$gpuid"
export VLLM_ATTENTION_BACKEND="XFORMERS"  # 更省显存，更适合大模型推理

# --- 目录及日志 ---
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${current_dir}/llms.log"
PID_FILE="${current_dir}/llms.pid"

# --- 写入启动日志 ---
{
    echo "===== [Launching LLM Server] ====="
    echo "Time: $(date)"
    echo "Port: $port"
    echo "GPU ID: $CUDA_VISIBLE_DEVICES"
    echo "Model Path: $model_path"
    [ -n "$lora_dir" ] && echo "LoRA Directory: $lora_dir"
    echo "==================================="
} >> "$LOG_FILE" 2>&1

# --- 检查端口是否占用 ---
if lsof -i ":$port" > /dev/null 2>&1; then
    echo "❌ Error: Port $port is already in use. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# --- 构建启动命令 ---
cmd="python -m vllm.entrypoints.openai.api_server"
cmd+=" --model \"$model_path\""
cmd+=" --port \"$port\""
cmd+=" --dtype auto"
cmd+=" --pipeline-parallel-size 1"
cmd+=" --trust-remote-code"
cmd+=" --enable-prefix-caching"
cmd+=" --guided-decoding-backend lm-format-enforcer"
cmd+=" --tokenizer-mode auto"
cmd+=" --seed 42"
cmd+=" --disable-log-requests"
cmd+=" --disable-frontend-multiprocessing"
cmd+=" --gpu-memory-utilization 0.9"

# --- LoRA逻辑判断 ---
if [ -n "$lora_dir" ]; then
    cmd+=" --enable-lora"
    cmd+=" --lora-modules lora=\"$lora_dir\""
elif [ -f "${model_path}/adapter_config.json" ]; then
    echo "Detected adapter_config.json, enabling built-in LoRA." >> "$LOG_FILE"
    cmd+=" --enable-lora"
fi

# --- 启动模型服务 ---
echo "Starting server with command:" >> "$LOG_FILE"
echo "$cmd" >> "$LOG_FILE"
eval "$cmd" >> "$LOG_FILE" 2>&1 &
launcher_pid=$!

# --- 等待服务器初始化 ---
sleep 5

# --- 捕捉真正的 Server PID ---
server_pid=$(pgrep -P "$launcher_pid" -f "vllm.entrypoints.openai.api_server" | head -n 1)

if [ -z "$server_pid" ]; then
    echo "❌ Error: vLLM Server process not found. Check log: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# --- 记录真正的API服务器PID ---
echo "$server_pid" >> "$PID_FILE"

# --- 成功提示 ---
echo "✅ vLLM API server is running on port $port with PID $server_pid" >> "$LOG_FILE"
echo "Started successfully! (Log: $LOG_FILE, PID file: $PID_FILE)"
