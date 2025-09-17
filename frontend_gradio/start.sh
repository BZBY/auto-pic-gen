#!/bin/bash

echo "Starting Video Person Dataset Extraction System - Gradio Frontend"
echo

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# 切换到脚本目录
cd "$(dirname "$0")"

# 安装依赖（如果需要）
echo "Installing/Updating dependencies..."
python -m pip install -r requirements.txt

echo
echo "Starting Gradio frontend on http://localhost:7860"
echo "Backend should be running on http://localhost:8000"
echo
echo "Press Ctrl+C to stop the server"
echo

# 启动Gradio应用
python app.py