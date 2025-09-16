"""视频处理相关API路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from typing import List, Optional
import logging
import os
import shutil
from pathlib import Path

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
        # 验证视频路径
        if not request.video_paths:
            raise ValueError("至少需要提供一个视频文件路径")

        # 处理参考图片路径 - 转换临时文件名为完整路径
        processed_reference_paths = []
        for ref_path in request.reference_image_paths:
            if not os.path.isabs(ref_path):
                # 如果不是绝对路径，尝试在temp目录中查找
                temp_ref_path = os.path.join(str(config.TEMP_DIR), ref_path)
                if os.path.exists(temp_ref_path):
                    processed_reference_paths.append(temp_ref_path)
                else:
                    logger.warning(f"跳过无效参考图片文件: {ref_path} (未找到文件)")
            else:
                processed_reference_paths.append(ref_path)
        
        # 更新请求中的参考图片路径
        request.reference_image_paths = processed_reference_paths

        # 获取输出目录
        output_dir = request.get_output_directory()

        # 批量处理所有视频文件
        task_ids = []
        processed_videos = []

        for i, video_path in enumerate(request.video_paths):
            # 检查是否为上传的文件路径（临时处理）
            if not os.path.isabs(video_path):
                # 如果不是绝对路径，尝试在temp目录中查找
                temp_path = os.path.join(str(config.TEMP_DIR), video_path)
                if os.path.exists(temp_path):
                    video_path = temp_path
                    request.video_paths[i] = video_path  # 更新路径
                else:
                    logger.warning(f"跳过无效视频文件: {video_path} (未找到文件)")
                    continue
            
            # 验证每个视频文件
            if not config.validate_file_path(video_path, "video"):
                logger.warning(f"跳过无效视频文件: {video_path}")
                continue

            # 为每个视频创建子目录
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            video_output_dir = os.path.join(output_dir, f"video_{i+1}_{video_name}")

            # 创建兼容的旧格式请求对象
            legacy_request = type('LegacyRequest', (), {
                'video_path': video_path,
                'output_directory': video_output_dir,  # 修改为正确的属性名
                'reference_image_paths': request.reference_image_paths,
                'config': type('Config', (), {
                    'max_frames': request.config.max_frames,
                    'scene_change_threshold': request.config.scene_change_threshold,
                    'quality_threshold': request.config.quality_threshold,
                    'tag_threshold': request.config.tag_threshold,
                    'character_tag_threshold': request.config.character_tag_threshold,
                    'batch_size': request.config.batch_size
                })()
            })()

            # 启动处理任务
            task_id = await video_processor.start_video_processing(legacy_request)
            task_ids.append(task_id)
            processed_videos.append(video_path)

            logger.info(f"已启动视频处理任务 {i+1}/{len(request.video_paths)}: {video_path} -> {task_id}")

        if not task_ids:
            raise ValueError("没有有效的视频文件可以处理")

        return {
            "success": True,
            "task_ids": task_ids,
            "main_task_id": task_ids[0],  # 主任务ID（兼容旧版前端）
            "total_videos": len(task_ids),
            "processed_videos": processed_videos,
            "output_directory": output_dir,
            "message": f"批量视频处理任务已开始，共 {len(task_ids)} 个视频"
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

@router.post("/upload-video")
async def upload_video_file(file: UploadFile = File(...)):
    """上传视频文件"""
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in config.ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的视频格式: {file_extension}"
            )
        
        # 确保temp目录存在
        config.ensure_directories()
        
        # 生成唯一文件名
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = config.TEMP_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"视频文件上传成功: {file.filename} -> {file_path}")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": str(file_path),
            "temp_filename": unique_filename,
            "file_size": file_path.stat().st_size
        }
        
    except Exception as e:
        logger.error(f"视频文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/upload-image")
async def upload_image_file(file: UploadFile = File(...)):
    """上传参考图片文件"""
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in config.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的图片格式: {file_extension}"
            )
        
        # 确保temp目录存在
        config.ensure_directories()
        
        # 生成唯一文件名
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = config.TEMP_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"图片文件上传成功: {file.filename} -> {file_path}")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": str(file_path),
            "temp_filename": unique_filename,
            "file_size": file_path.stat().st_size
        }
        
    except Exception as e:
        logger.error(f"图片文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.delete("/temp-file/{filename}")
async def delete_temp_file(filename: str):
    """删除临时文件"""
    try:
        file_path = config.TEMP_DIR / filename
        if file_path.exists():
            file_path.unlink()
            return {"success": True, "message": f"文件 {filename} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        logger.error(f"删除临时文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/temp-files")
async def list_temp_files():
    """列出所有临时文件"""
    try:
        temp_files = []
        if config.TEMP_DIR.exists():
            for file_path in config.TEMP_DIR.iterdir():
                if file_path.is_file():
                    temp_files.append({
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "created_time": file_path.stat().st_ctime
                    })
        
        return {
            "success": True,
            "files": temp_files,
            "total_count": len(temp_files)
        }
    except Exception as e:
        logger.error(f"列出临时文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")
