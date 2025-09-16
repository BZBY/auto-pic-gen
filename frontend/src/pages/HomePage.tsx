import React, { useState, useEffect } from 'react';
import { videoApi, systemApi } from '../services/api';
import { VideoProcessRequest, ProcessingConfig, ProcessingStatus as ProcessingStatusType } from '../types';
import FilePathInput from '../components/FilePathInput';
import ProcessingStatus from '../components/ProcessingStatus';

const HomePage: React.FC = () => {
  const [videoPath, setVideoPath] = useState('');
  const [referencePaths, setReferencePaths] = useState<string[]>(['']);
  const [outputDirectory, setOutputDirectory] = useState('');
  const [config, setConfig] = useState<ProcessingConfig>({
    max_frames: 200,
    scene_change_threshold: 0.3,
    quality_threshold: 0.6,
    tag_threshold: 0.35,
    character_tag_threshold: 0.75,
    general_tag_threshold: 0.35,
    batch_size: 16
  });
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTask, setCurrentTask] = useState<ProcessingStatusType | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentTask && currentTask.status === 'processing') {
      interval = setInterval(async () => {
        try {
          const status = await videoApi.getTaskStatus(currentTask.task_id);
          setCurrentTask(status);
          if (status.status !== 'processing') {
            setIsProcessing(false);
          }
        } catch (error) {
          console.error('获取任务状态失败:', error);
        }
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [currentTask]);

  const checkSystemHealth = async () => {
    try {
      const health = await systemApi.healthCheck();
      setSystemStatus(health);
    } catch (error) {
      console.error('系统健康检查失败:', error);
    }
  };

  const addReferencePath = () => {
    setReferencePaths([...referencePaths, '']);
  };

  const removeReferencePath = (index: number) => {
    setReferencePaths(referencePaths.filter((_, i) => i !== index));
  };

  const updateReferencePath = (index: number, value: string) => {
    const newPaths = [...referencePaths];
    newPaths[index] = value;
    setReferencePaths(newPaths);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validReferencePaths = referencePaths.filter(path => path.trim());
    
    const request: VideoProcessRequest = {
      video_path: videoPath,
      reference_image_paths: validReferencePaths,
      output_directory: outputDirectory,
      config: config
    };

    try {
      setIsProcessing(true);
      const result = await videoApi.startProcessing(request);
      
      // 立即获取任务状态
      const status = await videoApi.getTaskStatus(result.task_id);
      setCurrentTask(status);
    } catch (error) {
      console.error('启动处理失败:', error);
      setIsProcessing(false);
      alert('启动处理失败: ' + (error as any).response?.data?.detail || (error as Error).message);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await videoApi.cancelTask(taskId);
      setCurrentTask(null);
      setIsProcessing(false);
    } catch (error) {
      console.error('取消任务失败:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 页面标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            视频人物训练集提取系统
          </h1>
          <p className="text-gray-600">
            基于WD标签匹配的智能视频帧提取和人物数据集生成
          </p>
        </div>

        {/* 系统状态 */}
        {systemStatus && (
          <div className={`mb-6 p-4 rounded-lg ${
            systemStatus.status === 'healthy' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center">
              <div className={`h-3 w-3 rounded-full mr-2 ${
                systemStatus.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <span className="font-medium">
                系统状态: {systemStatus.status === 'healthy' ? '正常' : '异常'}
              </span>
            </div>
            {systemStatus.model_info && (
              <p className="text-sm text-gray-600 mt-1">
                模型: {systemStatus.model_info.model_name} | 
                设备: {systemStatus.model_info.device} | 
                标签数: {systemStatus.model_info.total_tags}
              </p>
            )}
          </div>
        )}

        {/* 当前任务状态 */}
        {currentTask && (
          <ProcessingStatus 
            status={currentTask} 
            onCancel={handleCancelTask}
          />
        )}

        {/* 处理表单 */}
        <div className="bg-white shadow rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 视频文件路径 */}
            <FilePathInput
              label="视频文件路径"
              value={videoPath}
              onChange={setVideoPath}
              fileType="video"
              placeholder="例如: C:/Videos/anime_episode.mp4"
              required
            />

            {/* 参考图片路径 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                参考图片路径 (可选)
              </label>
              {referencePaths.map((path, index) => (
                <div key={index} className="flex items-center space-x-2 mb-2">
                  <div className="flex-1">
                    <FilePathInput
                      label=""
                      value={path}
                      onChange={(value) => updateReferencePath(index, value)}
                      fileType="image"
                      placeholder="例如: C:/Images/character_ref.jpg"
                    />
                  </div>
                  {referencePaths.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeReferencePath(index)}
                      className="p-2 text-red-500 hover:text-red-700"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addReferencePath}
                className="mt-2 px-3 py-1 text-sm text-primary-600 hover:text-primary-800 border border-primary-300 rounded hover:bg-primary-50"
              >
                + 添加参考图片
              </button>
            </div>

            {/* 输出目录 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                输出目录 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={outputDirectory}
                onChange={(e) => setOutputDirectory(e.target.value)}
                placeholder="例如: C:/Output/dataset"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                required
              />
            </div>

            {/* 处理配置 */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">处理配置</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">最大帧数</label>
                  <input
                    type="number"
                    value={config.max_frames}
                    onChange={(e) => setConfig({...config, max_frames: parseInt(e.target.value)})}
                    min="1"
                    max="1000"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">场景变化阈值</label>
                  <input
                    type="number"
                    value={config.scene_change_threshold}
                    onChange={(e) => setConfig({...config, scene_change_threshold: parseFloat(e.target.value)})}
                    min="0"
                    max="1"
                    step="0.1"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">质量阈值</label>
                  <input
                    type="number"
                    value={config.quality_threshold}
                    onChange={(e) => setConfig({...config, quality_threshold: parseFloat(e.target.value)})}
                    min="0"
                    max="1"
                    step="0.1"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">角色标签阈值</label>
                  <input
                    type="number"
                    value={config.character_tag_threshold}
                    onChange={(e) => setConfig({...config, character_tag_threshold: parseFloat(e.target.value)})}
                    min="0"
                    max="1"
                    step="0.05"
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>

            {/* 提交按钮 */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isProcessing}
                className={`px-6 py-3 border border-transparent text-base font-medium rounded-md text-white ${
                  isProcessing 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                }`}
              >
                {isProcessing ? '处理中...' : '开始处理'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
