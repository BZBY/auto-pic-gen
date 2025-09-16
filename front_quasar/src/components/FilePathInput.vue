<template>
  <div class="q-mb-md">
    <q-input
      :model-value="modelValue"
      @update:model-value="(value: string | number | null) => $emit('update:modelValue', String(value || ''))"
      :label="label + (required ? ' *' : '')"
      :placeholder="placeholder"
      :required="required"
      :color="getInputColor()"
      :bg-color="getInputBgColor()"
      :loading="isValidating"
      outlined
    >
      <template #append>
        <q-icon
          v-if="!isValidating && isValid !== null"
          :name="isValid ? 'check_circle' : 'error'"
          :color="isValid ? 'positive' : 'negative'"
        />
      </template>
    </q-input>

    <!-- 错误消息 -->
    <div v-if="isValid === false && errorMessage" class="text-negative text-caption q-mt-xs">
      {{ errorMessage }}
    </div>

    <!-- 帮助文本 -->
    <div class="text-grey-6 text-caption q-mt-xs">
      请输入{{ fileType === 'video' ? '视频' : '图片' }}文件的完整本地路径
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { videoApi } from '../services/api';

interface Props {
  modelValue: string;
  label: string;
  fileType: 'video' | 'image';
  placeholder?: string;
  required?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  required: false
});

defineEmits<{
  'update:modelValue': [value: string];
}>();

const isValidating = ref(false);
const isValid = ref<boolean | null>(null);
const errorMessage = ref('');

// 监听值变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue?.trim()) {
      void validatePath(newValue);
    } else {
      isValid.value = null;
      errorMessage.value = '';
    }
  },
  { immediate: true }
);

const validatePath = async (path: string) => {
  isValidating.value = true;
  try {
    const result = await videoApi.validateFilePath(path, props.fileType);
    isValid.value = result.valid;
    errorMessage.value = result.error || '';
  } catch {
    isValid.value = false;
    errorMessage.value = '验证文件路径时出错';
  } finally {
    isValidating.value = false;
  }
};

const getInputColor = () => {
  if (isValid.value === true) return 'positive';
  if (isValid.value === false) return 'negative';
  return 'primary';
};

const getInputBgColor = () => {
  if (isValid.value === true) return 'light-green-1';
  if (isValid.value === false) return 'red-1';
  return undefined;
};
</script>