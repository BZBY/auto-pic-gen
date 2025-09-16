@echo off
echo 视频人物训练集提取系统 - 环境设置
echo ================================

echo.
echo 此脚本将为您设置完整的开发环境
echo 包括: UV虚拟环境 + Python依赖 + Node.js依赖
echo.
echo 按任意键继续...
pause >nul

echo.
echo [1/4] 检查UV是否已安装...
uv --version >nul 2>&1
if errorlevel 1 (
    echo UV未安装，正在安装...
    pip install uv
    if errorlevel 1 (
        echo 错误: UV安装失败，请检查Python和pip是否正确安装
        pause
        exit /b 1
    )
    echo UV安装成功！
) else (
    echo UV已安装
)

echo.
echo [2/4] 设置Python后端环境...
cd /d "%~dp0backend"

if not exist ".venv" (
    echo 创建Python虚拟环境...
    uv venv
    if errorlevel 1 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

echo 激活虚拟环境并安装Python依赖...
call .venv\Scripts\activate.bat
uv pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: Python依赖安装失败
    pause
    exit /b 1
)
echo Python环境设置完成！

echo.
echo [3/4] 设置Node.js前端环境...
cd /d "%~dp0frontend"

echo 检查Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo 检查yarn...
yarn --version >nul 2>&1
if errorlevel 1 (
    echo 未找到yarn，使用npm安装依赖...
    npm install
    if errorlevel 1 (
        echo 错误: Node.js依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo 使用yarn安装依赖...
    yarn install
    if errorlevel 1 (
        echo 错误: Node.js依赖安装失败
        pause
        exit /b 1
    )
)
echo Node.js环境设置完成！

echo.
echo [4/4] 验证环境...
cd /d "%~dp0"

echo 验证Python环境...
cd backend
call .venv\Scripts\activate.bat
python -c "import fastapi; import torch; import cv2; print('Python环境验证成功！')"
if errorlevel 1 (
    echo 警告: Python环境验证失败，可能存在依赖问题
)

echo 验证Node.js环境...
cd ../frontend
node -e "console.log('Node.js环境验证成功！')"
if errorlevel 1 (
    echo 警告: Node.js环境验证失败
)

cd ..

echo.
echo ================================
echo 🎉 环境设置完成！
echo ================================
echo.
echo 现在您可以使用以下命令启动系统：
echo   start_system.bat     - 启动完整系统
echo   start_backend.bat    - 仅启动后端
echo   start_frontend.bat   - 仅启动前端
echo.
echo 注意事项：
echo - 后端使用UV虚拟环境 (backend/.venv/)
echo - 虚拟环境不会被上传到Git
echo - 首次运行会自动下载WD模型 (约2-3GB)
echo.
echo 按任意键退出...
pause >nul
