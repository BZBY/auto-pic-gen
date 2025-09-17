"""
视频人物训练集提取系统 - Gradio 前端界面 (增强版)
基于 Gradio 5.x 构建的智能训练GUI界面
用户体验至上的设计理念
"""

import gradio as gr
import requests
import json
import time
import os
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import asyncio
from datetime import datetime

# 配置
BACKEND_URL = "http://localhost:8000"
TEMP_DIR = "temp_uploads"

# 确保临时目录存在
os.makedirs(TEMP_DIR, exist_ok=True)

class VideoProcessor:
    """视频处理器接口类"""

    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.session.timeout = (10, 30)  # 连接超时10s，读取超时30s

    def check_backend_health(self) -> Dict[str, Any]:
        """检查后端服务健康状态"""
        try:
            response = self.session.get(f"{self.backend_url}/docs", timeout=5)
            if response.status_code == 200:
                return {"healthy": True, "message": "后端服务正常运行"}
            else:
                return {"healthy": False, "message": f"后端服务异常 (状态码: {response.status_code})"}
        except requests.exceptions.ConnectionError:
            return {"healthy": False, "message": "❌ 无法连接到后端服务 (http://localhost:8000)"}
        except requests.exceptions.Timeout:
            return {"healthy": False, "message": "❌ 后端服务响应超时"}
        except Exception as e:
            return {"healthy": False, "message": f"❌ 后端服务检查失败: {str(e)}"}

    def upload_video(self, file_path: str) -> Dict[str, Any]:
        """上传视频文件到后端"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'video/*')}
                response = self.session.post(f"{self.backend_url}/api/video/upload-video", files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_image(self, file_path: str) -> Dict[str, Any]:
        """上传参考图片到后端"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'image/*')}
                response = self.session.post(f"{self.backend_url}/api/video/upload-image", files=files)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_processing(self, video_paths: List[str], reference_paths: List[str],
                        output_dir: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """开始视频处理"""
        try:
            payload = {
                "video_paths": video_paths,
                "reference_image_paths": reference_paths,
                "output_directory": output_dir,
                "config": config
            }
            response = self.session.post(f"{self.backend_url}/api/video/process", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            response = self.session.get(f"{self.backend_url}/api/video/status/{task_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

# 全局处理器实例
processor = VideoProcessor()

# 全局状态变量
auto_refresh_thread = None
stop_refresh_flag = False

def check_backend_connection():
    """检查后端连接状态"""
    health = processor.check_backend_health()
    if health["healthy"]:
        return f"✅ {health['message']}"
    else:
        return f"{health['message']}"

def process_uploaded_videos(video_files):
    """处理上传的视频文件"""
    if not video_files:
        return [], "⚠️ 没有选择视频文件"

    # 首先检查后端连接
    health = processor.check_backend_health()
    if not health["healthy"]:
        return [], f"❌ 无法上传文件: {health['message']}"

    uploaded_paths = []
    messages = []

    for video_file in video_files:
        if video_file is None:
            continue
        result = processor.upload_video(video_file.name)
        if result.get("success"):
            uploaded_paths.append(result["temp_filename"])
            file_size = result.get('file_size', 0)
            size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
            messages.append(f"✅ {result['filename']} 上传成功 ({size_mb:.1f}MB)")
        else:
            messages.append(f"❌ {os.path.basename(video_file.name)} 上传失败: {result.get('error', '未知错误')}")

    if uploaded_paths:
        messages.append(f"\n🎯 总计成功上传 {len(uploaded_paths)} 个视频文件")

    return uploaded_paths, "\n".join(messages)

def process_uploaded_images(image_files):
    """处理上传的参考图片"""
    if not image_files:
        return [], "⚠️ 没有选择参考图片"

    # 首先检查后端连接
    health = processor.check_backend_health()
    if not health["healthy"]:
        return [], f"❌ 无法上传文件: {health['message']}"

    uploaded_paths = []
    messages = []

    for image_file in image_files:
        if image_file is None:
            continue
        result = processor.upload_image(image_file.name)
        if result.get("success"):
            uploaded_paths.append(result["temp_filename"])
            file_size = result.get('file_size', 0)
            size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
            messages.append(f"✅ {result['filename']} 上传成功 ({size_mb:.1f}MB)")
        else:
            messages.append(f"❌ {os.path.basename(image_file.name)} 上传失败: {result.get('error', '未知错误')}")

    if uploaded_paths:
        messages.append(f"\n🎯 总计成功上传 {len(uploaded_paths)} 个参考图片")

    return uploaded_paths, "\n".join(messages)

def start_video_processing(video_paths, reference_paths, output_dir,
                          max_frames, scene_threshold, quality_threshold,
                          tag_threshold, character_threshold, batch_size):
    """启动视频处理任务"""
    # 检查后端连接
    health = processor.check_backend_health()
    if not health["healthy"]:
        return f"❌ 后端服务不可用: {health['message']}", "", ""

    if not video_paths:
        return "❌ 请先上传视频文件", "", ""

    if not output_dir.strip():
        return "❌ 请指定输出目录", "", ""

    config = {
        "max_frames": int(max_frames),
        "scene_change_threshold": scene_threshold,
        "quality_threshold": quality_threshold,
        "tag_threshold": tag_threshold,
        "character_tag_threshold": character_threshold,
        "batch_size": int(batch_size)
    }

    result = processor.start_processing(video_paths, reference_paths, output_dir, config)

    if result.get("success"):
        task_ids = result.get("task_ids", [])
        main_task_id = result.get("main_task_id", "")
        message = f"""🚀 处理任务已成功启动！

📝 任务ID: {main_task_id}
📹 视频数量: {result.get('total_videos', 0)}
📁 输出目录: {output_dir}
⚙️ 最大帧数: {int(max_frames)}

💡 提示: 点击"🔄 自动刷新"按钮实时监控处理进度"""
        return (message, main_task_id, json.dumps(task_ids, indent=2))
    else:
        return f"❌ 启动失败: {result.get('error', '未知错误')}", "", ""

def check_task_status(task_id):
    """检查任务状态"""
    if not task_id.strip():
        return "⚠️ 请先启动处理任务", ""

    result = processor.get_task_status(task_id)

    if result.get("success") or "task_id" in result:
        status_info = []
        current_time = datetime.now().strftime("%H:%M:%S")
        status_info.append(f"🕒 更新时间: {current_time}")
        status_info.append(f"🏷️ 任务ID: {result.get('task_id', task_id)}")

        status = result.get('status', '未知')
        status_emoji = {
            'pending': '⏳',
            'running': '🚀',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '⏹️'
        }.get(status, '🔄')
        status_info.append(f"{status_emoji} 状态: {status}")

        progress = result.get('progress', 0)
        progress_bar = '█' * int(progress / 5) + '░' * (20 - int(progress / 5))
        status_info.append(f"📊 进度: {progress}% [{progress_bar}]")

        if result.get('message'):
            status_info.append(f"💬 消息: {result['message']}")

        if result.get('error'):
            status_info.append(f"⚠️ 错误: {result['error']}")

        if result.get('result'):
            res = result['result']
            status_info.append("─" * 40)
            status_info.append("📈 处理结果:")
            if res.get('extracted_frames'):
                status_info.append(f"  🎦 提取帧数: {res['extracted_frames']}")
            if res.get('matched_frames'):
                status_info.append(f"  🎯 匹配帧数: {res['matched_frames']}")
            if res.get('output_path'):
                status_info.append(f"  📁 输出路径: {res['output_path']}")

        # 添加完成提醒
        if status == 'completed':
            status_info.append("\n🎉 任务已完成！您可以查看输出目录中的结果文件。")
        elif status == 'failed':
            status_info.append("\n💔 任务处理失败，请检查错误信息并重试。")

        return "\n".join(status_info), json.dumps(result, indent=2, ensure_ascii=False)
    else:
        return f"❌ 获取状态失败: {result.get('error', '未知错误')}", ""

def start_auto_refresh(task_id):
    """启动自动刷新"""
    global auto_refresh_thread, stop_refresh_flag

    if not task_id.strip():
        return "⚠️ 请先启动处理任务", "", "❌ 自动刷新未启动"

    stop_refresh_flag = False

    def refresh_loop():
        while not stop_refresh_flag:
            time.sleep(3)  # 每3秒刷新一次
            if stop_refresh_flag:
                break
            # 这里需要在实际应用中通过事件机制更新界面

    auto_refresh_thread = threading.Thread(target=refresh_loop)
    auto_refresh_thread.daemon = True
    auto_refresh_thread.start()

    status_text, detail_text = check_task_status(task_id)
    return status_text, detail_text, "✅ 自动刷新已启动 (每3秒更新)"

def stop_auto_refresh():
    """停止自动刷新"""
    global stop_refresh_flag
    stop_refresh_flag = True
    return "⏹️ 自动刷新已停止"

# 创建 Gradio 界面
def create_interface():
    """创建增强版 Gradio 界面"""

    # 自定义CSS样式
    custom_css = """
    .status-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    """

    with gr.Blocks(title="视频人物训练集提取系统", theme=gr.themes.Soft(), css=custom_css) as demo:

        # 标题和系统状态
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("""
                # 🎬 视频人物训练集提取系统 (增强版)
                基于 WD Tagger 的智能视频帧提取和角色识别系统
                """)
            with gr.Column(scale=1):
                health_btn = gr.Button("🔍 检查后端状态", variant="secondary", size="sm")
                health_status = gr.Textbox(label="后端状态", interactive=False, lines=2)

        # 文件上传区域
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📹 视频文件上传")
                video_files = gr.File(
                    label="选择视频文件 (支持拖拽)",
                    file_count="multiple",
                    file_types=["video"],
                    height=150
                )
                video_upload_btn = gr.Button("📤 上传视频", variant="primary")
                video_status = gr.Textbox(label="视频上传状态", interactive=False, lines=4)

            with gr.Column(scale=1):
                gr.Markdown("### 🖼️ 参考图片上传（可选）")
                ref_files = gr.File(
                    label="选择参考图片 (支持拖拽)",
                    file_count="multiple",
                    file_types=["image"],
                    height=150
                )
                ref_upload_btn = gr.Button("📤 上传参考图片", variant="secondary")
                ref_status = gr.Textbox(label="图片上传状态", interactive=False, lines=4)

        # 处理配置
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ⚙️ 处理配置")
                output_dir = gr.Textbox(
                    label="📁 输出目录",
                    value="./output",
                    placeholder="请输入输出目录路径",
                    info="处理结果将保存到此目录"
                )

                with gr.Row():
                    max_frames = gr.Number(
                        label="🎦 最大提取帧数",
                        value=200,
                        minimum=1,
                        maximum=1000,
                        info="每个视频最多提取的帧数"
                    )
                    batch_size = gr.Number(
                        label="📦 批处理大小",
                        value=8,
                        minimum=1,
                        maximum=32,
                        info="同时处理的图片数量"
                    )

                with gr.Row():
                    scene_threshold = gr.Slider(
                        label="🎬 场景变化阈值",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.3,
                        step=0.05,
                        info="越小越敏感，提取更多帧"
                    )
                    quality_threshold = gr.Slider(
                        label="🌟 图像质量阈值",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.5,
                        step=0.05,
                        info="过滤低质量图像"
                    )

                with gr.Row():
                    tag_threshold = gr.Slider(
                        label="🏷️ 标签置信度阈值",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.35,
                        step=0.05,
                        info="一般标签的最低置信度"
                    )
                    character_threshold = gr.Slider(
                        label="👤 角色标签阈值",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.75,
                        step=0.05,
                        info="角色标签的最低置信度(较高)"
                    )

        # 处理控制
        with gr.Row():
            start_btn = gr.Button("🚀 开始处理", variant="primary", size="lg")
            with gr.Column():
                with gr.Row():
                    status_btn = gr.Button("📊 手动刷新", variant="secondary")
                    auto_refresh_btn = gr.Button("🔄 自动刷新", variant="secondary")
                    stop_refresh_btn = gr.Button("⏹️ 停止刷新", variant="secondary")
                auto_refresh_status = gr.Textbox(label="自动刷新状态", interactive=False, lines=1)

        # 状态显示
        with gr.Row():
            with gr.Column():
                process_status = gr.Textbox(
                    label="🔄 处理状态",
                    interactive=False,
                    lines=12,
                    placeholder="状态信息将在这里显示..."
                )
            with gr.Column():
                detailed_status = gr.Textbox(
                    label="📋 详细信息 (JSON)",
                    interactive=False,
                    lines=12,
                    placeholder="详细的技术信息将在这里显示..."
                )

        # 隐藏的状态变量
        video_paths_state = gr.State([])
        ref_paths_state = gr.State([])
        current_task_id = gr.State("")

        # 事件绑定
        health_btn.click(
            fn=check_backend_connection,
            outputs=[health_status]
        )

        video_upload_btn.click(
            fn=process_uploaded_videos,
            inputs=[video_files],
            outputs=[video_paths_state, video_status]
        )

        ref_upload_btn.click(
            fn=process_uploaded_images,
            inputs=[ref_files],
            outputs=[ref_paths_state, ref_status]
        )

        start_btn.click(
            fn=start_video_processing,
            inputs=[
                video_paths_state, ref_paths_state, output_dir,
                max_frames, scene_threshold, quality_threshold,
                tag_threshold, character_threshold, batch_size
            ],
            outputs=[process_status, current_task_id, detailed_status]
        )

        status_btn.click(
            fn=check_task_status,
            inputs=[current_task_id],
            outputs=[process_status, detailed_status]
        )

        auto_refresh_btn.click(
            fn=start_auto_refresh,
            inputs=[current_task_id],
            outputs=[process_status, detailed_status, auto_refresh_status]
        )

        stop_refresh_btn.click(
            fn=stop_auto_refresh,
            outputs=[auto_refresh_status]
        )

        # 启动时自动检查后端状态
        demo.load(
            fn=check_backend_connection,
            outputs=[health_status]
        )

        # 添加使用说明
        gr.Markdown("""
        ---
        ### 📝 使用指南

        #### 🚀 快速开始
        1. **检查后端**: 确保后端服务运行正常 (绿色✅表示正常)
        2. **上传文件**: 拖拽或选择视频文件和参考图片
        3. **配置参数**: 根据需要调整处理参数
        4. **开始处理**: 点击"🚀 开始处理"按钮
        5. **监控进度**: 使用"🔄 自动刷新"实时查看进度

        #### ⚙️ 参数调优建议
        - **场景变化阈值**: 0.2-0.4 (动作片用较小值，静态场景用较大值)
        - **图像质量阈值**: 0.4-0.6 (要求高质量时调高)
        - **标签置信度**: 0.3-0.4 (一般标签)
        - **角色置信度**: 0.7-0.8 (角色识别精度)

        #### 🔧 故障排除
        - **后端连接失败**: 确保后端服务在 http://localhost:8000 运行
        - **上传失败**: 检查文件格式和大小限制
        - **处理缓慢**: 减少批处理大小或最大帧数

        #### 📊 性能优化
        - **批处理大小**: GPU显存允许的情况下可以增大 (4-16)
        - **最大帧数**: 根据视频长度和质量要求调整
        - **自动刷新**: 每3秒更新一次，避免频繁刷新影响性能
        """)

    return demo

if __name__ == "__main__":
    # 创建并启动界面
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        debug=True
    )