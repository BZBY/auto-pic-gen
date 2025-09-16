"""标签相关API路由"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from PIL import Image
import logging

from ..models.tag_models import TagMatchRequest, ImageTagResult
from ..services.wd_tagger import get_wd_tagger
from ..services.tag_matcher import get_tag_matcher
from ..utils.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tags", tags=["tags"])

# 获取服务实例
wd_tagger = get_wd_tagger()
tag_matcher = get_tag_matcher()

@router.post("/analyze-image", response_model=ImageTagResult)
async def analyze_single_image(
    image_path: str,
    general_threshold: float = 0.35,
    character_threshold: float = 0.75
):
    """分析单张图片的标签"""
    try:
        if not config.validate_file_path(image_path, "image"):
            raise HTTPException(status_code=400, detail="无效的图片文件路径")
        
        image = Image.open(image_path)
        result = wd_tagger.tag_single_image(
            image=image,
            general_threshold=general_threshold,
            character_threshold=character_threshold
        )
        result.filename = image_path
        
        return result
    except Exception as e:
        logger.error(f"分析图片标签失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze-images", response_model=List[ImageTagResult])
async def analyze_multiple_images(
    image_paths: List[str],
    general_threshold: float = 0.35,
    character_threshold: float = 0.75
):
    """批量分析图片标签"""
    try:
        # 验证所有路径
        for path in image_paths:
            if not config.validate_file_path(path, "image"):
                raise HTTPException(status_code=400, detail=f"无效的图片文件路径: {path}")
        
        # 加载图片
        images = []
        for path in image_paths:
            image = Image.open(path)
            images.append(image)
        
        # 批量分析
        results = wd_tagger.batch_tag_images(
            images=images,
            filenames=image_paths,
            general_threshold=general_threshold,
            character_threshold=character_threshold
        )
        
        return results
    except Exception as e:
        logger.error(f"批量分析图片标签失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-match-request")
async def create_match_request_from_references(
    reference_image_paths: List[str],
    min_confidence: float = 0.7
):
    """根据参考图片自动创建匹配请求"""
    try:
        # 验证路径
        for path in reference_image_paths:
            if not config.validate_file_path(path, "image"):
                raise HTTPException(status_code=400, detail=f"无效的图片文件路径: {path}")
        
        # 分析参考图片
        reference_results = []
        for path in reference_image_paths:
            image = Image.open(path)
            result = wd_tagger.tag_single_image(image)
            result.filename = path
            reference_results.append(result)
        
        # 创建匹配请求
        match_request = tag_matcher.create_reference_match_request(
            reference_results, min_confidence
        )
        
        return {
            "success": True,
            "match_request": match_request,
            "reference_analysis": reference_results
        }
    except Exception as e:
        logger.error(f"创建匹配请求失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/model-info")
async def get_model_info():
    """获取WD Tagger模型信息"""
    try:
        info = wd_tagger.get_model_info()
        return {
            "success": True,
            "model_info": info
        }
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-match")
async def test_tag_matching(
    test_image_path: str,
    match_request: TagMatchRequest
):
    """测试标签匹配"""
    try:
        if not config.validate_file_path(test_image_path, "image"):
            raise HTTPException(status_code=400, detail="无效的图片文件路径")
        
        # 分析测试图片
        image = Image.open(test_image_path)
        image_tags = wd_tagger.tag_single_image(image)
        image_tags.filename = test_image_path
        
        # 进行匹配
        match_result = tag_matcher.match_single_image(image_tags, match_request)
        
        return {
            "success": True,
            "image_tags": image_tags,
            "match_result": match_result
        }
    except Exception as e:
        logger.error(f"测试标签匹配失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
