<template>
  <q-page class="q-pa-md">
    <!-- 页面标题 -->
    <div class="text-center q-mb-xl">
      <h1 class="text-h3 text-weight-bold q-mb-sm text-primary">
        🎬 视频人物训练集提取系统
      </h1>
      <p class="text-body1 text-grey-7">
        基于WD标签匹配的智能视频帧提取和人物数据集生成
      </p>
    </div>

    <!-- 系统状态卡片 -->
    <q-card v-if="systemStatus" class="q-mb-md" flat bordered>
      <q-card-section class="row items-center">
        <q-icon
          :name="systemStatus.status === 'healthy' ? 'check_circle' : 'error'"
          :color="systemStatus.status === 'healthy' ? 'green' : 'red'"
          size="md"
          class="q-mr-sm"
        />
        <div class="col">
          <div class="text-subtitle1 text-weight-medium">
            系统状态: {{ systemStatus.status === 'healthy' ? '✅ 正常运行' : '❌ 异常' }}
          </div>
          <div v-if="systemStatus.model_info" class="text-caption text-grey-6">
            📋 模型: {{ systemStatus.model_info.model_name }} | 
            🖥️ 设备: {{ systemStatus.model_info.device }} | 
            🏷️ 标签数: {{ systemStatus.model_info.total_tags }}
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- 当前任务状态 -->
    <processing-status
      v-if="currentTask"
      :status="currentTask"
      @cancel="handleCancelTask"
      class="q-mb-md"
    />

    <!-- 主要处理界面 -->
    <div class="row q-gutter-lg">
      <!-- 左侧：文件上传区域 -->
      <div class="col-12 col-lg-4">
        <q-card class="full-height">
          <q-card-section>
            <div class="text-h6 text-weight-medium q-mb-md">
              📁 文件上传
            </div>
            
            <!-- 视频文件上传 -->
            <file-uploader
              v-model="videoPaths"
              label="🎥 视频文件"
              mode="video"
              :multiple="true"
              required
              class="q-mb-lg"
            />

            <!-- 参考图片上传 -->
            <file-uploader
              v-model="referencePaths"
              label="🖼️ 参考图片 (可选)"
              mode="image"
              :multiple="true"
              class="q-mb-md"
            />

            <q-banner class="bg-blue-1 text-blue-8 q-mb-md" dense>
              <template #avatar>
                <q-icon name="info" color="blue" />
              </template>
              <div class="text-body2">
                💡 提示：上传参考图片可以帮助系统更准确地识别和匹配目标人物
              </div>
            </q-banner>
          </q-card-section>
        </q-card>
      </div>

      <!-- 中间：配置和控制区域 -->
      <div class="col-12 col-lg-4">
        <q-card class="full-height">
          <q-card-section>
            <div class="text-h6 text-weight-medium q-mb-md">
              ⚙️ 处理配置
            </div>

            <q-form @submit="handleSubmit" class="q-gutter-md">
              <!-- 输出目录配置 -->
              <q-input
                v-model="outputDirectory"
                label="📂 输出目录名称"
                placeholder="extracted_dataset"
                outlined
                dense
                hint="将在系统临时目录下创建此文件夹"
              >
                <template #prepend>
                  <q-icon name="folder" />
                </template>
              </q-input>

              <!-- 基础配置 -->
              <div class="row q-gutter-md">
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model.number="config.max_frames"
                    label="📊 最大帧数"
                    type="number"
                    min="10"
                    max="1000"
                    outlined
                    dense
                    hint="提取的最大帧数"
                  />
                </div>
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model.number="config.batch_size"
                    label="🔄 批处理大小"
                    type="number"
                    min="1"
                    max="32"
                    outlined
                    dense
                    hint="同时处理的帧数"
                  />
                </div>
              </div>

              <!-- 高级配置 -->
              <q-expansion-item
                label="🔧 高级配置"
                icon="settings"
                header-class="text-primary"
              >
                <div class="q-pa-md q-gutter-md">
                  <div class="row q-gutter-md">
                    <div class="col-12 col-sm-6">
                      <q-input
                        v-model.number="config.scene_change_threshold"
                        label="🎬 场景变化阈值"
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        outlined
                        dense
                        hint="0-1，越高越严格"
                      />
                    </div>
                    <div class="col-12 col-sm-6">
                      <q-input
                        v-model.number="config.quality_threshold"
                        label="🎯 质量阈值"
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        outlined
                        dense
                        hint="0-1，越高质量要求越高"
                      />
                    </div>
                    <div class="col-12 col-sm-6">
                      <q-input
                        v-model.number="config.character_tag_threshold"
                        label="👤 角色标签阈值"
                        type="number"
                        min="0"
                        max="1"
                        step="0.05"
                        outlined
                        dense
                        hint="0-1，角色识别的置信度"
                      />
                    </div>
                    <div class="col-12 col-sm-6">
                      <q-input
                        v-model.number="config.tag_threshold"
                        label="🏷️ 一般标签阈值"
                        type="number"
                        min="0"
                        max="1"
                        step="0.05"
                        outlined
                        dense
                        hint="0-1，一般标签的置信度"
                      />
                    </div>
                  </div>
                </div>
              </q-expansion-item>

              <!-- 提交按钮 -->
              <div class="q-pt-lg">
                <q-btn
                  type="submit"
                  :loading="isProcessing"
                  :disable="isProcessing || videoPaths.length === 0"
                  color="primary"
                  size="lg"
                  class="full-width"
                  icon="play_arrow"
                >
                  <span v-if="isProcessing">
                    🔄 处理中...
                  </span>
                  <span v-else>
                    🚀 开始处理 ({{ videoPaths.length }} 个视频)
                  </span>
                </q-btn>
                
                <div v-if="videoPaths.length === 0" class="text-center q-mt-sm">
                  <q-chip color="orange" text-color="white" icon="warning">
                    请先上传至少一个视频文件
                  </q-chip>
                </div>
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </div>

      <!-- 右侧：历史记录区域 -->
      <div class="col-12 col-lg-4">
        <task-history
          ref="taskHistoryRef"
          :current-task="currentTask"
          @cancel-task="handleCancelTask"
          @view-results="handleViewResults"
        />
      </div>
    </div>

    <!-- 使用说明 -->
    <q-card class="q-mt-lg" flat bordered>
      <q-card-section>
        <q-expansion-item
          label="📖 使用说明"
          icon="help"
          header-class="text-primary"
        >
          <div class="q-pa-md">
            <div class="text-body1 q-mb-md">
              <strong>📋 操作步骤：</strong>
            </div>
            <q-list>
              <q-item>
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" size="sm">1</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>上传视频文件</q-item-label>
                  <q-item-label caption>支持 MP4, AVI, MKV 等格式，可上传多个视频</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" size="sm">2</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>上传参考图片（可选）</q-item-label>
                  <q-item-label caption>提供目标人物的参考图片，提高匹配准确度</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" size="sm">3</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>调整处理配置</q-item-label>
                  <q-item-label caption>根据需要调整帧数限制、质量阈值等参数</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" size="sm">4</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label>开始处理</q-item-label>
                  <q-item-label caption>点击"开始处理"按钮，系统将自动提取和分析视频帧</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </q-expansion-item>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { videoApi, systemApi } from '../services/api';
