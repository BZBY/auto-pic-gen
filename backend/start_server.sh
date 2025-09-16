#!/bin/bash

echo "🚀 启动视频人物训练集提取系统后端..."
echo

cd "$(dirname "$0")"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    echo "请先安装Python 3.8+"
    exit 1
fi

# 检查依赖是否安装
echo "📋 检查依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 启动服务器
echo "🚀 启动服务器..."
python3 main.py
