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
        :label="getDisplayName(path)"
      />

      <!-- 文件选择区域 -->
      <div class="row q-gutter-sm q-mb-sm">
        <q-btn
          label="选择视频文件"
          icon="video_file"
          color="primary"
          outline
          size="sm"
          @click="openFileDialog('video')"
        />
        <q-btn
          label="选择视频目录"
          icon="folder"
          color="secondary"
          outline
          size="sm"
          @click="openFileDialog('directory')"
        />
      </div>

      <!-- 手动输入区域 -->
      <q-expansion-item
        label="手动输入路径"
        icon="edit"
        header-class="text-primary"
      >
        <q-card>
          <q-card-section>
            <q-input
              v-model="manualInput"
              label="文件或目录路径"
              placeholder="例如: C:\Videos\anime.mp4 或 C:\Videos\"
              outlined
              dense
              hint="支持绝对路径，如 C:\Videos\ 或 /home/user/videos/"
            >
              <template #append>
                <q-btn
                  @click="addManualPath"
                  icon="add"
                  flat
                  round
                  size="sm"
                  :disable="!manualInput.trim()"
                  color="primary"
                />
              </template>
            </q-input>

            <!-- 批量输入 -->
            <q-separator class="q-my-md" />
            <q-input
              v-model="batchInput"
              type="textarea"
              label="批量输入（每行一个路径）"
              placeholder="C:\Videos\video1.mp4&#10;C:\Videos\video2.mp4&#10;D:\Movies\"
              outlined
              rows="3"
              hint="每行输入一个文件或目录路径"
            >
              <template #append>
                <q-btn
                  @click="addBatchPaths"
                  icon="playlist_add"
                  flat
                  round
                  size="sm"
                  :disable="!batchInput.trim()"
                  color="secondary"
                />
              </template>
            </q-input>
          </q-card-section>
        </q-card>
      </q-expansion-item>
    </div>

    <!-- 输出目录选择 -->
    <div v-else-if="mode === 'output'" class="q-gutter-sm">
      <q-input
        :model-value="typeof modelValue === 'string' ? modelValue : ''"
        @update:model-value="(value) => $emit('update:modelValue', String(value || ''))"
        label="输出目录路径"
        placeholder="例如: C:\Output\dataset"
        outlined
        hint="选择处理结果的输出目录"
      >
        <template #append>
          <q-btn
            @click="openFileDialog('output-directory')"
            icon="folder_open"
            flat
            round
            size="sm"
            color="primary"
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
        class="q-mt-sm"
      />
    </div>

    <!-- 参考图片选择 -->
    <div v-else-if="mode === 'reference'" class="q-gutter-sm">
      <q-input
        :model-value="typeof modelValue === 'string' ? modelValue : ''"
        @update:model-value="(value) => $emit('update:modelValue', String(value || ''))"
        label="参考图片路径"
        placeholder="例如: C:\Images\character.jpg"
        outlined
        dense
        hint="选择用于匹配的参考图片"
      >
        <template #append>
          <q-btn
            @click="openFileDialog('image')"
            icon="image"
            flat
            round
            size="sm"
            color="primary"
          />
        </template>
      </q-input>
    </div>

    <!-- 隐藏的文件输入元素 -->
    <input
      ref="fileInput"
      type="file"
      style="display: none"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

// 扩展File接口以支持path属性（Electron环境）
interface ExtendedFile extends File {
  path?: string;
}

interface Props {
  modelValue?: string | string[];
  label?: string;
  required?: boolean;
  mode: 'video' | 'output' | 'reference';
  videoPaths?: string[];
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  required: false,
  videoPaths: () => []
});

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]];
}>();

const fileInput = ref<HTMLInputElement>();
const manualInput = ref('');
const batchInput = ref('');
const currentMode = ref<'video' | 'directory' | 'image' | 'output-directory'>('video');

// 计算属性
const hasVideoPaths = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue.length > 0 : false
);

const videoPaths = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue : []
);

