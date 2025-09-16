# 视频人物训练集提取系统

基于WD标签匹配的智能视频帧提取和人物数据集生成系统。

## 功能特性

✅ **智能帧提取**: 场景变化检测 + 质量评估，避免重复和模糊帧
✅ **WD标签匹配**: 使用EVA02-Large Tagger v3进行精确标签识别
✅ **直接标签匹配**: 基于标签置信度的精确筛选，而非相似度计算
✅ **完整图像保留**: 保持人物完整信息，包含服装、姿态、背景
✅ **本地部署**: 纯本地运行，无需上传文件到服务器
✅ **实时进度**: 异步处理 + 实时状态更新

## 系统架构

```
auto-pic-gen/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 主应用
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 核心服务
│   │   │   ├── wd_tagger.py   # WD标签器
│   │   │   ├── frame_extractor.py # 帧提取
│   │   │   ├── tag_matcher.py # 标签匹配
│   │   │   └── video_processor.py # 视频处理
│   │   ├── api/               # API路由
│   │   └── utils/
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
└── README.md
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- UV (Python包管理器)
- yarn (推荐) 或 npm
- CUDA 支持的GPU (可选，CPU也可运行)

### 快速设置 (推荐)

运行自动环境设置脚本：
```bash
# 一键设置所有环境
setup_env.bat
```

### 手动设置

#### 1. 安装UV (如果未安装)
```bash
pip install uv
```

#### 2. 设置后端环境
```bash
cd backend
uv venv                    # 创建虚拟环境
.venv\Scripts\activate     # 激活虚拟环境 (Windows)
# source .venv/bin/activate  # 激活虚拟环境 (Linux/Mac)
uv pip install -r requirements.txt
```

#### 3. 安装前端依赖
```bash
cd frontend
yarn install
# 或使用 npm install
```

#### 4. 启动后端服务
```bash
cd backend
.venv\Scripts\activate     # 激活虚拟环境
python -m app.main
```

#### 5. 启动前端服务
```bash
cd frontend
yarn start
# 或使用 npm start
```

## 🚀 启动系统

### 方法一：使用启动脚本 (推荐)

1. **首次设置环境**:
   ```bash
   # 双击运行，自动设置所有环境
   setup_env.bat
   ```

2. **启动整个系统**:
   ```bash
   # 双击运行
   start_system.bat
   ```

3. **分别启动**:
   ```bash
   # 先启动后端
   start_backend.bat
   
   # 再启动前端
   start_frontend.bat
   ```

### 方法二：手动启动 (开发者)

1. **启动后端**:
   ```bash
   cd backend
   .venv\Scripts\activate
   python -m app.main
   ```

2. **启动前端**:
   ```bash
   cd frontend
   yarn start
   ```

## 使用方法

### 1. 访问Web界面
打开浏览器访问 `http://localhost:3000`

### 2. 输入文件路径
- **视频文件路径**: 输入本地视频文件的完整路径 (如: `C:/Videos/anime.mp4`)
- **参考图片路径**: 输入参考人物图片的路径 (可选，用于自动匹配)
- **输出目录**: 指定数据集输出目录

### 3. 配置处理参数
- **最大帧数**: 最多提取的帧数 (默认: 200)
- **场景变化阈值**: 场景变化检测敏感度 (默认: 0.3)
- **质量阈值**: 图片质量要求 (默认: 0.6)
- **角色标签阈值**: 角色标签置信度要求 (默认: 0.75)

### 4. 开始处理
点击"开始处理"按钮，系统将：
1. 智能提取视频帧
2. 对所有帧进行WD标注
3. 处理参考图像(如果提供)
4. 基于标签进行精确匹配
5. 导出最终数据集

### 5. 查看结果
处理完成后，输出目录将包含：
- 筛选后的图片文件 (`.jpg`)
- 对应的标签文件 (`.txt`)
- 元数据文件 (`metadata.json`)
- 处理结果 (`processing_result.json`)

## 核心技术

### WD EVA02-Large Tagger v3
- **模型**: `SmilingWolf/wd-eva02-large-tagger-v3`
- **训练数据**: Danbooru 2024年2月最新数据
- **支持标签**: 角色标签、一般标签、评级标签
- **输入尺寸**: 448x448

### 智能帧提取算法
```python
scene_change_score = (1 - hist_correlation) * 0.6 + optical_flow * 0.3 + edge_density * 0.1
```

### 标签匹配策略
- **直接匹配**: 基于标签名称和置信度的精确匹配
- **分类权重**: 角色标签 > 一般标签
- **评级过滤**: 支持general/sensitive评级筛选

## API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 配置选项

### 环境变量
```bash
# 模型配置
WD_MODEL_NAME=SmilingWolf/wd-eva02-large-tagger-v3
DEVICE=cuda  # 或 cpu

# 处理配置
MAX_FRAMES=200
SCENE_CHANGE_THRESHOLD=0.3
QUALITY_THRESHOLD=0.6
TAG_THRESHOLD=0.35
CHARACTER_TAG_THRESHOLD=0.75

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 支持的文件格式
- **视频**: .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm
- **图片**: .jpg, .jpeg, .png, .bmp, .tiff, .webp

## 🔧 开发说明

### UV虚拟环境
本项目使用UV作为Python包管理器，具有以下优势：
- **更快的依赖解析**: 比pip快10-100倍
- **更好的依赖管理**: 自动解决版本冲突
- **统一的接口**: 兼容pip命令

虚拟环境位置：`backend/.venv/`

### Git版本控制
项目已配置完善的`.gitignore`文件，自动排除：
- ✅ UV虚拟环境 (`.venv/`)
- ✅ Node.js依赖 (`node_modules/`)
- ✅ Python缓存文件 (`__pycache__/`)
- ✅ 模型缓存和输出文件
- ✅ IDE配置文件
- ✅ 系统临时文件

安全上传到Git，不会包含大文件和敏感信息。

## 故障排除

### 1. CUDA相关错误
如果遇到CUDA错误，可以：
- 设置环境变量 `DEVICE=cpu` 使用CPU运行
- 确保安装了正确版本的PyTorch

### 2. 模型下载问题
首次运行时会自动下载WD模型，如果网络问题：
- 确保网络连接正常
- 可能需要设置代理或使用镜像源

### 3. 路径问题
- 确保文件路径使用正确的格式 (Windows: `C:/path/to/file`)
- 确保文件确实存在且可访问

### 4. 内存不足
如果处理大视频时内存不足：
- 减少 `max_frames` 参数
- 减少 `batch_size` 参数
- 使用更小的视频文件

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！