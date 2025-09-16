<template>
  <q-card class="q-mb-md">
    <q-card-section>
      <!-- 状态和取消按钮 -->
      <div class="row items-center justify-between q-mb-md">
        <div class="row items-center q-gutter-md">
          <q-chip
            :color="getStatusColor(status.status)"
            text-color="white"
            :label="getStatusText(status.status)"
          />
          <span class="text-grey-6 text-caption">
            任务ID: {{ status.task_id.slice(0, 8) }}...
          </span>
        </div>

        <q-btn
          v-if="status.status === 'processing' && onCancel"
          @click="onCancel(status.task_id)"
          label="取消任务"
          color="negative"
          outline
          size="sm"
        />
      </div>

      <!-- 进度条 -->
      <div class="q-mb-md">
        <div class="row justify-between text-caption text-grey-6 q-mb-xs">
          <span>进度</span>
          <span>{{ Math.round(status.progress * 100) }}%</span>
        </div>
        <q-linear-progress
          :value="status.progress"
          color="primary"
          size="8px"
          rounded
        />
      </div>

      <!-- 当前步骤 -->
      <div class="q-mb-md">
        <div class="text-grey-6 text-caption q-mb-xs">当前步骤</div>
        <div class="text-body2 text-weight-medium q-mb-xs">
          {{ status.current_step }}
        </div>
        <div class="text-caption text-grey-5">
          步骤 {{ status.completed_steps }} / {{ status.total_steps }}
        </div>
      </div>

      <!-- 时间信息 -->
      <div class="row q-gutter-md">
        <div class="col">
          <div class="text-grey-6 text-caption">开始时间</div>
          <div class="text-body2">{{ formatTime(status.start_time) }}</div>
        </div>
        <div class="col">
          <div class="text-grey-6 text-caption">
            {{ status.end_time ? '结束时间' : '运行时间' }}
          </div>
          <div class="text-body2">
            {{ status.end_time ? formatTime(status.end_time) : calculateDuration() }}
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <q-banner
        v-if="status.error_message"
        class="bg-red-1 text-red-8 q-mt-md"
        dense
      >
        <template #avatar>
          <q-icon name="error" color="red" />
        </template>
        <span class="text-weight-medium">错误信息：</span>
        {{ status.error_message }}
      </q-banner>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import type { ProcessingStatus as ProcessingStatusType } from '../types';

interface Props {
  status: ProcessingStatusType;
  onCancel?: (taskId: string) => void;
}

const props = defineProps<Props>();

const getStatusColor = (statusValue: string) => {
  switch (statusValue) {
    case 'pending':
      return 'warning';
    case 'processing':
      return 'primary';
    case 'completed':
      return 'positive';
    case 'failed':
      return 'negative';
    case 'cancelled':
      return 'grey';
    default:
      return 'grey';
  }
};

const getStatusText = (statusValue: string) => {
  switch (statusValue) {
    case 'pending':
      return '等待中';
    case 'processing':
      return '处理中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    case 'cancelled':
      return '已取消';
    default:
      return statusValue;
  }
};

const formatTime = (timeString: string) => {
  return new Date(timeString).toLocaleString('zh-CN');
};

const calculateDuration = () => {
  const start = new Date(props.status.start_time);
  const end = props.status.end_time ? new Date(props.status.end_time) : new Date();
  const duration = Math.floor((end.getTime() - start.getTime()) / 1000);

  if (duration < 60) {
    return `${duration}秒`;
  } else if (duration < 3600) {
    return `${Math.floor(duration / 60)}分${duration % 60}秒`;
  } else {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}小时${minutes}分`;
  }
};
</script>