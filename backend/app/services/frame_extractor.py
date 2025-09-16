"""智能视频帧提取服务"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

from ..models.video_models import ExtractedFrame, FrameQuality, VideoInfo

logger = logging.getLogger(__name__)

class SceneChangeDetector:
    """智能场景变化检测"""
    
    def __init__(self):
        self.prev_hist = None
        self.prev_frame_gray = None
        
    def calculate_scene_change(self, frame: np.ndarray) -> float:
        """计算场景变化程度"""
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算直方图
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # 计算光流（需要前一帧）
        optical_flow_score = 0.0
        if self.prev_frame_gray is not None:
            # 使用更简单的帧差法
            frame_diff = cv2.absdiff(self.prev_frame_gray, gray)
            optical_flow_score = np.mean(frame_diff) / 255.0
        
        # 直方图相关性
        hist_correlation = 1.0
        if self.prev_hist is not None:
            hist_correlation = cv2.compareHist(self.prev_hist, hist, cv2.HISTCMP_CORREL)
        
        # 边缘密度变化
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])
        
        # 组合得分
        scene_change_score = (1 - hist_correlation) * 0.6 + optical_flow_score * 0.3 + edge_density * 0.1
        
        # 更新状态
        self.prev_hist = hist.copy()
        self.prev_frame_gray = gray.copy()
        
        return min(scene_change_score, 1.0)  # 确保不超过1.0

class ImageQualityAssessor:
    """图像质量评估"""
    
    @staticmethod
    def assess_quality(image: np.ndarray) -> FrameQuality:
        """评估图像质量"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. 模糊度检测（拉普拉斯方差）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 1000.0, 1.0)  # 归一化
        
        # 2. 亮度评估
        mean_brightness = np.mean(gray)
        brightness_score = 1.0 - abs(mean_brightness - 128) / 128.0
        
        # 3. 对比度评估
        contrast = gray.std()
        contrast_score = min(contrast / 64.0, 1.0)
        
        # 4. 噪声评估（边缘密度）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])
        noise_score = min(edge_density * 10, 1.0)
        
        # 综合质量评分
        overall_quality = (
            blur_score * 0.4 + 
            brightness_score * 0.2 + 
            contrast_score * 0.3 + 
            noise_score * 0.1
        )
        
        return FrameQuality(
            overall=overall_quality,
            blur=blur_score,
            brightness=brightness_score,
            contrast=contrast_score,
            noise=noise_score
        )

class VideoFrameExtractor:
    """智能视频帧提取器"""
    
    def __init__(self):
        self.scene_detector = SceneChangeDetector()
        self.quality_assessor = ImageQualityAssessor()
    
    def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        file_size = Path(video_path).stat().st_size
        
        cap.release()
        
        return VideoInfo(
            filename=Path(video_path).name,
            duration=duration,
            fps=fps,
            total_frames=total_frames,
            width=width,
            height=height,
            file_size=file_size
        )
    
    def extract_frames(self, video_path: str, 
                      output_dir: str,
                      max_frames: int = 200,
                      scene_change_threshold: float = 0.3,
                      quality_threshold: float = 0.6,
                      progress_callback=None) -> Tuple[List[ExtractedFrame], VideoInfo]:
        """从视频中智能提取帧"""
        
        # 获取视频信息
        video_info = self.get_video_info(video_path)
        logger.info(f"视频信息: {video_info.total_frames} 帧, {video_info.fps} FPS")
        
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        extracted_frames = []
        frame_count = 0
        last_extract_frame = -10  # 避免连续提取
        
        # 重置检测器状态
        self.scene_detector = SceneChangeDetector()
        
        try:
            while cap.isOpened() and len(extracted_frames) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 更新进度
                if progress_callback:
                    progress = min(frame_count / video_info.total_frames, 1.0)
                    progress_callback(progress, f"处理第 {frame_count} 帧")
                
                # 跳帧处理（每3帧检测一次）
                if frame_count % 3 != 0:
                    frame_count += 1
                    continue
                
                # 场景变化检测
                scene_change = self.scene_detector.calculate_scene_change(frame)
                
                # 只在场景有显著变化时考虑提取
                if scene_change > scene_change_threshold:
                    # 避免连续提取相似帧
                    if frame_count - last_extract_frame > 15:  # 至少间隔15帧
                        # 质量评估
                        quality = self.quality_assessor.assess_quality(frame)
                        
                        if quality.overall > quality_threshold:
                            timestamp = frame_count / video_info.fps
                            
                            # 保存帧
                            filename = f"frame_{len(extracted_frames):04d}_{frame_count:06d}.jpg"
                            frame_path = output_path / filename
                            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            
                            extracted_frame = ExtractedFrame(
                                frame_number=frame_count,
                                timestamp=timestamp,
                                filename=filename,
                                scene_change=scene_change,
                                quality=quality,
                                width=frame.shape[1],
                                height=frame.shape[0]
                            )
                            
                            extracted_frames.append(extracted_frame)
                            last_extract_frame = frame_count
                            
                            logger.info(f"提取帧 {frame_count} (t={timestamp:.1f}s, "
                                      f"scene={scene_change:.3f}, quality={quality.overall:.3f})")
                
                frame_count += 1
            
        finally:
            cap.release()
        
        logger.info(f"总共提取 {len(extracted_frames)} 帧")
        return extracted_frames, video_info
