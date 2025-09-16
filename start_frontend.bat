@echo off
chcp 65001 >nul
echo 启动视频人物训练集提取系统 - 前端界面 (Quasar Vue3)
echo ========================================

cd /d "%~dp0front_quasar"

echo.
echo 启动Quasar前端服务...
echo 前端地址: http://localhost:9000
echo 请确保后端服务已启动 (http://localhost:8000)
echo 按 Ctrl+C 停止服务
echo.

quasar dev

pause
