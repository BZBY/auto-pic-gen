// API服务
import axios from 'axios';
import { 
  VideoProcessRequest, 
  ProcessingStatus, 
  VideoInfo,
  ImageTagResult,
  TagMatchRequest 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

export const videoApi = {
  // 开始视频处理
  async startProcessing(request: VideoProcessRequest): Promise<{ task_id: string }> {
    const response = await api.post('/api/video/process', request);
    return response.data;
  },

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<ProcessingStatus> {
    const response = await api.get(`/api/video/status/${taskId}`);
    return response.data;
  },

  // 获取所有任务
  async getAllTasks(): Promise<ProcessingStatus[]> {
    const response = await api.get('/api/video/tasks');
    return response.data;
  },

  // 取消任务
  async cancelTask(taskId: string): Promise<{ success: boolean }> {
    const response = await api.delete(`/api/video/task/${taskId}`);
    return response.data;
  },

  // 获取视频信息
  async getVideoInfo(videoPath: string): Promise<{ video_info: VideoInfo }> {
    const response = await api.get('/api/video/info', {
      params: { video_path: videoPath }
    });
    return response.data;
  },

  // 验证文件路径
  async validateFilePath(filePath: string, fileType: string = 'video'): Promise<{
    valid: boolean;
    path: string;
    type: string;
    error?: string;
  }> {
    const response = await api.get('/api/video/validate-path', {
      params: { file_path: filePath, file_type: fileType }
    });
    return response.data;
  }
};

export const tagsApi = {
  // 分析单张图片
  async analyzeSingleImage(
    imagePath: string, 
    generalThreshold: number = 0.35,
    characterThreshold: number = 0.75
  ): Promise<ImageTagResult> {
    const response = await api.post('/api/tags/analyze-image', null, {
      params: {
        image_path: imagePath,
        general_threshold: generalThreshold,
        character_threshold: characterThreshold
      }
    });
    return response.data;
  },

  // 批量分析图片
  async analyzeMultipleImages(
    imagePaths: string[],
    generalThreshold: number = 0.35,
    characterThreshold: number = 0.75
  ): Promise<ImageTagResult[]> {
    const response = await api.post('/api/tags/analyze-images', {
      image_paths: imagePaths,
      general_threshold: generalThreshold,
      character_threshold: characterThreshold
    });
    return response.data;
  },

  // 根据参考图片创建匹配请求
  async createMatchRequest(
    referenceImagePaths: string[],
    minConfidence: number = 0.7
  ): Promise<{
    match_request: TagMatchRequest;
    reference_analysis: ImageTagResult[];
  }> {
    const response = await api.post('/api/tags/create-match-request', {
      reference_image_paths: referenceImagePaths,
      min_confidence: minConfidence
    });
    return response.data;
  },

  // 获取模型信息
  async getModelInfo(): Promise<{
    model_name: string;
    device: string;
    total_tags: number;
    general_tags_count: number;
    character_tags_count: number;
  }> {
    const response = await api.get('/api/tags/model-info');
    return response.data.model_info;
  },

  // 测试标签匹配
  async testMatch(
    testImagePath: string,
    matchRequest: TagMatchRequest
  ): Promise<{
    image_tags: ImageTagResult;
    match_result: any;
  }> {
    const response = await api.post('/api/tags/test-match', {
      test_image_path: testImagePath,
      ...matchRequest
    });
    return response.data;
  }
};

export const systemApi = {
  // 健康检查
  async healthCheck(): Promise<{
    status: string;
    model_loaded: boolean;
    model_info: any;
    config: any;
  }> {
    const response = await api.get('/api/health');
    return response.data;
  },

  // 获取系统配置
  async getConfig(): Promise<{
    processing_config: any;
    supported_video_formats: string[];
    supported_image_formats: string[];
    model_name: string;
    device: string;
  }> {
    const response = await api.get('/api/config');
    return response.data;
  }
};

export default api;
