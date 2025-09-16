"""WD EVA02-Large Tagger v3 推理服务"""
import torch
import timm
import pandas as pd
import numpy as np
from PIL import Image
from typing import List, Dict, Tuple
import torchvision.transforms as transforms
from huggingface_hub import hf_hub_download
import logging

from ..models.tag_models import TagResult, TagCategory, ImageTagResult
from ..utils.config import config

logger = logging.getLogger(__name__)

class WDTaggerService:
    """WD EVA02-Large Tagger v3 推理服务"""
    
    def __init__(self, model_name: str = None, device: str = None):
        self.model_name = model_name or config.WD_MODEL_NAME
        self.device = device or config.DEVICE
        self.model = None
        self.tag_names = []
        self.general_tags = []
        self.character_tags = []
        self.transform = None
        
        # 确保设备可用
        if self.device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
            logger.warning("CUDA不可用，切换到CPU")
        
        self._load_model()
    
    def _load_model(self):
        """加载WD Tagger模型和标签"""
        try:
            logger.info(f"正在加载WD Tagger: {self.model_name}")
            
            # 使用timm加载模型
            self.model = timm.create_model(
                f'hf-hub:{self.model_name}', 
                pretrained=True
            ).eval().to(self.device)
            
            # 加载标签文件
            tags_csv_path = hf_hub_download(
                repo_id=self.model_name, 
                filename="selected_tags.csv"
            )
            
            # 读取标签
            df = pd.read_csv(tags_csv_path)
            self.tag_names = df['name'].tolist()
            self.general_tags = df[df['category'] == 0]['name'].tolist()
            self.character_tags = df[df['category'] == 4]['name'].tolist()
            
            logger.info(f"已加载 {len(self.tag_names)} 个标签 "
                       f"({len(self.general_tags)} 个一般标签, "
                       f"{len(self.character_tags)} 个角色标签)")
            
            # 数据预处理管道
            self.transform = transforms.Compose([
                transforms.Resize((448, 448)),  # WD v3 使用448x448
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], 
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
        except Exception as e:
            logger.error(f"加载WD Tagger失败: {e}")
            raise
    
    def tag_single_image(self, image: Image.Image, 
                        general_threshold: float = 0.35,
                        character_threshold: float = 0.75) -> ImageTagResult:
        """对单张图片进行标注"""
        try:
            # 预处理图像
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # 推理
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probs = torch.sigmoid(outputs[0]).cpu().numpy()
            
            # 处理结果
            all_tags = []
            character_tags = []
            general_tags = []
            ratings = {}
            
            for i, prob in enumerate(probs):
                tag_name = self.tag_names[i]
                
                # 评级标签特殊处理
                if tag_name in ['general', 'sensitive', 'questionable', 'explicit']:
                    ratings[tag_name] = float(prob)
                    continue
                
                # 角色标签
                if tag_name in self.character_tags and prob > character_threshold:
                    tag_result = TagResult(
                        tag=tag_name,  # 修正字段名
                        confidence=float(prob),
                        category=TagCategory.CHARACTER
                    )
                    all_tags.append(tag_result)
                    character_tags.append(tag_result)
                
                # 一般标签
                elif tag_name in self.general_tags and prob > general_threshold:
                    tag_result = TagResult(
                        tag=tag_name,  # 修正字段名
                        confidence=float(prob),
                        category=TagCategory.GENERAL
                    )
                    all_tags.append(tag_result)
                    general_tags.append(tag_result)
            
            # 转换为字典格式
            character_dict = {tag.tag: tag.confidence for tag in character_tags}
            general_dict = {tag.tag: tag.confidence for tag in general_tags}
            
            return ImageTagResult(
                image_path="",  # 将在调用时设置
                character_tags=character_dict,
                general_tags=general_dict,
                rating_tags=ratings,
                copyright_tags={},  # 暂时为空
                artist_tags={},     # 暂时为空
                confidence_score=sum(tag.confidence for tag in all_tags) / len(all_tags) if all_tags else 0.0,
                processing_time=0.0  # 将在调用时设置
            )
            
        except Exception as e:
            logger.error(f"图片标注失败: {e}")
            raise
    
    def batch_tag_images(self, images: List[Image.Image], 
                        filenames: List[str] = None,
                        general_threshold: float = 0.35,
                        character_threshold: float = 0.75,
                        batch_size: int = 16) -> List[ImageTagResult]:
        """批量标注图片"""
        results = []
        filenames = filenames or [f"image_{i}.jpg" for i in range(len(images))]
        
        try:
            for i in range(0, len(images), batch_size):
                batch_images = images[i:i + batch_size]
                batch_filenames = filenames[i:i + batch_size]
                batch_tensors = []
                
                # 预处理批次
                for image in batch_images:
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    tensor = self.transform(image)
                    batch_tensors.append(tensor)
                
                # 批量推理
                batch_input = torch.stack(batch_tensors).to(self.device)
                with torch.no_grad():
                    outputs = self.model(batch_input)
                    probs_batch = torch.sigmoid(outputs).cpu().numpy()
                
                # 处理每张图片的结果
                for j, (probs, filename) in enumerate(zip(probs_batch, batch_filenames)):
                    all_tags = []
                    character_tags = []
                    general_tags = []
                    ratings = {}
                    
                    for k, prob in enumerate(probs):
                        tag_name = self.tag_names[k]
                        
                        # 评级标签
                        if tag_name in ['general', 'sensitive', 'questionable', 'explicit']:
                            ratings[tag_name] = float(prob)
                            continue
                        
                        # 角色标签
                        if tag_name in self.character_tags and prob > character_threshold:
                            tag_result = TagResult(
                                tag=tag_name,  # 修正字段名
                                confidence=float(prob),
                                category=TagCategory.CHARACTER
                            )
                            all_tags.append(tag_result)
                            character_tags.append(tag_result)
                        
                        # 一般标签
                        elif tag_name in self.general_tags and prob > general_threshold:
                            tag_result = TagResult(
                                tag=tag_name,  # 修正字段名
                                confidence=float(prob),
                                category=TagCategory.GENERAL
                            )
                            all_tags.append(tag_result)
                            general_tags.append(tag_result)
                    
                    # 转换为字典格式
                    character_dict = {tag.tag: tag.confidence for tag in character_tags}
                    general_dict = {tag.tag: tag.confidence for tag in general_tags}
                    
                    result = ImageTagResult(
                        image_path=filename,
                        character_tags=character_dict,
                        general_tags=general_dict,
                        rating_tags=ratings,
                        copyright_tags={},  # 暂时为空
                        artist_tags={},     # 暂时为空
                        confidence_score=sum(tag.confidence for tag in all_tags) / len(all_tags) if all_tags else 0.0,
                        processing_time=0.0  # 将在处理完成后设置
                    )
                    results.append(result)
                    
                logger.info(f"已处理 {min(i + batch_size, len(images))}/{len(images)} 张图片")
            
            return results
            
        except Exception as e:
            logger.error(f"批量标注失败: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'total_tags': len(self.tag_names),
            'general_tags_count': len(self.general_tags),
            'character_tags_count': len(self.character_tags)
        }

# 全局单例实例
_tagger_instance = None

def get_wd_tagger() -> WDTaggerService:
    """获取WD Tagger服务实例（单例模式）"""
    global _tagger_instance
    if _tagger_instance is None:
        _tagger_instance = WDTaggerService()
    return _tagger_instance
