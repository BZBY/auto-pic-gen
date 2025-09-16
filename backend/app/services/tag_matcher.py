"""标签直接匹配服务 - 基于WD标签的精确匹配"""
from typing import List, Dict, Set, Optional, Tuple
import logging
from collections import defaultdict

from ..models.tag_models import ImageTagResult, TagMatchRequest, TagMatchResult, TagCategory

logger = logging.getLogger(__name__)

class DirectTagMatcher:
    """基于WD标签的直接匹配器"""
    
    def __init__(self):
        pass
    
    def match_single_image(self, image_tags: ImageTagResult, 
                          match_request: TagMatchRequest) -> TagMatchResult:
        """对单张图片进行标签匹配"""
        
        # 提取图片的标签名称和置信度
        image_tag_dict = {tag.name: tag.confidence for tag in image_tags.tags}
        character_tag_dict = {tag.name: tag.confidence for tag in image_tags.character_tags}
        general_tag_dict = {tag.name: tag.confidence for tag in image_tags.general_tags}
        
        # 1. 检查必须包含的标签
        matched_required = []
        for required_tag in match_request.required_tags:
            if required_tag in image_tag_dict:
                # 根据标签类型使用不同的阈值
                threshold = (match_request.character_tag_threshold 
                           if required_tag in character_tag_dict 
                           else match_request.general_tag_threshold)
                
                if image_tag_dict[required_tag] >= threshold:
                    matched_required.append(required_tag)
        
        # 2. 检查角色标签要求
        matched_character = []
        for char_tag in match_request.character_tags:
            if char_tag in character_tag_dict:
                if character_tag_dict[char_tag] >= match_request.character_tag_threshold:
                    matched_character.append(char_tag)
        
        # 3. 检查排除标签
        excluded_found = []
        for excluded_tag in match_request.excluded_tags:
            if excluded_tag in image_tag_dict:
                threshold = (match_request.character_tag_threshold 
                           if excluded_tag in character_tag_dict 
                           else match_request.general_tag_threshold)
                
                if image_tag_dict[excluded_tag] >= threshold:
                    excluded_found.append(excluded_tag)
        
        # 4. 检查评级要求
        ratings = image_tags.ratings
        rating_pass = True
        
        # 检查general评级最小值
        if ratings.get('general', 0) < match_request.min_rating_general:
            rating_pass = False
        
        # 检查sensitive评级最大值
        if ratings.get('sensitive', 0) > match_request.max_rating_sensitive:
            rating_pass = False
        
        # 5. 计算匹配结果
        required_match = (len(matched_required) == len(match_request.required_tags) 
                         if match_request.required_tags else True)
        
        character_match = (len(matched_character) == len(match_request.character_tags) 
                          if match_request.character_tags else True)
        
        no_excluded = len(excluded_found) == 0
        
        # 总体匹配判断
        is_matched = required_match and character_match and no_excluded and rating_pass
        
        # 计算匹配得分
        score = self._calculate_match_score(
            matched_required, match_request.required_tags,
            matched_character, match_request.character_tags,
            excluded_found, match_request.excluded_tags,
            ratings, match_request
        )
        
        return TagMatchResult(
            matched=is_matched,
            score=score,
            matched_required_tags=matched_required,
            matched_character_tags=matched_character,
            excluded_tags_found=excluded_found,
            rating_scores=ratings
        )
    
    def _calculate_match_score(self, matched_required: List[str], required_tags: List[str],
                              matched_character: List[str], character_tags: List[str],
                              excluded_found: List[str], excluded_tags: List[str],
                              ratings: Dict[str, float], match_request: TagMatchRequest) -> float:
        """计算匹配得分"""
        score = 0.0
        
        # 必需标签得分 (40%)
        if required_tags:
            required_score = len(matched_required) / len(required_tags)
            score += required_score * 0.4
        else:
            score += 0.4  # 没有必需标签要求时给满分
        
        # 角色标签得分 (30%)
        if character_tags:
            character_score = len(matched_character) / len(character_tags)
            score += character_score * 0.3
        else:
            score += 0.3  # 没有角色标签要求时给满分
        
        # 排除标签得分 (20%) - 找到排除标签会扣分
        if excluded_tags:
            excluded_penalty = len(excluded_found) / len(excluded_tags)
            score += (1.0 - excluded_penalty) * 0.2
        else:
            score += 0.2  # 没有排除标签时给满分
        
        # 评级得分 (10%)
        rating_score = 0.0
        general_score = min(ratings.get('general', 0) / match_request.min_rating_general, 1.0)
        sensitive_penalty = max(0, 1.0 - ratings.get('sensitive', 0) / match_request.max_rating_sensitive)
        rating_score = (general_score + sensitive_penalty) / 2
        score += rating_score * 0.1
        
        return min(score, 1.0)
    
    def find_matching_frames(self, frames_with_tags: List[Tuple[any, ImageTagResult]], 
                           match_request: TagMatchRequest) -> List[Tuple[any, TagMatchResult]]:
        """在帧列表中找到匹配的帧"""
        matching_results = []
        
        for frame_data, image_tags in frames_with_tags:
            match_result = self.match_single_image(image_tags, match_request)
            
            if match_result.matched:
                matching_results.append((frame_data, match_result))
        
        # 按匹配得分排序
        matching_results.sort(key=lambda x: x[1].score, reverse=True)
        
        return matching_results
    
    def create_reference_match_request(self, reference_tags: List[ImageTagResult],
                                     min_confidence: float = 0.7) -> TagMatchRequest:
        """根据参考图片自动创建匹配请求"""
        
        # 统计所有参考图片中的标签
        tag_counts = defaultdict(list)
        character_tag_counts = defaultdict(list)
        rating_stats = defaultdict(list)
        
        for ref_tags in reference_tags:
            # 收集标签统计
            for tag in ref_tags.tags:
                tag_counts[tag.name].append(tag.confidence)
                if tag.category == TagCategory.CHARACTER:
                    character_tag_counts[tag.name].append(tag.confidence)
            
            # 收集评级统计
            for rating_name, rating_value in ref_tags.ratings.items():
                rating_stats[rating_name].append(rating_value)
        
        # 选择高频且高置信度的标签作为必需标签
        required_tags = []
        character_tags = []
        
        # 必需标签：在大部分参考图片中出现且平均置信度高
        for tag_name, confidences in tag_counts.items():
            if len(confidences) >= len(reference_tags) * 0.6:  # 至少60%的参考图片包含
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence >= min_confidence:
                    if tag_name in character_tag_counts:
                        character_tags.append(tag_name)
                    else:
                        required_tags.append(tag_name)
        
        # 计算评级要求
        general_ratings = rating_stats.get('general', [0.5])
        sensitive_ratings = rating_stats.get('sensitive', [0.3])
        
        min_general = min(general_ratings) * 0.8  # 稍微放宽要求
        max_sensitive = max(sensitive_ratings) * 1.2  # 稍微放宽要求
        
        return TagMatchRequest(
            required_tags=required_tags,
            character_tags=character_tags,
            excluded_tags=[],  # 可以后续手动添加
            min_rating_general=max(min_general, 0.5),  # 最低0.5
            max_rating_sensitive=min(max_sensitive, 0.5),  # 最高0.5
            character_tag_threshold=0.75,
            general_tag_threshold=0.35
        )
    
    def analyze_tag_distribution(self, frames_with_tags: List[Tuple[any, ImageTagResult]]) -> Dict:
        """分析标签分布，帮助用户了解数据"""
        
        tag_stats = defaultdict(lambda: {'count': 0, 'confidences': [], 'category': None})
        rating_stats = defaultdict(list)
        
        for frame_data, image_tags in frames_with_tags:
            # 统计标签
            for tag in image_tags.tags:
                tag_stats[tag.name]['count'] += 1
                tag_stats[tag.name]['confidences'].append(tag.confidence)
                tag_stats[tag.name]['category'] = tag.category.value
            
            # 统计评级
            for rating_name, rating_value in image_tags.ratings.items():
                rating_stats[rating_name].append(rating_value)
        
        # 计算统计信息
        result = {
            'total_frames': len(frames_with_tags),
            'tag_distribution': {},
            'rating_distribution': {},
            'most_common_tags': [],
            'character_tags': [],
            'general_tags': []
        }
        
        # 处理标签统计
        for tag_name, stats in tag_stats.items():
            avg_confidence = sum(stats['confidences']) / len(stats['confidences'])
            frequency = stats['count'] / len(frames_with_tags)
            
            tag_info = {
                'count': stats['count'],
                'frequency': frequency,
                'avg_confidence': avg_confidence,
                'category': stats['category']
            }
            
            result['tag_distribution'][tag_name] = tag_info
            
            if stats['category'] == 'character':
                result['character_tags'].append((tag_name, tag_info))
            elif stats['category'] == 'general':
                result['general_tags'].append((tag_name, tag_info))
        
        # 排序最常见标签
        sorted_tags = sorted(tag_stats.items(), 
                           key=lambda x: (x[1]['count'], sum(x[1]['confidences'])/len(x[1]['confidences'])), 
                           reverse=True)
        result['most_common_tags'] = [(name, tag_stats[name]) for name, _ in sorted_tags[:20]]
        
        # 处理评级统计
        for rating_name, values in rating_stats.items():
            result['rating_distribution'][rating_name] = {
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
        
        return result

# 全局单例实例
_matcher_instance = None

def get_tag_matcher() -> DirectTagMatcher:
    """获取标签匹配器实例（单例模式）"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = DirectTagMatcher()
    return _matcher_instance
