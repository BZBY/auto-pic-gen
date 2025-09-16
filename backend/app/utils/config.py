"""配置管理模块"""
import os
from typing import Dict, Any
from pathlib import Path

class Config:
    """应用配置类"""
    
    # 基础配置
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # 模型配置
    WD_MODEL_NAME = os.getenv("WD_MODEL_NAME", "SmilingWolf/wd-eva02-large-tagger-v3")
    DEVICE = os.getenv("DEVICE", "cuda")
    
    # 文件路径配置
    BASE_DIR = Path(__file__).parent.parent.parent
    DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
    TEMP_DIR = BASE_DIR / "temp"
    
    # 视频处理配置
    MAX_FRAMES = int(os.getenv("MAX_FRAMES", "200"))
    SCENE_CHANGE_THRESHOLD = float(os.getenv("SCENE_CHANGE_THRESHOLD", "0.15"))  # 降低阈值，要求更显著的变化
    QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "0.5"))  # 稍微降低质量要求
    
    # 标签配置
    TAG_THRESHOLD = float(os.getenv("TAG_THRESHOLD", "0.35"))
    CHARACTER_TAG_THRESHOLD = float(os.getenv("CHARACTER_TAG_THRESHOLD", "0.75"))
    GENERAL_TAG_THRESHOLD = float(os.getenv("GENERAL_TAG_THRESHOLD", "0.35"))
    
    # API配置 - 本地路径验证
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    @classmethod
    def get_default_processing_config(cls) -> Dict[str, Any]:
        """获取默认的处理配置"""
        return {
            'max_frames': cls.MAX_FRAMES,
            'scene_change_threshold': cls.SCENE_CHANGE_THRESHOLD,
            'quality_threshold': cls.QUALITY_THRESHOLD,
            'tag_threshold': cls.TAG_THRESHOLD,
            'character_tag_threshold': cls.CHARACTER_TAG_THRESHOLD,
            'general_tag_threshold': cls.GENERAL_TAG_THRESHOLD,
            'batch_size': 16
        }
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        for dir_path in [cls.DEFAULT_OUTPUT_DIR, cls.TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_file_path(cls, file_path: str, file_type: str = "video") -> bool:
        """验证文件路径是否有效"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            if file_type == "video":
                return path.suffix.lower() in cls.ALLOWED_VIDEO_EXTENSIONS
            elif file_type == "image":
                return path.suffix.lower() in cls.ALLOWED_IMAGE_EXTENSIONS
            
            return True
        except Exception:
            return False

# 全局配置实例
config = Config()
config.ensure_directories()
