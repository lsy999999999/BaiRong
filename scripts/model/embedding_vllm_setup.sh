#!/bin/bash

set -e

# Default values for model path and port
model_name_or_path="openai/gpt-3.5-turbo"  # Default model path (can be replaced with a different model)
port=9890

# Parsing command line arguments
while getopts "m:p:" flag; do
    case "${flag}" in
        m) model_name_or_path=${OPTARG};;  # Set the model path
        p) port=${OPTARG};;  # Set the port
        *) echo "Usage: $0 [-m model_name_or_path] [-p port]" && exit 1;;
    esac
done

# Set the GPU ID for CUDA
export CUDA_VISIBLE_DEVICES=7  # Using GPU 7

# Log file path
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${current_dir}/vllm_embedding.log"

# Write startup information to the log file
{
    echo "===== [Launching vLLM Embedding API Server] ====="
    echo "Time: $(date)"
    echo "Model Path: $model_name_or_path"
    echo "Port: $port"
    echo "GPU ID: $CUDA_VISIBLE_DEVICES"
    echo "==================================="
} >> "$LOG_FILE" 2>&1

# Check if the specified port is already in use
if lsof -i ":$port" > /dev/null 2>&1; then
    echo "❌ Error: Port $port is already in use. Aborting." | tee -a "$LOG_FILE"
    exit 1
fi

# Build the command to start the vLLM server with embedding task
cmd="python3 -m vllm.entrypoints.openai.api_server"
cmd+=" --model \"$model_name_or_path\""
cmd+=" --port \"$port\""
cmd+=" --task embedding"
cmd+=" --dtype auto"  # Automatically determine data type
cmd+=" --pipeline-parallel-size 1"  # Disable pipeline parallelism for single-device use
cmd+=" --trust-remote-code"  # Trust remote code for custom models
cmd+=" --seed 42"  # Set random seed for reproducibility
cmd+=" --disable-log-requests"  # Disable logging of API requests
cmd+=" --disable-frontend-multiprocessing"  # Disable frontend multiprocessing for simplicity
cmd+=" --gpu-memory-utilization 0.9"  # Set GPU memory utilization to 90%

# Start the server and log the command
echo "Starting server with command:" >> "$LOG_FILE"
echo "$cmd" >> "$LOG_FILE"
eval "$cmd" >> "$LOG_FILE" 2>&1 &
launcher_pid=$!

# Wait for the server to initialize
sleep 5

# Capture the actual server PID
server_pid=$(pgrep -P "$launcher_pid" -f "vllm.entrypoints.openai.api_server" | head -n 1)

if [ -z "$server_pid" ]; then
    echo "❌ Error: vLLM Server process not found. Check log: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# Save the actual API server PID
echo "$server_pid" >> "$current_dir/vllm_server.pid"

# Success message
echo "✅ vLLM Embedding API server is running on port $port with PID $server_pid" >> "$LOG_FILE"
echo "Started successfully! (Log: $LOG_FILE, PID file: $current_dir/vllm_embedding.pid)"
