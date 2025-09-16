"""视频处理主服务 - 整合所有处理流程"""
import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Callable
import logging
from datetime import datetime
from PIL import Image

from ..models.video_models import (
    VideoProcessRequest, ProcessingStatus, ProcessingResult, 
    ExtractedFrame, VideoInfo, ProcessingConfig
)
from ..models.tag_models import TagMatchRequest, ImageTagResult
from ..utils.config import config
from .frame_extractor import VideoFrameExtractor
from .wd_tagger import get_wd_tagger
from .tag_matcher import get_tag_matcher

logger = logging.getLogger(__name__)

class VideoProcessingService:
    """视频处理主服务"""
    
    def __init__(self):
        self.frame_extractor = VideoFrameExtractor()
        self.wd_tagger = get_wd_tagger()
        self.tag_matcher = get_tag_matcher()
        self.processing_tasks: Dict[str, ProcessingStatus] = {}
    
    async def start_video_processing(self, request: VideoProcessRequest) -> str:
        """开始视频处理任务（异步）"""
        
        # 验证输入路径
        if not config.validate_file_path(request.video_path, "video"):
            raise ValueError(f"无效的视频文件路径: {request.video_path}")
        
        for ref_path in request.reference_image_paths:
            if not config.validate_file_path(ref_path, "image"):
                raise ValueError(f"无效的参考图片路径: {ref_path}")
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        status = ProcessingStatus(
            task_id=task_id,
            status="pending",
            progress=0.0,
            current_step="初始化任务",
            total_steps=5,
            completed_steps=0,
            start_time=datetime.now()
        )
        
        self.processing_tasks[task_id] = status
        
        # 启动异步处理任务
        asyncio.create_task(self._process_video_async(task_id, request))
        
        return task_id
    
    async def _process_video_async(self, task_id: str, request: VideoProcessRequest):
        """异步处理视频的核心逻辑"""
        status = self.processing_tasks[task_id]
        
        try:
            status.status = "processing"
            
            # 步骤1: 提取视频帧
            status.current_step = "提取视频帧"
            status.progress = 0.1
            logger.info(f"任务 {task_id}: 开始提取视频帧")
            
            def progress_callback(progress, step_info):
                status.progress = 0.1 + progress * 0.3  # 0.1-0.4
                status.current_step = f"提取视频帧: {step_info}"
            
            frames, video_info = self.frame_extractor.extract_frames(
                video_path=request.video_path,
                output_dir=request.output_directory,
                max_frames=request.config.max_frames,
                scene_change_threshold=request.config.scene_change_threshold,
                quality_threshold=request.config.quality_threshold,
                progress_callback=progress_callback
            )
            
            status.completed_steps = 1
            status.progress = 0.4
            
            if not frames:
                raise ValueError("没有提取到任何有效帧")
            
            # 步骤2: 批量标注提取的帧
            status.current_step = "对提取的帧进行WD标注"
            status.progress = 0.4
            logger.info(f"任务 {task_id}: 开始标注 {len(frames)} 张图片")
            
            # 加载图片
            frame_images = []
            frame_filenames = []
            output_path = Path(request.output_directory)
            
            for frame in frames:
                img_path = output_path / frame.filename
                if img_path.exists():
                    image = Image.open(img_path)
                    frame_images.append(image)
                    frame_filenames.append(frame.filename)
            
            # 批量标注
            frame_tag_results = self.wd_tagger.batch_tag_images(
                images=frame_images,
                filenames=frame_filenames,
                general_threshold=request.config.general_tag_threshold,
                character_threshold=request.config.character_tag_threshold,
                batch_size=request.config.batch_size
            )
            
            # 将标签结果添加到帧数据
            for i, tag_result in enumerate(frame_tag_results):
                if i < len(frames):
                    frames[i].tags = {tag.name: tag.confidence for tag in tag_result.tags}
            
            status.completed_steps = 2
            status.progress = 0.6
            
            # 步骤3: 处理参考图像
            reference_tag_results = []
            if request.reference_image_paths:
                status.current_step = "处理参考图像"
                status.progress = 0.6
                logger.info(f"任务 {task_id}: 处理 {len(request.reference_image_paths)} 张参考图像")
                
                for ref_path in request.reference_image_paths:
                    ref_image = Image.open(ref_path)
                    ref_tags = self.wd_tagger.tag_single_image(
                        image=ref_image,
                        general_threshold=request.config.general_tag_threshold,
                        character_threshold=request.config.character_tag_threshold
                    )
                    ref_tags.filename = Path(ref_path).name
                    reference_tag_results.append(ref_tags)
            
            status.completed_steps = 3
            status.progress = 0.7
            
            # 步骤4: 标签匹配筛选
            matched_frames = frames  # 默认返回所有帧
            
            if reference_tag_results:
                status.current_step = "基于参考图像进行标签匹配"
                status.progress = 0.7
                logger.info(f"任务 {task_id}: 开始标签匹配")
                
                # 自动创建匹配请求
                match_request = self.tag_matcher.create_reference_match_request(
                    reference_tag_results, min_confidence=0.6
                )
                
                # 进行匹配
                frames_with_tags = [(frame, frame_tag_results[i]) 
                                   for i, frame in enumerate(frames) 
                                   if i < len(frame_tag_results)]
                
                matching_results = self.tag_matcher.find_matching_frames(
                    frames_with_tags, match_request
                )
                
                matched_frames = [frame_data for frame_data, _ in matching_results]
                
                logger.info(f"匹配到 {len(matched_frames)} 张符合要求的图片")
            
            status.completed_steps = 4
            status.progress = 0.9
            
            # 步骤5: 导出最终数据集
            status.current_step = "导出数据集"
            status.progress = 0.9
            
            await self._export_final_dataset(
                matched_frames, frame_tag_results, request.output_directory
            )
            
            # 完成处理
            status.status = "completed"
            status.progress = 1.0
            status.current_step = "处理完成"
            status.completed_steps = 5
            status.end_time = datetime.now()
            
            # 保存处理结果
            processing_time = (status.end_time - status.start_time).total_seconds()
            
            result = ProcessingResult(
                task_id=task_id,
                video_info=video_info,
                total_extracted_frames=len(frames),
                matched_frames=len(matched_frames),
                output_directory=request.output_directory,
                processing_time=processing_time,
                config_used=request.config,
                frames=matched_frames
            )
            
            # 保存结果到文件
            result_path = Path(request.output_directory) / "processing_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"任务 {task_id} 处理完成")
            
        except Exception as e:
            logger.error(f"任务 {task_id} 处理失败: {e}")
            status.status = "failed"
            status.error_message = str(e)
            status.end_time = datetime.now()
    
    async def _export_final_dataset(self, frames: List[ExtractedFrame], 
                                   tag_results: List[ImageTagResult],
                                   output_dir: str):
        """导出最终数据集"""
        output_path = Path(output_dir)
        
        # 创建标签文件
        for i, frame in enumerate(frames):
            if i < len(tag_results):
                tag_result = tag_results[i]
                
                # 创建标签文本
                tag_strings = []
                for tag in tag_result.tags:
                    tag_strings.append(f"{tag.name}:{tag.confidence:.3f}")
                
                # 保存标签文件
                tag_filename = frame.filename.replace('.jpg', '.txt')
                tag_path = output_path / tag_filename
                
                with open(tag_path, 'w', encoding='utf-8') as f:
                    f.write(', '.join(tag_strings))
        
        # 创建元数据文件
        metadata = []
        for i, frame in enumerate(frames):
            metadata.append({
                'filename': frame.filename,
                'frame_number': frame.frame_number,
                'timestamp': frame.timestamp,
                'scene_change': frame.scene_change,
                'quality': frame.quality.dict(),
                'tag_count': len(frame.tags) if frame.tags else 0
            })
        
        metadata_path = output_path / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"数据集导出完成，共 {len(frames)} 张图片")
    
    def get_task_status(self, task_id: str) -> Optional[ProcessingStatus]:
        """获取任务状态"""
        return self.processing_tasks.get(task_id)
    
    def get_all_tasks(self) -> List[ProcessingStatus]:
        """获取所有任务状态"""
        return list(self.processing_tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.processing_tasks:
            status = self.processing_tasks[task_id]
            if status.status in ["pending", "processing"]:
                status.status = "cancelled"
                status.end_time = datetime.now()
                return True
        return False

# 全局单例实例
_processor_instance = None

def get_video_processor() -> VideoProcessingService:
    """获取视频处理服务实例（单例模式）"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = VideoProcessingService()
    return _processor_instance
