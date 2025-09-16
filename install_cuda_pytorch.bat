@echo off
chcp 65001 >nul
echo 安装CUDA版本的PyTorch
echo =======================

cd /d "%~dp0backend"

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo 卸载现有PyTorch版本...
uv pip uninstall torch torchvision torchaudio -y

echo.
echo 安装CUDA版本PyTorch (CUDA 12.1)...
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo 验证CUDA是否可用...
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'GPU count: {torch.cuda.device_count()}')"

echo.
echo 安装完成！
pause