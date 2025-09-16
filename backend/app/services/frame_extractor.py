"""智能视频帧提取服务"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

from ..models.video_models import ExtractedFrame, FrameQuality, VideoInfo

logger = logging.getLogger(__name__)

class SceneChangeDetector:
    """优化的场景变化检测器 - 基于最佳实践"""
    
    def __init__(self):
        self.prev_hist_rgb = None
        self.prev_hist_hsv = None
        self.prev_frame_gray = None
        self.frame_buffer = []  # 用于平滑检测
        self.buffer_size = 3
        
    def calculate_scene_change(self, frame: np.ndarray) -> float:
        """计算场景变化程度 - 使用多指标融合"""
        try:
            # 转换为不同色彩空间
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 如果是第一帧，初始化
            if self.prev_frame_gray is None:
                self._initialize_first_frame(frame, gray, hsv)
                return 0.0
            
            # 1. RGB直方图比较（对颜色变化敏感）
            hist_rgb = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
            rgb_correlation = cv2.compareHist(self.prev_hist_rgb, hist_rgb, cv2.HISTCMP_CORREL)
            rgb_score = max(0.0, 1.0 - rgb_correlation)
            
            # 2. HSV直方图比较（对光照变化不敏感）
            hist_hsv = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hsv_correlation = cv2.compareHist(self.prev_hist_hsv, hist_hsv, cv2.HISTCMP_CORREL)
            hsv_score = max(0.0, 1.0 - hsv_correlation)
            
            # 3. 帧差异（结构变化检测）
            frame_diff = cv2.absdiff(self.prev_frame_gray, gray)
            # 使用自适应阈值减少噪声影响
            _, thresh = cv2.threshold(frame_diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            diff_score = np.sum(thresh > 0) / (thresh.shape[0] * thresh.shape[1])
            
            # 4. 边缘密度变化（细节变化检测）
            edges_curr = cv2.Canny(gray, 50, 150)
            edges_prev = cv2.Canny(self.prev_frame_gray, 50, 150)
            edge_diff = cv2.absdiff(edges_curr, edges_prev)
            edge_score = np.mean(edge_diff) / 255.0
            
            # 融合多个指标（权重基于最佳实践）
            scene_change_score = (
                rgb_score * 0.35 +      # RGB颜色变化
                hsv_score * 0.25 +      # HSV颜色变化（光照鲁棒）
                diff_score * 0.25 +     # 结构变化
                edge_score * 0.15       # 边缘变化
            )
            
            # 使用滑动窗口平滑结果，避免噪声
            self.frame_buffer.append(scene_change_score)
            if len(self.frame_buffer) > self.buffer_size:
                self.frame_buffer.pop(0)
            
            # 计算平滑后的得分
            smoothed_score = np.mean(self.frame_buffer)
            
            # 应用非线性变换，增强显著变化
            if smoothed_score > 0.1:
                smoothed_score = smoothed_score ** 0.8  # 增强大变化
            else:
                smoothed_score = smoothed_score ** 1.2  # 抑制小变化
            
            # 更新状态
            self.prev_hist_rgb = hist_rgb.copy()
            self.prev_hist_hsv = hist_hsv.copy()
            self.prev_frame_gray = gray.copy()
            
            return min(smoothed_score, 1.0)
            
        except Exception as e:
            # 出错时返回0，避免程序崩溃
            return 0.0
    
    def _initialize_first_frame(self, frame: np.ndarray, gray: np.ndarray, hsv: np.ndarray):
        """初始化第一帧的数据"""
        self.prev_frame_gray = gray.copy()
        self.prev_hist_rgb = cv2.calcHist([frame], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
        self.prev_hist_hsv = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        self.frame_buffer = [0.0]

class ImageQualityAssessor:
    """优化的图像质量评估器"""
    
    @staticmethod
    def assess_quality(image: np.ndarray) -> FrameQuality:
        """评估图像质量 - 使用更稳定的算法"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 1. 清晰度评估（使用多种方法）
            # Laplacian方差（主要指标）
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            # Sobel梯度幅值（辅助指标）
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            sobel_var = np.sqrt(sobelx**2 + sobely**2).var()
            
            # 组合清晰度得分
            blur_score = min((laplacian_var / 500.0 + sobel_var / 1000.0) / 2, 1.0)
            
            # 2. 亮度评估（更合理的范围）
            mean_brightness = np.mean(gray)
            # 最佳亮度范围是80-180
            if 80 <= mean_brightness <= 180:
                brightness_score = 1.0
            elif mean_brightness < 80:
                brightness_score = mean_brightness / 80.0
            else:
                brightness_score = max(0.0, 1.0 - (mean_brightness - 180) / 75.0)
            
            # 3. 对比度评估（使用RMS对比度）
            rms_contrast = np.sqrt(np.mean((gray - np.mean(gray))**2))
            contrast_score = min(rms_contrast / 50.0, 1.0)
            
            # 4. 噪声评估（使用更精确的方法）
            # 计算图像的局部方差
            kernel = np.ones((5,5), np.float32) / 25
            local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            local_var = cv2.filter2D((gray.astype(np.float32) - local_mean)**2, -1, kernel)
            noise_score = 1.0 - min(np.mean(local_var) / 1000.0, 1.0)  # 噪声越小，得分越高
            
            # 5. 结构信息评估（新增）
            # 使用边缘密度评估图像的结构丰富度
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            structure_score = min(edge_density * 5, 1.0)
            
            # 综合质量评分（调整权重）
            overall_quality = (
                blur_score * 0.35 +         # 清晰度最重要
                contrast_score * 0.25 +     # 对比度很重要
                brightness_score * 0.2 +    # 亮度重要
                structure_score * 0.1 +     # 结构信息
                noise_score * 0.1           # 噪声控制
            )
            
            return FrameQuality(
                overall=overall_quality,
                blur=blur_score,
                brightness=brightness_score,
                contrast=contrast_score,
                noise=noise_score
            )
            
        except Exception as e:
            # 出错时返回低质量得分
            return FrameQuality(
                overall=0.1,
                blur=0.1,
                brightness=0.5,
                contrast=0.1,
                noise=0.1
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
            duration=duration,
            fps=fps,
            width=width,
            height=height,
            frame_count=total_frames,  # 修正字段名
            file_size=file_size,
            format=Path(video_path).suffix.lower()  # 添加格式字段
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
        logger.info(f"视频信息: {video_info.frame_count} 帧, {video_info.fps} FPS")
        
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
            # 添加跳帧策略，避免处理每一帧
            frame_skip = max(1, int(video_info.fps / 10))  # 每秒最多检测10帧
            logger.info(f"跳帧策略: 每{frame_skip}帧检测一次")
            
            while cap.isOpened() and len(extracted_frames) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 更新进度和日志
                if frame_count % 1000 == 0:  # 每1000帧输出一次进度
                    progress = min(frame_count / video_info.frame_count, 1.0)
                    logger.info(f"处理进度: {frame_count}/{video_info.frame_count} 帧 ({progress*100:.1f}%), 已提取: {len(extracted_frames)} 帧")
                    if progress_callback:
                        progress_callback(progress, f"处理第 {frame_count} 帧")
                
                # 跳帧处理（降低处理频率）
                if frame_count % frame_skip != 0:
                    frame_count += 1
                    continue
                
                # 场景变化检测（添加异常处理）
                try:
                    scene_change = self.scene_detector.calculate_scene_change(frame)
                except Exception as e:
                    logger.warning(f"场景检测失败 (帧{frame_count}): {e}, 跳过此帧")
                    frame_count += 1
                    continue
                
                # 只在场景有显著变化时考虑提取
                if scene_change > scene_change_threshold:
                    # 避免连续提取相似帧（增加最小间隔）
                    min_frame_interval = max(30, int(video_info.fps * 2))  # 至少2秒间隔
                    if frame_count - last_extract_frame > min_frame_interval:
                        # 质量评估（添加异常处理）
                        try:
                            quality = self.quality_assessor.assess_quality(frame)
                        except Exception as e:
                            logger.warning(f"质量评估失败 (帧{frame_count}): {e}, 跳过此帧")
                            frame_count += 1
                            continue
                        
                        if quality.overall > quality_threshold:
                            timestamp = frame_count / video_info.fps
                            
                            # 保存帧（添加异常处理）
                            filename = f"frame_{len(extracted_frames):04d}_{frame_count:06d}.jpg"
                            frame_path = output_path / filename
                            
                            try:
                                success = cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                                if not success:
                                    logger.warning(f"保存帧失败 (帧{frame_count}): 写入失败")
                                    frame_count += 1
                                    continue
                                
                                # 获取文件大小
                                file_size = frame_path.stat().st_size if frame_path.exists() else 0
                            except Exception as e:
                                logger.warning(f"保存帧失败 (帧{frame_count}): {e}")
                                frame_count += 1
                                continue
                            
                            extracted_frame = ExtractedFrame(
                                frame_id=f"frame_{len(extracted_frames):04d}",
                                frame_index=frame_count,
                                timestamp=timestamp,
                                image_path=str(frame_path),
                                scene_change_score=scene_change,
                                quality_score=quality.overall,
                                width=frame.shape[1],
                                height=frame.shape[0],
                                file_size=file_size
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
