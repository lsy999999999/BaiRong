#!/bin/bash

set -e

# --- 基本设置 ---
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${current_dir}/llms.pid"
LOG_FILE="${current_dir}/llms.log"

# --- 检查PID文件是否存在 ---
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️ No PID file found at $PID_FILE. Nothing to stop."
    exit 0
fi

# --- 杀死所有记录的PID ---
echo "🛑 Stopping all running vLLM servers..."
while IFS= read -r pid; do
    if [ -n "$pid" ]; then
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Killing process PID: $pid"
            kill -9 "$pid" && echo "✅ Process $pid terminated."
        else
            echo "⚠️ PID $pid not found, maybe already exited."
        fi
    fi
done < "$PID_FILE"

# --- 清理文件 ---
rm -f "$PID_FILE"
echo "🗑️ PID file removed: $PID_FILE"

if [ -f "$LOG_FILE" ]; then
    rm -f "$LOG_FILE"
    echo "🗑️ Log file removed: $LOG_FILE"
fi

echo "✅ All vLLM servers stopped."