import type { VideoProcessRequest, ProcessingConfig, ProcessingStatus as ProcessingStatusType } from '../types';
import FileUploader from '../components/FileUploader.vue';
import ProcessingStatus from '../components/ProcessingStatus.vue';
import TaskHistory from '../components/TaskHistory.vue';

// 响应式数据
const videoPaths = ref<string[]>([]);
const referencePaths = ref<string[]>([]);
const outputDirectory = ref('extracted_dataset');
const config = ref<ProcessingConfig>({
  max_frames: 200,
  scene_change_threshold: 0.15,  // 降低场景变化阈值
  quality_threshold: 0.5,        // 降低质量阈值
  tag_threshold: 0.35,
  character_tag_threshold: 0.75,
  general_tag_threshold: 0.35,
  batch_size: 16
});

const isProcessing = ref(false);
const currentTask = ref<ProcessingStatusType | null>(null);
const taskHistoryRef = ref<InstanceType<typeof TaskHistory>>();
const systemStatus = ref<{
  status: string;
  model_loaded: boolean;
  model_info: {
    model_name: string;
    device: string;
    total_tags: number;
  } | undefined;
} | null>(null);

// 生命周期
onMounted(() => {
  void checkSystemHealth();
});

// 监听视频文件变化
watch(
  () => videoPaths.value,
  (newPaths) => {
    console.log('视频文件列表更新:', newPaths);
  },
  { deep: true }
);

