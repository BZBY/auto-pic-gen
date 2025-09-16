@echo off
echo 启动视频人物训练集提取系统 - 后端服务
echo ========================================

cd /d "%~dp0backend"

echo 检查UV环境...
uv --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到uv，请先安装uv
    echo 安装命令: pip install uv
    pause
    exit /b 1
)

echo.
echo 检查Python虚拟环境...
if not exist ".venv" (
    echo 创建虚拟环境...
    uv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

echo.
echo 激活虚拟环境并安装依赖...
call .venv\Scripts\activate.bat
uv pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 启动后端服务...
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo.

python -m app.main

pause
