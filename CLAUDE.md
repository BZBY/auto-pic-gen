# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a video person dataset extraction system that uses WD (Waifu Diffusion) tagging for intelligent frame extraction and character identification. The system combines computer vision techniques with AI-based image tagging to create training datasets from video files.

## Development Commands

### Environment Setup
- **First-time setup**: Run `setup_env.bat` to automatically configure both Python and Node.js environments
- **Python environment**: Uses UV package manager with virtual environment at `backend/.venv/`
- **Node.js environment**: Uses yarn (preferred) or npm for dependency management

### Running the System
- **Full system**: `start_system.bat` (starts both backend and frontend)
- **Backend only**: `start_backend.bat` (FastAPI server on port 8000)
- **Frontend only**: `start_frontend.bat` (React dev server on port 3000)

### Manual Commands
Backend:
```bash
cd backend
.venv\Scripts\activate
python -m app.main
```

Frontend:
```bash
cd frontend
yarn start  # or npm start
```

### Dependencies
- **Backend**: `cd backend && uv pip install -r requirements.txt`
- **Frontend**: `cd frontend && yarn install`

## Architecture

### Backend (FastAPI + Python)
- **Main app**: `backend/app/main.py` - FastAPI application with CORS setup
- **Core services**:
  - `services/wd_tagger.py` - WD EVA02-Large Tagger v3 model for image labeling
  - `services/frame_extractor.py` - Intelligent video frame extraction with scene change detection
  - `services/tag_matcher.py` - Direct tag matching based on confidence scores
  - `services/video_processor.py` - Main video processing pipeline
- **API routes**: `api/video.py` and `api/tags.py` for video processing and tag management
- **Configuration**: `utils/config.py` for environment variables and settings

### Frontend (React + TypeScript)
- **Tech stack**: React 18, TypeScript, Tailwind CSS, React Query
- **Proxy setup**: Frontend proxies API requests to `http://localhost:8000`
- **UI components**: React with drag-and-drop file upload support

### Key Technologies
- **WD Tagger**: SmilingWolf/wd-eva02-large-tagger-v3 model for anime/character tagging
- **Video processing**: OpenCV for frame extraction and quality assessment
- **AI framework**: PyTorch with Transformers and Timm
- **Scene detection**: Histogram correlation + optical flow + edge density algorithm

## Development Notes

### Package Management
- **Backend**: Uses UV (ultra-fast Python package installer) instead of pip
- **Virtual environment**: Located at `backend/.venv/` (excluded from Git)
- **Frontend**: Prefers yarn over npm for faster dependency resolution

### Model Downloads
- First run automatically downloads the WD tagger model (~2-3GB)
- Models are cached locally and excluded from Git

### API Documentation
- Swagger UI available at `http://localhost:8000/docs`
- ReDoc available at `http://localhost:8000/redoc`

### Processing Pipeline
1. Intelligent frame extraction using scene change detection
2. WD tagging of all extracted frames
3. Optional reference image processing for character matching
4. Tag-based filtering with confidence thresholds
5. Dataset export with images and corresponding tag files

### Environment Variables
Key configuration options in backend:
- `DEVICE`: "cuda" or "cpu" for model inference
- `MAX_FRAMES`: Maximum frames to extract (default: 200)
- `SCENE_CHANGE_THRESHOLD`: Scene detection sensitivity (default: 0.3)
- `TAG_THRESHOLD`: General tag confidence threshold (default: 0.35)
- `CHARACTER_TAG_THRESHOLD`: Character tag confidence threshold (default: 0.75)