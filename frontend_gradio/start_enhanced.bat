@echo off
echo Starting Video Person Dataset Extraction System - Enhanced Gradio Frontend
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM 切换到脚本目录
cd /d "%~dp0"

REM 安装依赖（如果需要）
echo Installing/Updating dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting Enhanced Gradio frontend on http://localhost:7860
echo Backend should be running on http://localhost:8000
echo.
echo Features:
echo  - Real-time status monitoring
echo  - Auto-refresh functionality
echo  - Enhanced error handling
echo  - Better user experience
echo.
echo Press Ctrl+C to stop the server
echo.

REM 启动增强版Gradio应用
python app_enhanced.py

pause