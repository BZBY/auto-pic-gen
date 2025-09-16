"""FastAPI主应用"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from pathlib import Path

from .api.video import router as video_router
from .api.tags import router as tags_router
from .utils.config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="视频人物训练集提取系统",
    description="基于WD标签匹配的智能视频帧提取和人物数据集生成系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React开发服务器
        "http://127.0.0.1:3000",   # React开发服务器
        "http://localhost:9000",    # Quasar开发服务器
        "http://127.0.0.1:9000",   # Quasar开发服务器
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(video_router)
app.include_router(tags_router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "视频人物训练集提取系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        # 检查模型是否正常加载
        from .services.wd_tagger import get_wd_tagger
        tagger = get_wd_tagger()
        model_info = tagger.get_model_info()
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_info": model_info,
            "config": {
                "device": config.DEVICE,
                "max_frames": config.MAX_FRAMES,
                "scene_change_threshold": config.SCENE_CHANGE_THRESHOLD,
                "quality_threshold": config.QUALITY_THRESHOLD
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/api/config")
async def get_config():
    """获取系统配置"""
    return {
        "processing_config": config.get_default_processing_config(),
        "supported_video_formats": list(config.ALLOWED_VIDEO_EXTENSIONS),
        "supported_image_formats": list(config.ALLOWED_IMAGE_EXTENSIONS),
        "model_name": config.WD_MODEL_NAME,
        "device": config.DEVICE
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "detail": str(exc) if config.DEBUG else "请查看服务器日志"
        }
    )

if __name__ == "__main__":
    logger.info("启动视频人物训练集提取系统...")
    logger.info(f"配置: {config.get_default_processing_config()}")
    
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
