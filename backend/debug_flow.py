#!/usr/bin/env python3
"""
调试工具：检查视频处理数据流程
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_temp_files():
    """检查临时文件目录"""
    from app.utils.config import config
    
    print("📁 临时文件检查")
    print("-" * 40)
    print(f"临时目录: {config.TEMP_DIR}")
    print(f"目录存在: {config.TEMP_DIR.exists()}")
    
    if config.TEMP_DIR.exists():
        temp_files = list(config.TEMP_DIR.iterdir())
        print(f"文件数量: {len(temp_files)}")
        
        for i, file_path in enumerate(temp_files, 1):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                print(f"  {i}. {file_path.name} ({file_size} bytes)")
                
                # 检查文件类型
                suffix = file_path.suffix.lower()
                if suffix in config.ALLOWED_VIDEO_EXTENSIONS:
                    print(f"     ✅ 有效视频文件")
                elif suffix in config.ALLOWED_IMAGE_EXTENSIONS:
                    print(f"     ✅ 有效图片文件")
                else:
                    print(f"     ⚠️  未知文件类型: {suffix}")
    else:
        print("❌ 临时目录不存在")
    
    print()

def test_path_validation():
    """测试路径验证功能"""
    from app.utils.config import config
    
    print("🔍 路径验证测试")
    print("-" * 40)
    
    # 测试样例路径
    test_paths = [
        "103932-1080p.mp4",  # 相对路径（临时文件名）
        "QQ20250916-235846.png",  # 相对路径（临时文件名）
        "/absolute/path/video.mp4",  # 绝对路径
        "nonexistent.mp4"  # 不存在的文件
    ]
    
    for path in test_paths:
        print(f"测试路径: {path}")
        
        # 检查是否为绝对路径
        is_abs = os.path.isabs(path)
        print(f"  绝对路径: {is_abs}")
        
        if not is_abs:
            # 构造临时文件路径
            temp_path = config.TEMP_DIR / path
            exists = temp_path.exists()
            print(f"  临时文件路径: {temp_path}")
            print(f"  文件存在: {exists}")
            
            if exists:
                # 验证文件类型
                suffix = temp_path.suffix.lower()
                if suffix in config.ALLOWED_VIDEO_EXTENSIONS:
                    valid = config.validate_file_path(str(temp_path), "video")
                    print(f"  视频文件验证: {valid}")
                elif suffix in config.ALLOWED_IMAGE_EXTENSIONS:
                    valid = config.validate_file_path(str(temp_path), "image")
                    print(f"  图片文件验证: {valid}")
        else:
            # 直接验证绝对路径
            exists = os.path.exists(path)
            print(f"  文件存在: {exists}")
        
        print()

def simulate_request():
    """模拟前端请求"""
    from app.models.video_models import VideoProcessRequest, ProcessingConfig
    
    print("🧪 模拟请求测试")
    print("-" * 40)
    
    # 获取临时目录中的文件
    from app.utils.config import config
    temp_files = list(config.TEMP_DIR.iterdir()) if config.TEMP_DIR.exists() else []
    
    video_files = [f.name for f in temp_files if f.suffix.lower() in config.ALLOWED_VIDEO_EXTENSIONS]
    image_files = [f.name for f in temp_files if f.suffix.lower() in config.ALLOWED_IMAGE_EXTENSIONS]
    
    print(f"发现视频文件: {video_files}")
    print(f"发现图片文件: {image_files}")
    
    if video_files:
        # 创建模拟请求
        request = VideoProcessRequest(
            video_paths=video_files[:1],  # 只取第一个视频
            reference_image_paths=image_files[:1] if image_files else [],  # 只取第一个图片
            output_directory="test_output",
            config=ProcessingConfig()
        )
        
        print("\n📋 模拟请求内容:")
        print(f"  视频路径: {request.video_paths}")
        print(f"  参考图片: {request.reference_image_paths}")
        print(f"  输出目录: {request.output_directory}")
        
        # 模拟路径处理逻辑
        print("\n🔄 路径处理模拟:")
        
        # 处理视频路径
        for i, video_path in enumerate(request.video_paths):
            print(f"  视频 {i+1}: {video_path}")
            if not os.path.isabs(video_path):
                temp_path = os.path.join(str(config.TEMP_DIR), video_path)
                if os.path.exists(temp_path):
                    print(f"    ✅ 转换为: {temp_path}")
                    print(f"    验证结果: {config.validate_file_path(temp_path, 'video')}")
                else:
                    print(f"    ❌ 文件不存在: {temp_path}")
        
        # 处理参考图片路径
        for i, ref_path in enumerate(request.reference_image_paths):
            print(f"  图片 {i+1}: {ref_path}")
            if not os.path.isabs(ref_path):
                temp_path = os.path.join(str(config.TEMP_DIR), ref_path)
                if os.path.exists(temp_path):
                    print(f"    ✅ 转换为: {temp_path}")
                    print(f"    验证结果: {config.validate_file_path(temp_path, 'image')}")
                else:
                    print(f"    ❌ 文件不存在: {temp_path}")
    else:
        print("❌ 没有找到视频文件进行测试")

def main():
    """主函数"""
    print("🔧 视频处理系统调试工具")
    print("=" * 50)
    
    try:
        check_temp_files()
        test_path_validation()
        simulate_request()
        
        print("✅ 调试完成")
        
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
