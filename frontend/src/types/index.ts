// 类型定义

export interface VideoInfo {
  filename: string;
  duration: number;
  fps: number;
  total_frames: number;
  width: number;
  height: number;
  file_size: number;
}

export interface FrameQuality {
  overall: number;
  blur: number;
  brightness: number;
  contrast: number;
  noise: number;
}

export interface ExtractedFrame {
  frame_number: number;
  timestamp: number;
  filename: string;
  scene_change: number;
  quality: FrameQuality;
  tags: Record<string, number>;
  width: number;
  height: number;
}

export interface ProcessingConfig {
  max_frames: number;
  scene_change_threshold: number;
  quality_threshold: number;
  tag_threshold: number;
  character_tag_threshold: number;
  general_tag_threshold: number;
  batch_size: number;
}

export interface VideoProcessRequest {
  video_path: string;
  reference_image_paths: string[];
  output_directory: string;
  config: ProcessingConfig;
  output_name?: string;
}

export interface ProcessingStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step: string;
  total_steps: number;
  completed_steps: number;
  start_time: string;
  end_time?: string;
  error_message?: string;
}

export interface ProcessingResult {
  task_id: string;
  video_info: VideoInfo;
  total_extracted_frames: number;
  matched_frames: number;
  output_directory: string;
  processing_time: number;
  config_used: ProcessingConfig;
  frames: ExtractedFrame[];
}

export interface TagResult {
  name: string;
  confidence: number;
  category: 'general' | 'character' | 'rating';
}

export interface ImageTagResult {
  filename: string;
  tags: TagResult[];
  ratings: Record<string, number>;
  character_tags: TagResult[];
  general_tags: TagResult[];
}

export interface TagMatchRequest {
  required_tags: string[];
  excluded_tags: string[];
  character_tags: string[];
  min_rating_general: number;
  max_rating_sensitive: number;
  character_tag_threshold: number;
  general_tag_threshold: number;
}

export interface TagMatchResult {
  matched: boolean;
  score: number;
  matched_required_tags: string[];
  matched_character_tags: string[];
  excluded_tags_found: string[];
  rating_scores: Record<string, number>;
}
