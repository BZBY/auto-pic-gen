"""视频处理相关API路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

from ..models.video_models import (
    VideoProcessRequest, ProcessingStatus, ProcessingResult, VideoInfo
)
from ..services.video_processor import get_video_processor
from ..services.frame_extractor import VideoFrameExtractor
from ..utils.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])

# 获取服务实例
video_processor = get_video_processor()
frame_extractor = VideoFrameExtractor()

@router.post("/process", response_model=dict)
async def start_video_processing(request: VideoProcessRequest):
    """开始视频处理任务"""
    try:
        task_id = await video_processor.start_video_processing(request)
        return {
            "success": True,
            "task_id": task_id,
            "message": "视频处理任务已开始"
        }
    except Exception as e:
        logger.error(f"启动视频处理任务失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{task_id}", response_model=ProcessingStatus)
async def get_task_status(task_id: str):
    """获取任务处理状态"""
    status = video_processor.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status

@router.get("/tasks", response_model=List[ProcessingStatus])
async def get_all_tasks():
    """获取所有任务状态"""
    return video_processor.get_all_tasks()

@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    success = video_processor.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务")
    return {"success": True, "message": "任务已取消"}

@router.get("/info")
async def get_video_info(video_path: str):
    """获取视频基本信息"""
    try:
        if not config.validate_file_path(video_path, "video"):
            raise HTTPException(status_code=400, detail="无效的视频文件路径")
        
        video_info = frame_extractor.get_video_info(video_path)
        return {
            "success": True,
            "video_info": video_info
        }
    except Exception as e:
        logger.error(f"获取视频信息失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate-path")
async def validate_file_path(file_path: str, file_type: str = "video"):
    """验证文件路径是否有效"""
    try:
        is_valid = config.validate_file_path(file_path, file_type)
        return {
            "valid": is_valid,
            "path": file_path,
            "type": file_type
        }
    except Exception as e:
        return {
            "valid": False,
            "path": file_path,
            "type": file_type,
            "error": str(e)
        }
