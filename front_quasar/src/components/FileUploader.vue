<template>
  <div class="file-uploader q-mb-md">
    <q-label v-if="label" class="text-weight-medium q-mb-sm">
      {{ label }}{{ required ? ' *' : '' }}
    </q-label>

    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{
        'upload-area--dragover': isDragOver,
        'upload-area--disabled': disabled
      }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @click="!disabled && openFileDialog()"
    >
      <div class="upload-content">
        <q-icon
          :name="mode === 'video' ? 'video_file' : 'image'"
          size="48px"
          :color="isDragOver ? 'primary' : 'grey-5'"
        />
        <div class="text-h6 q-mt-sm">
          {{ uploadText }}
        </div>
        <div class="text-body2 text-grey-6">
          {{ hintText }}
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div v-if="uploadedFiles.length > 0" class="q-mt-md">
      <q-list bordered separator>
        <q-item
          v-for="file in uploadedFiles"
          :key="file.temp_filename"
          class="q-pa-md"
        >
          <q-item-section avatar>
            <q-icon
              :name="mode === 'video' ? 'video_file' : 'image'"
              color="primary"
              size="md"
            />
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ file.filename }}</q-item-label>
            <q-item-label caption>
              {{ formatFileSize(file.file_size) }}
              <span v-if="file.uploadProgress !== undefined && file.uploadProgress < 100">
                - 上传中: {{ file.uploadProgress }}%
              </span>
              <span v-else-if="file.uploaded">
                - 已上传
              </span>
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <q-btn
              @click="removeFile(file.temp_filename)"
              icon="delete"
              color="negative"
              flat
              round
              size="sm"
              :disable="file.uploadProgress !== undefined && file.uploadProgress < 100"
            />
          </q-item-section>

          <!-- 上传进度条 -->
          <q-linear-progress
            v-if="file.uploadProgress !== undefined && file.uploadProgress < 100"
            :value="file.uploadProgress / 100"
            color="primary"
            class="absolute-bottom"
            size="2px"
          />
        </q-item>
      </q-list>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      ref="fileInput"
      type="file"
      style="display: none"
      :accept="acceptTypes"
      :multiple="multiple ? true : false"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { videoApi } from '../services/api';

interface UploadedFile {
  filename: string;
  temp_filename: string;
  file_path: string;
  file_size: number;
  uploaded: boolean;
  uploadProgress?: number;
}

interface Props {
  modelValue?: string[];
  label?: string;
  mode: 'video' | 'image';
  required?: boolean;
  multiple?: boolean;
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  label: '',
  required: false,
  multiple: true,
  disabled: false
});

const emit = defineEmits<{
  'update:modelValue': [value: string[]];
}>();

const fileInput = ref<HTMLInputElement>();
const isDragOver = ref(false);
const uploadedFiles = ref<UploadedFile[]>([]);

// 计算属性
const acceptTypes = computed(() => {
  if (props.mode === 'video') {
    return '.mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v';
  } else {
    return '.jpg,.jpeg,.png,.gif,.bmp,.webp,.tiff';
  }
});

const uploadText = computed(() => {
  if (props.disabled) return '已禁用';
  return isDragOver.value 
    ? `释放以上传${props.mode === 'video' ? '视频' : '图片'}` 
    : `点击或拖拽上传${props.mode === 'video' ? '视频' : '图片'}文件`;
});

const hintText = computed(() => {
  if (props.mode === 'video') {
    return '支持 MP4, AVI, MKV, MOV, WMV 等格式';
  } else {
    return '支持 JPG, PNG, GIF, BMP, WebP 等格式';
  }
});

// 监听文件变化，更新modelValue
watch(uploadedFiles, (newFiles) => {
  const filePaths = newFiles
    .filter(file => file.uploaded)
    .map(file => file.temp_filename);
  emit('update:modelValue', filePaths);
}, { deep: true });

// 方法
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const openFileDialog = () => {
  if (props.disabled) return;
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files;
  if (files) {
    void handleFiles(Array.from(files));
  }
};

const handleDrop = (event: DragEvent) => {
  if (props.disabled) return;
  isDragOver.value = false;
  const files = event.dataTransfer?.files;
  if (files) {
    void handleFiles(Array.from(files));
  }
};

const handleFiles = async (files: File[]) => {
  for (const file of files) {
    // 检查文件类型
    const isValidType = props.mode === 'video' 
      ? /\.(mp4|avi|mkv|mov|wmv|flv|webm|m4v)$/i.test(file.name)
      : /\.(jpg|jpeg|png|gif|bmp|webp|tiff)$/i.test(file.name);
    
    if (!isValidType) {
      alert(`不支持的文件格式: ${file.name}`);
      continue;
    }

    // 检查是否已存在（基于文件名和大小）
    const existingFile = uploadedFiles.value.find(f => 
      f.filename === file.name && f.file_size === file.size
    );
    
    if (existingFile) {
      const shouldReplace = confirm(
        `文件 "${file.name}" 已存在（${formatFileSize(file.size)}）。\n是否要替换现有文件？`
      );
      
      if (shouldReplace) {
        // 删除现有文件
        await removeFile(existingFile.temp_filename, false);
      } else {
        continue;
      }
    }

    // 如果不允许多文件，清空现有文件
    if (!props.multiple) {
      // 删除现有文件
      for (const existingFile of uploadedFiles.value) {
        await removeFile(existingFile.temp_filename, false);
      }
      uploadedFiles.value = [];
    }

    // 添加到上传列表
    const uploadingFile: UploadedFile = {
      filename: file.name,
      temp_filename: '',
      file_path: '',
      file_size: file.size,
      uploaded: false,
      uploadProgress: 0
    };

    uploadedFiles.value.push(uploadingFile);

    try {
      // 上传文件
      const result = props.mode === 'video' 
        ? await videoApi.uploadVideo(file)
        : await videoApi.uploadImage(file);

      // 更新文件信息
      const fileIndex = uploadedFiles.value.findIndex(f => f.filename === file.name && !f.uploaded);
      if (fileIndex !== -1) {
        const existingFile = uploadedFiles.value[fileIndex];
        if (existingFile) {
          uploadedFiles.value[fileIndex] = {
            filename: existingFile.filename,
            file_size: existingFile.file_size,
            temp_filename: result.temp_filename,
            file_path: result.file_path,
            uploaded: true,
            uploadProgress: 100
          };
        }
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      // 移除失败的文件
      const fileIndex = uploadedFiles.value.findIndex(f => f.filename === file.name && !f.uploaded);
      if (fileIndex !== -1) {
        uploadedFiles.value.splice(fileIndex, 1);
      }
      alert(`文件上传失败: ${file.name}`);
    }
  }
};

const removeFile = async (tempFilename: string, showConfirm = true) => {
  if (showConfirm && !confirm('确定要删除这个文件吗？')) {
    return;
  }

  try {
    // 从服务器删除临时文件
    if (tempFilename) {
      await videoApi.deleteTempFile(tempFilename);
    }
    
    // 从列表中移除
    const index = uploadedFiles.value.findIndex(f => f.temp_filename === tempFilename);
    if (index !== -1) {
      uploadedFiles.value.splice(index, 1);
    }
  } catch (error) {
    console.error('删除文件失败:', error);
    alert('删除文件失败');
  }
};
</script>

<style scoped>
.upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #1976d2;
  background: #f5f5f5;
}

.upload-area--dragover {
  border-color: #1976d2;
  background: #e3f2fd;
}

.upload-area--disabled {
  cursor: not-allowed;
  opacity: 0.6;
  background: #f0f0f0;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.q-item {
  position: relative;
}
</style>
