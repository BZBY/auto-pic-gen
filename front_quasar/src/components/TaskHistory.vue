<template>
  <q-card class="task-history-card">
    <q-card-section>
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6 text-weight-medium">
          📜 处理历史
        </div>
        <div class="row q-gutter-sm">
          <q-btn
            @click="refreshHistory"
            icon="refresh"
            size="sm"
            flat
            round
            color="primary"
          />
          <q-btn
            @click="clearHistory"
            icon="clear_all"
            size="sm"
            flat
            round
            color="negative"
            v-if="tasks.length > 0"
          />
        </div>
      </div>

      <!-- 历史任务列表 -->
      <div v-if="tasks.length === 0" class="text-center text-grey-6 q-py-lg">
        <q-icon name="history" size="48px" class="q-mb-sm" />
        <div>暂无处理历史</div>
      </div>

      <q-list v-else separator>
        <q-item
          v-for="task in tasks"
          :key="task.task_id"
          class="q-pa-md"
        >
          <q-item-section avatar>
            <q-avatar 
              :color="getStatusColor(task.status)" 
              text-color="white" 
              :icon="getStatusIcon(task.status)"
            />
          </q-item-section>

          <q-item-section>
            <q-item-label class="text-weight-medium">
              任务 {{ task.task_id.substring(0, 8) }}...
            </q-item-label>
            <q-item-label caption>
              {{ formatTime(task.start_time) }}
            </q-item-label>
            <q-item-label caption v-if="task.current_step">
              {{ task.current_step }}
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <div class="column items-end q-gutter-xs">
              <q-chip 
                :color="getStatusColor(task.status)"
                text-color="white"
                size="sm"
              >
                {{ getStatusText(task.status) }}
              </q-chip>
              
              <q-linear-progress
                v-if="task.status === 'processing'"
                :value="task.progress / 100"
                color="primary"
                size="4px"
                class="q-mt-xs"
                style="width: 100px"
              />
              
              <div class="text-caption text-grey-6">
                {{ Math.round(task.progress) }}%
              </div>
            </div>
          </q-item-section>

          <q-item-section side>
            <q-btn
              v-if="task.status === 'processing'"
              @click="cancelTask(task.task_id)"
              icon="stop"
              size="sm"
              flat
              round
              color="negative"
            />
            <q-btn
              v-else-if="task.status === 'completed'"
              @click="viewResults(task.task_id)"
              icon="visibility"
              size="sm"
              flat
              round
              color="primary"
            />
          </q-item-section>
        </q-item>
      </q-list>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { videoApi } from '../services/api';
import type { ProcessingStatus } from '../types';

// interface Props {
//   currentTask?: ProcessingStatus | null;
// }

// 暂时不使用props，但保留接口定义以备将来扩展
// const props = defineProps<Props>();

const emit = defineEmits<{
  'cancel-task': [taskId: string];
  'view-results': [taskId: string];
}>();

const tasks = ref<ProcessingStatus[]>([]);
const loading = ref(false);

// 生命周期
onMounted(() => {
  void refreshHistory();
});

// 方法
const refreshHistory = async () => {
  try {
    loading.value = true;
    const allTasks = await videoApi.getAllTasks();
    
    // 排序：进行中的任务在前，然后按时间倒序
    tasks.value = allTasks.sort((a, b) => {
      // 进行中的任务优先
      if (a.status === 'processing' && b.status !== 'processing') return -1;
      if (b.status === 'processing' && a.status !== 'processing') return 1;
      
      // 按开始时间倒序
      return new Date(b.start_time).getTime() - new Date(a.start_time).getTime();
    });
    
  } catch (error) {
    console.error('获取历史任务失败:', error);
  } finally {
    loading.value = false;
  }
};

const clearHistory = () => {
  if (!confirm('确定要清空所有历史记录吗？')) return;
  
  try {
    // 这里可以添加清空历史的API调用
    // 目前只是清空本地显示，将来可以添加服务器端清空
    tasks.value = [];
  } catch (error) {
    console.error('清空历史失败:', error);
  }
};

const cancelTask = async (taskId: string) => {
  emit('cancel-task', taskId);
  await refreshHistory();
};

const viewResults = (taskId: string) => {
  emit('view-results', taskId);
};

// 工具函数
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'pending': return 'orange';
    case 'processing': return 'blue';
    case 'completed': return 'green';
    case 'failed': return 'red';
    case 'cancelled': return 'grey';
    default: return 'grey';
  }
};

const getStatusIcon = (status: string): string => {
  switch (status) {
    case 'pending': return 'schedule';
    case 'processing': return 'play_arrow';
    case 'completed': return 'check_circle';
    case 'failed': return 'error';
    case 'cancelled': return 'cancel';
    default: return 'help';
  }
};

const getStatusText = (status: string): string => {
  switch (status) {
    case 'pending': return '等待中';
    case 'processing': return '处理中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'cancelled': return '已取消';
    default: return '未知';
  }
};

const formatTime = (timeStr: string): string => {
  try {
    const date = new Date(timeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return timeStr;
  }
};

// 暴露刷新方法给父组件
defineExpose({
  refreshHistory
});
</script>

<style scoped>
.task-history-card {
  height: 100%;
  max-height: 500px;
  overflow-y: auto;
}

.q-item {
  border-radius: 8px;
  margin-bottom: 4px;
}

.q-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}
</style>
