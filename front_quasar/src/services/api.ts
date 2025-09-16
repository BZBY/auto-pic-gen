// API服务
import { api } from 'boot/axios';
import type {
  VideoProcessRequest,
  ProcessingStatus,
  VideoInfo,
  ImageTagResult,
  TagMatchRequest
} from '../types';

// 批量处理返回类型
interface BatchProcessingResult {
  success: boolean;
  task_ids: string[];
  main_task_id: string;
  total_videos: number;
  processed_videos: string[];
  output_directory: string;
  message: string;
}

// 单任务处理返回类型（向后兼容）
interface SingleProcessingResult {
  task_id: string;
}

export const videoApi = {
  // 上传视频文件
  async uploadVideo(file: File): Promise<{
    success: boolean;
    filename: string;
    file_path: string;
    temp_filename: string;
    file_size: number;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/video/upload-video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 上传图片文件
  async uploadImage(file: File): Promise<{
    success: boolean;
    filename: string;
    file_path: string;
    temp_filename: string;
    file_size: number;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/video/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 删除临时文件
  async deleteTempFile(filename: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/api/video/temp-file/${filename}`);
    return response.data;
  },

  // 列出临时文件
  async listTempFiles(): Promise<{
    success: boolean;
    files: Array<{
      filename: string;
      size: number;
      created_time: number;
    }>;
    total_count: number;
  }> {
    const response = await api.get('/api/video/temp-files');
    return response.data;
  },

  // 开始视频处理
  async startProcessing(request: VideoProcessRequest): Promise<BatchProcessingResult | SingleProcessingResult> {
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
    match_result: unknown;
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
    model_info: unknown;
    config: unknown;
  }> {
    const response = await api.get('/api/health');
    return response.data;
  },

  // 获取系统配置
  async getConfig(): Promise<{
    processing_config: unknown;
    supported_video_formats: string[];
    supported_image_formats: string[];
    model_name: string;
    device: string;
  }> {
    const response = await api.get('/api/config');
    return response.data;
  }
};