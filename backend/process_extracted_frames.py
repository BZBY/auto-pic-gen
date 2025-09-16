#!/usr/bin/env python3
"""
处理已提取帧的脚本 - 跳过提取步骤，直接进行标注和后续处理
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List
import logging
from PIL import Image

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.video_models import ExtractedFrame, ProcessingConfig
from app.services.wd_tagger import get_wd_tagger
from app.services.tag_matcher import get_tag_matcher
from app.models.tag_models import ImageTagResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_extracted_frames(directory: str) -> List[ExtractedFrame]:
    """扫描目录中已提取的帧文件"""
    frame_dir = Path(directory)
    if not frame_dir.exists():
        logger.error(f"目录不存在: {directory}")
        return []
    
    frames = []
    image_files = list(frame_dir.glob("*.jpg")) + list(frame_dir.glob("*.png"))
    image_files.sort()  # 按文件名排序
    
    logger.info(f"发现 {len(image_files)} 个图片文件")
    
    for i, img_path in enumerate(image_files):
        try:
            # 获取文件信息
            file_size = img_path.stat().st_size
            
            # 尝试从文件名解析帧索引（如果有的话）
            frame_index = i  # 默认使用序号
            timestamp = i * 2.0  # 假设每2秒一帧
            
            # 尝试从文件名提取更精确的信息
            filename = img_path.stem
            if "_" in filename:
                parts = filename.split("_")
                if len(parts) >= 2 and parts[-1].isdigit():
                    frame_index = int(parts[-1])
                    timestamp = frame_index / 30.0  # 假设30fps
            
            # 获取图片尺寸
            with Image.open(img_path) as img:
                width, height = img.size
            
            frame = ExtractedFrame(
                frame_id=f"frame_{i:04d}",
                frame_index=frame_index,
                timestamp=timestamp,
                image_path=str(img_path),
                scene_change_score=0.5,  # 默认值
                quality_score=0.7,      # 默认值
                width=width,
                height=height,
                file_size=file_size
            )
            
            frames.append(frame)
            
        except Exception as e:
            logger.warning(f"处理文件失败 {img_path}: {e}")
            continue
    
    logger.info(f"成功加载 {len(frames)} 个帧")
    return frames

async def process_frames_with_wd_tagger(frames: List[ExtractedFrame], 
                                      config: ProcessingConfig) -> List[ImageTagResult]:
    """使用WD标签器处理帧"""
    logger.info(f"开始标注 {len(frames)} 张图片")
    
    # 获取WD标签器
    wd_tagger = get_wd_tagger()
    
    # 加载图片
    frame_images = []
    frame_filenames = []
    
    for frame in frames:
        img_path = Path(frame.image_path)
        if img_path.exists():
            try:
                image = Image.open(img_path)
                frame_images.append(image)
                frame_filenames.append(img_path.name)
            except Exception as e:
                logger.warning(f"加载图片失败 {img_path}: {e}")
                continue
    
    logger.info(f"成功加载 {len(frame_images)} 张图片")
    
    # 批量标注
    try:
        frame_tag_results = wd_tagger.batch_tag_images(
            images=frame_images,
            filenames=frame_filenames,
            general_threshold=config.general_tag_threshold,
            character_threshold=config.character_tag_threshold,
            batch_size=config.batch_size
        )
        
        logger.info(f"标注完成，得到 {len(frame_tag_results)} 个结果")
        return frame_tag_results
        
    except Exception as e:
        logger.error(f"批量标注失败: {e}")
        return []

def save_results(frames: List[ExtractedFrame], 
                tag_results: List[ImageTagResult],
                output_dir: str):
    """保存处理结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存标签结果到JSON
    import json
    
    results_data = []
    for i, (frame, tag_result) in enumerate(zip(frames, tag_results)):
        result = {
            "frame_id": frame.frame_id,
            "frame_index": frame.frame_index,
            "timestamp": frame.timestamp,
            "image_path": frame.image_path,
            "scene_change_score": frame.scene_change_score,
            "quality_score": frame.quality_score,
            "width": frame.width,
            "height": frame.height,
            "file_size": frame.file_size,
            "tags": {
                "general": tag_result.general_tags,
                "character": tag_result.character_tags,
                "rating": tag_result.rating_tags
            }
        }
        results_data.append(result)
    
    # 保存到文件
    results_file = output_path / "tagging_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"结果已保存到: {results_file}")
    
    # 生成统计报告
    report_file = output_path / "processing_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("视频帧处理报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"总帧数: {len(frames)}\n")
        f.write(f"标注帧数: {len(tag_results)}\n")
        f.write(f"平均质量得分: {sum(f.quality_score for f in frames) / len(frames):.3f}\n")
        f.write(f"平均场景变化得分: {sum(f.scene_change_score for f in frames) / len(frames):.3f}\n")
        
        # 统计最常见的标签
        all_tags = {}
        for tag_result in tag_results:
            for tag_name, confidence in tag_result.general_tags.items():
                if confidence > 0.5:  # 只统计高置信度标签
                    all_tags[tag_name] = all_tags.get(tag_name, 0) + 1
        
        f.write("\n最常见的标签 (置信度 > 0.5):\n")
        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
        for tag_name, count in sorted_tags[:20]:  # 显示前20个
            f.write(f"  {tag_name}: {count} 次\n")
    
    logger.info(f"报告已保存到: {report_file}")

async def main():
    """主函数"""
    print("🎬 处理已提取帧的脚本")
    print("=" * 50)
    
    # 获取输入参数
    if len(sys.argv) < 2:
        print("用法: python process_extracted_frames.py <帧目录> [输出目录]")
        print("示例: python process_extracted_frames.py E:/Git_my/auto-pic-gen/backend/outputs/video_1_103932-1080p")
        sys.exit(1)
    
    frame_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else f"{frame_directory}_processed"
    
    print(f"📂 帧目录: {frame_directory}")
    print(f"📁 输出目录: {output_directory}")
    print()
    
    try:
        # 1. 扫描已提取的帧
        print("📋 步骤1: 扫描帧文件...")
        frames = scan_extracted_frames(frame_directory)
        if not frames:
            print("❌ 没有找到有效的帧文件")
            sys.exit(1)
        
        # 2. 配置处理参数
        config = ProcessingConfig(
            max_frames=200,
            scene_change_threshold=0.15,
            quality_threshold=0.5,
            tag_threshold=0.35,
            character_tag_threshold=0.75,
            general_tag_threshold=0.35,
            batch_size=8  # 降低批处理大小避免内存问题
        )
        
        # 3. 进行WD标注
        print("🏷️  步骤2: WD标签标注...")
        tag_results = await process_frames_with_wd_tagger(frames, config)
        if not tag_results:
            print("❌ 标注失败")
            sys.exit(1)
        
        # 4. 保存结果
        print("💾 步骤3: 保存结果...")
        save_results(frames, tag_results, output_directory)
        
        print("✅ 处理完成!")
        print(f"📊 处理了 {len(frames)} 帧，标注了 {len(tag_results)} 帧")
        print(f"📁 结果保存在: {output_directory}")
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
