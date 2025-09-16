@echo off
chcp 65001 >nul
echo 🚀 启动视频人物训练集提取系统后端...
echo.

cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到PATH
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 📋 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📦 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

REM 启动服务器
echo 🚀 启动服务器...
python main.py

pause
