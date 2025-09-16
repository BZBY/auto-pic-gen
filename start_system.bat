@echo off
echo 启动视频人物训练集提取系统
echo ==============================
echo.
echo 此脚本将同时启动后端和前端服务
echo 后端: http://localhost:8000
echo 前端: http://localhost:3000
echo.
echo 按任意键继续...
pause >nul

echo.
echo 启动后端服务...
start "后端服务" cmd /c "start_backend.bat"

echo 等待后端服务启动...
timeout /t 5 >nul

echo.
echo 启动前端服务...
start "前端服务" cmd /c "start_frontend.bat"

echo.
echo 系统启动完成！
echo 请等待服务完全启动后访问: http://localhost:3000
echo.
echo 按任意键退出...
pause >nul
