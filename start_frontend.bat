@echo off
echo 启动视频人物训练集提取系统 - 前端界面
echo ========================================

cd /d "%~dp0frontend"

echo 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请确保Node.js已安装并添加到PATH
    pause
    exit /b 1
)

echo 检查yarn...
yarn --version >nul 2>&1
if errorlevel 1 (
    echo 未找到yarn，使用npm...
    set USE_NPM=1
) else (
    echo 使用yarn管理依赖
    set USE_NPM=0
)

echo.
echo 检查依赖包...
if not exist "node_modules" (
    echo 正在安装依赖包...
    if %USE_NPM%==1 (
        npm install
    ) else (
        yarn install
    )
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动前端服务...
echo 前端地址: http://localhost:3000
echo 请确保后端服务已启动 (http://localhost:8000)
echo 按 Ctrl+C 停止服务
echo.

if %USE_NPM%==1 (
    npm start
) else (
    yarn start
)

pause
