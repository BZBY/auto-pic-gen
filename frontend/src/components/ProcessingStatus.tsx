import React from 'react';
import { ProcessingStatus as ProcessingStatusType } from '../types';

interface ProcessingStatusProps {
  status: ProcessingStatusType;
  onCancel?: (taskId: string) => void;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ status, onCancel }) => {
  const getStatusColor = (statusValue: string) => {
    switch (statusValue) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
    const start = new Date(status.start_time);
    const end = status.end_time ? new Date(status.end_time) : new Date();
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

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(status.status)}`}>
            {getStatusText(status.status)}
          </span>
          <span className="text-sm text-gray-500">任务ID: {status.task_id.slice(0, 8)}...</span>
        </div>
        
        {status.status === 'processing' && onCancel && (
          <button
            onClick={() => onCancel(status.task_id)}
            className="px-3 py-1 text-sm text-red-600 hover:text-red-800 border border-red-300 rounded hover:bg-red-50"
          >
            取消任务
          </button>
        )}
      </div>

      {/* 进度条 */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>进度</span>
          <span>{Math.round(status.progress * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${status.progress * 100}%` }}
          ></div>
        </div>
      </div>

      {/* 当前步骤 */}
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-1">当前步骤</p>
        <p className="text-sm font-medium">{status.current_step}</p>
        <p className="text-xs text-gray-500">
          步骤 {status.completed_steps} / {status.total_steps}
        </p>
      </div>

      {/* 时间信息 */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-600">开始时间</p>
          <p className="font-medium">{formatTime(status.start_time)}</p>
        </div>
        <div>
          <p className="text-gray-600">
            {status.end_time ? '结束时间' : '运行时间'}
          </p>
          <p className="font-medium">
            {status.end_time ? formatTime(status.end_time) : calculateDuration()}
          </p>
        </div>
      </div>

      {/* 错误信息 */}
      {status.error_message && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-600">
            <span className="font-medium">错误信息：</span>
            {status.error_message}
          </p>
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;
