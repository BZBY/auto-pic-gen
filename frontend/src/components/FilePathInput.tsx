import React, { useState, useEffect } from 'react';
import { videoApi } from '../services/api';

interface FilePathInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  fileType: 'video' | 'image';
  placeholder?: string;
  required?: boolean;
}

const FilePathInput: React.FC<FilePathInputProps> = ({
  label,
  value,
  onChange,
  fileType,
  placeholder,
  required = false
}) => {
  const [isValidating, setIsValidating] = useState(false);
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    if (value.trim()) {
      validatePath(value);
    } else {
      setIsValid(null);
      setErrorMessage('');
    }
  }, [value]);

  const validatePath = async (path: string) => {
    setIsValidating(true);
    try {
      const result = await videoApi.validateFilePath(path, fileType);
      setIsValid(result.valid);
      setErrorMessage(result.error || '');
    } catch (error) {
      setIsValid(false);
      setErrorMessage('验证文件路径时出错');
    } finally {
      setIsValidating(false);
    }
  };

  const getStatusIcon = () => {
    if (isValidating) {
      return (
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
      );
    }
    if (isValid === true) {
      return (
        <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    }
    if (isValid === false) {
      return (
        <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      );
    }
    return null;
  };

  const getInputClasses = () => {
    const baseClasses = "mt-1 block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm";
    
    if (isValid === true) {
      return `${baseClasses} border-green-300 bg-green-50`;
    }
    if (isValid === false) {
      return `${baseClasses} border-red-300 bg-red-50`;
    }
    return `${baseClasses} border-gray-300`;
  };

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={getInputClasses()}
          required={required}
        />
        
        {/* 状态图标 */}
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          {getStatusIcon()}
        </div>
      </div>
      
      {/* 错误消息 */}
      {isValid === false && errorMessage && (
        <p className="mt-1 text-sm text-red-600">{errorMessage}</p>
      )}
      
      {/* 帮助文本 */}
      <p className="mt-1 text-xs text-gray-500">
        请输入{fileType === 'video' ? '视频' : '图片'}文件的完整本地路径
      </p>
    </div>
  );
};

export default FilePathInput;