// 监听任务状态变化
watch(
  () => currentTask.value,
  (newTask) => {
    if (newTask && newTask.status === 'processing') {
      const interval = setInterval(() => {
        void (async () => {
          try {
            const status = await videoApi.getTaskStatus(newTask.task_id);
            currentTask.value = status;
            if (status.status !== 'processing') {
              isProcessing.value = false;
              clearInterval(interval);
              // 刷新历史记录
              taskHistoryRef.value?.refreshHistory();
            }
          } catch (error) {
            console.error('获取任务状态失败:', error);
            clearInterval(interval);
          }
        })();
      }, 2000);
    }
  },
  { deep: true }
);

// 方法
const checkSystemHealth = async () => {
  try {
    const health = await systemApi.healthCheck();
    // 类型转换以匹配我们定义的类型
    systemStatus.value = {
      status: health.status,
      model_loaded: health.model_loaded,
      model_info: health.model_info as {
        model_name: string;
        device: string;
        total_tags: number;
      } | undefined
    };
  } catch (error) {
    console.error('系统健康检查失败:', error);
  }
};

const handleSubmit = async () => {
  if (videoPaths.value.length === 0) {
    alert('请先上传至少一个视频文件');
    return;
  }

  const validReferencePaths = referencePaths.value.filter(path => path.trim());

  const request: VideoProcessRequest = {
    video_paths: videoPaths.value,
    reference_image_paths: validReferencePaths,
    output_directory: outputDirectory.value,
    config: config.value
  };

  try {
    isProcessing.value = true;
    const result = await videoApi.startProcessing(request);

    // 处理批量任务结果
    if ('task_ids' in result && result.task_ids && result.task_ids.length > 0) {
      // 批量处理模式
      const batchResult = result as {
        task_ids: string[];
        main_task_id: string;
        total_videos: number;
        processed_videos: string[];
        output_directory: string;
        message: string;
      };

      // 使用主任务ID进行状态跟踪
      const mainTaskId = batchResult.main_task_id || batchResult.task_ids[0];
      if (!mainTaskId) {
        throw new Error('未收到有效的任务ID');
      }
      const status = await videoApi.getTaskStatus(mainTaskId);
      currentTask.value = status;

      console.log(`批量处理已开始: ${batchResult.total_videos} 个视频, 主任务ID: ${mainTaskId}`);
    } else if ('task_id' in result && result.task_id) {
      // 兼容旧版单任务返回
      const singleResult = result as { task_id: string };
      const status = await videoApi.getTaskStatus(singleResult.task_id);
      currentTask.value = status;
    } else {
      throw new Error('未收到有效的任务ID');
    }
  } catch (error) {
    console.error('启动处理失败:', error);
    isProcessing.value = false;
    const errorMessage = error instanceof Error
      ? error.message
      : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '未知错误';
    alert('启动处理失败: ' + errorMessage);
  }
};

const handleCancelTask = async (taskId: string) => {
  try {
    await videoApi.cancelTask(taskId);
    currentTask.value = null;
    isProcessing.value = false;
    // 刷新历史记录
    taskHistoryRef.value?.refreshHistory();
  } catch (error) {
    console.error('取消任务失败:', error);
  }
};

const handleViewResults = (taskId: string) => {
  // TODO: 实现查看结果功能
  console.log('查看任务结果:', taskId);
  alert(`查看任务 ${taskId} 的结果（功能开发中）`);
};
</script>