// 工具函数
const getDisplayName = (filePath: string) => {
  // 获取文件名或目录名
  const parts = filePath.replace(/\\/g, '/').split('/');
  return parts[parts.length - 1] || filePath;
};

const getDirectory = (filePath: string) => {
  const parts = filePath.replace(/\\/g, '/').split('/');
  parts.pop();
  return parts.join('/') || '/';
};

// 文件选择方法
const openFileDialog = (mode: 'video' | 'directory' | 'image' | 'output-directory') => {
  if (!fileInput.value) return;

  currentMode.value = mode;
  const input = fileInput.value;

  // 重置input
  input.value = '';

  // 设置文件选择参数
  switch (mode) {
    case 'video':
      input.multiple = true;
      input.webkitdirectory = false;
      input.accept = '.mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v,.ts,.m2ts';
      break;
    case 'directory':
      input.multiple = true;
      input.webkitdirectory = true;
      input.accept = '';
      break;
    case 'image':
      input.multiple = false;
      input.webkitdirectory = false;
      input.accept = '.jpg,.jpeg,.png,.gif,.bmp,.webp,.tiff,.svg';
      break;
    case 'output-directory':
      input.multiple = true;
      input.webkitdirectory = true;
      input.accept = '';
      break;
  }

  input.click();
};

const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;

  switch (currentMode.value) {
    case 'video': {
      const videoPaths = Array.from(files).map(file => {
        const extendedFile = file as ExtendedFile;
        return extendedFile.path || file.webkitRelativePath || file.name;
      }).filter((path): path is string => Boolean(path));

      const currentPaths = Array.isArray(props.modelValue) ? props.modelValue : [];
      const newVideoPaths = [...currentPaths, ...videoPaths];
      emit('update:modelValue', newVideoPaths);
      break;
    }

    case 'directory': {
      if (files[0]) {
        const extendedFile = files[0] as ExtendedFile;
        const dirPath = extendedFile.path ?
          getDirectory(extendedFile.path) :
          files[0].webkitRelativePath.split('/')[0] || '';

        if (dirPath) {
          const currentPaths = Array.isArray(props.modelValue) ? props.modelValue : [];
          const newPaths = [...currentPaths, dirPath];
          emit('update:modelValue', newPaths);
        }
      }
      break;
    }

    case 'image': {
      if (files[0]) {
        const extendedFile = files[0] as ExtendedFile;
        const imagePath = extendedFile.path || files[0].name;
        emit('update:modelValue', imagePath);
      }
      break;
    }

    case 'output-directory': {
      if (files[0]) {
        const extendedFile = files[0] as ExtendedFile;
        const dirPath = extendedFile.path ?
          getDirectory(extendedFile.path) :
          files[0].webkitRelativePath.split('/')[0] || '';

        if (dirPath) {
          emit('update:modelValue', dirPath);
        }
      }
      break;
    }
  }
};

// 手动输入方法
const addManualPath = () => {
  if (!manualInput.value.trim()) return;

  if (props.mode === 'video') {
    const newPaths = [...videoPaths.value, manualInput.value.trim()];
    emit('update:modelValue', newPaths);
  } else {
    emit('update:modelValue', manualInput.value.trim());
  }

  manualInput.value = '';
};

const addBatchPaths = () => {
  if (!batchInput.value.trim()) return;

  const paths = batchInput.value
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);

  if (paths.length > 0) {
    const newPaths = [...videoPaths.value, ...paths];
    emit('update:modelValue', newPaths);
  }

  batchInput.value = '';
};

const removeVideoPath = (index: number) => {
  const newPaths = [...videoPaths.value];
  newPaths.splice(index, 1);
  emit('update:modelValue', newPaths);
};

const autoGenerateOutputPath = () => {
  if (videoPaths.value.length === 0) return;

  const firstVideoPath = videoPaths.value[0];
  if (!firstVideoPath) return;

  const videoDir = getDirectory(firstVideoPath);
  const outputDir = `${videoDir}/extracted_dataset`;

  emit('update:modelValue', outputDir);
};
</script>