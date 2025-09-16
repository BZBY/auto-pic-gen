@echo off
chcp 65001 >nul
echo 启动视频人物训练集提取系统 - 后端服务
echo ========================================

set PROJECT_DIR=%~dp0

cd /d "%PROJECT_DIR%backend"

echo.
echo 启动后端服务...
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo.

python -m app.main

pause
