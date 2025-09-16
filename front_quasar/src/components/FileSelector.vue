<template>
  <div class="q-mb-md">
    <q-label v-if="label" class="text-weight-medium q-mb-sm">
      {{ label }}{{ required ? ' *' : '' }}
    </q-label>

    <!-- 视频文件选择 -->
    <div v-if="mode === 'video'" class="q-gutter-sm">
      <!-- 文件路径显示 -->
      <q-chip
        v-for="(path, index) in videoPaths"
        :key="index"
        removable
        @remove="removeVideoPath(index)"
        color="primary"
        text-color="white"
      >
        {{ getFileName(path) }}
      </q-chip>

      <!-- 添加视频按钮 -->
      <div class="row q-gutter-sm">
        <q-btn
          @click="selectVideoFiles"
          label="选择视频文件"
          icon="video_file"
          color="primary"
          outline
          size="sm"
        />
        <q-btn
          @click="selectVideoDirectory"
          label="选择视频目录"
          icon="folder"
          color="secondary"
          outline
          size="sm"
        />
      </div>

      <!-- 手动输入路径 -->
      <q-input
        v-model="manualPath"
        label="或手动输入路径"
        placeholder="C:/Videos/video.mp4 或 C:/Videos/"
        outlined
        dense
      >
        <template #append>
          <q-btn
            @click="addManualPath"
            icon="add"
            flat
            round
            size="sm"
            :disable="!manualPath.trim()"
          />
        </template>
      </q-input>
    </div>

    <!-- 输出目录选择 -->
    <div v-else-if="mode === 'output'" class="q-gutter-sm">
      <q-input
        :model-value="typeof modelValue === 'string' ? modelValue : ''"
        @update:model-value="(value) => $emit('update:modelValue', String(value || ''))"
        :label="inputLabel"
        :placeholder="placeholder"
        :required="required"
        outlined
      >
        <template #append>
          <q-btn
            @click="selectOutputDirectory"
            icon="folder_open"
            flat
            round
            size="sm"
          />
        </template>
      </q-input>

      <q-btn
        @click="autoGenerateOutputPath"
        label="自动生成输出目录"
        icon="auto_fix_high"
        color="positive"
        outline
        size="sm"
        :disable="!hasVideoPaths"
      />
    </div>

    <!-- 参考图片选择 -->
    <div v-else-if="mode === 'reference'" class="q-gutter-sm">
      <q-input
        :model-value="typeof modelValue === 'string' ? modelValue : ''"
        @update:model-value="(value) => $emit('update:modelValue', String(value || ''))"
        :label="inputLabel"
        :placeholder="placeholder"
        outlined
        dense
      >
        <template #append>
          <q-btn
            @click="selectImageFile"
            icon="image"
            flat
            round
            size="sm"
          />
        </template>
      </q-input>
    </div>

    <!-- 帮助文本 -->
    <div v-if="helpText" class="text-grey-6 text-caption q-mt-xs">
      {{ helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
// 简单的路径处理函数，替代Node.js的path模块
const path = {
  basename: (filePath: string) => {
    return filePath.split(/[\\/]/).pop() || filePath;
  },
  dirname: (filePath: string) => {
    const parts = filePath.split(/[\\/]/);
    parts.pop();
    return parts.join('/') || '/';
  },
  join: (...paths: string[]) => {
    return paths.join('/').replace(/\/+/g, '/');
  }
};

interface Props {
  modelValue?: string | string[];
  label?: string;
  placeholder?: string;
  required?: boolean;
  mode: 'video' | 'output' | 'reference';
  videoPaths?: string[]; // 用于输出目录自动生成
}

// 定义emit类型，根据模式返回不同类型
type EmitValue = string | string[];

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  placeholder: '',
  required: false,
  videoPaths: () => []
});

const emit = defineEmits<{
  'update:modelValue': [value: EmitValue];
}>();

const manualPath = ref('');

// 计算属性
const hasVideoPaths = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue.length > 0 : false
);

const videoPaths = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue : []
);

const inputLabel = computed(() => props.label);

const helpText = computed(() => {
  switch (props.mode) {
    case 'video':
      return '支持选择多个视频文件或整个视频目录';
    case 'output':
      return '选择处理结果的输出目录';
    case 'reference':
      return '选择参考图片文件';
    default:
      return '';
  }
});

// 方法
const getFileName = (filePath: string) => {
  return path.basename(filePath);
};

const removeVideoPath = (index: number) => {
  const newPaths = [...videoPaths.value];
  newPaths.splice(index, 1);
  emit('update:modelValue', newPaths);
};

const addManualPath = () => {
  if (!manualPath.value.trim()) return;

  const newPaths = [...videoPaths.value, manualPath.value.trim()];
  emit('update:modelValue', newPaths);
  manualPath.value = '';
};

// 使用浏览器的文件选择API
const selectVideoFiles = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.accept = '.mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v';

  input.onchange = (event) => {
    const files = (event.target as HTMLInputElement).files;
    if (files) {
      const filePaths = Array.from(files).map(file => file.name); // 在浏览器中只能获取文件名
      const newPaths = [...videoPaths.value, ...filePaths];
      emit('update:modelValue', newPaths);
    }
  };

  input.click();
};

const selectVideoDirectory = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.webkitdirectory = true; // 支持目录选择
  input.multiple = true;

  input.onchange = (event) => {
    const files = (event.target as HTMLInputElement).files;
    if (files) {
      // 获取目录路径（取第一个文件的路径去掉文件名）
      const firstFile = files[0];
      if (firstFile) {
        const dirPath = firstFile.webkitRelativePath.split('/')[0] || ''; // 获取目录名
        if (dirPath) {
          const newPaths = [...videoPaths.value, dirPath];
          emit('update:modelValue', newPaths);
        }
      }
    }
  };

  input.click();
};

const selectOutputDirectory = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.webkitdirectory = true;

  input.onchange = (event) => {
    const files = (event.target as HTMLInputElement).files;
    if (files && files[0]) {
      const dirPath = files[0].webkitRelativePath.split('/')[0] || '';
      if (dirPath) {
        emit('update:modelValue', dirPath);
      }
    }
  };

  input.click();
};

const selectImageFile = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.jpg,.jpeg,.png,.gif,.bmp,.webp';

  input.onchange = (event) => {
    const files = (event.target as HTMLInputElement).files;
    if (files && files[0]) {
      emit('update:modelValue', files[0].name);
    }
  };

  input.click();
};

const autoGenerateOutputPath = () => {
  if (videoPaths.value.length === 0) return;

  // 获取第一个视频的目录
  const firstVideoPath = videoPaths.value[0];
  if (!firstVideoPath) return;

  const videoDir = path.dirname(firstVideoPath);
  const outputDir = path.join(videoDir, 'extracted_dataset');

  emit('update:modelValue', outputDir);
};
</script>