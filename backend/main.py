#!/usr/bin/env python3
"""
视频人物训练集提取系统 - 后端启动文件
"""

import uvicorn
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动FastAPI应用"""
    try:
        # 确保必要的目录存在
        from app.utils.config import config
        config.ensure_directories()
        
        print("🚀 正在启动视频人物训练集提取系统后端...")
        print(f"📂 项目根目录: {project_root}")
        print(f"📁 输出目录: {config.DEFAULT_OUTPUT_DIR}")
        print(f"📁 临时目录: {config.TEMP_DIR}")
        print(f"🖥️  设备: {config.DEVICE}")
        print(f"🤖 模型: {config.WD_MODEL_NAME}")
        print("-" * 50)
        
        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=config.HOST,
            port=config.PORT,
            reload=config.DEBUG,
            log_level="info" if not config.DEBUG else "debug",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
