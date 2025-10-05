import * as React from 'react'
import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  FileText,
  Image,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Cloud
} from 'lucide-react'
import { toast } from 'sonner'

import { cn } from '@/utils/cn'

/**
 * 上传文件接口
 */
export interface UploadFile {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

/**
 * 文档上传组件属性接口
 */
interface DocumentUploadProps {
  onUploadComplete?: (files: File[]) => void
  onUploadError?: (error: string) => void
  onClose?: () => void
  maxFiles?: number
  maxFileSize?: number // MB
  acceptedTypes?: string[]
  className?: string
}

/**
 * 默认接受的文件类型
 */
const defaultAcceptedTypes = [
  '.pdf',
  '.doc',
  '.docx',
  '.txt',
  '.md',
  '.rtf',
  '.odt',
  '.jpg',
  '.jpeg',
  '.png',
  '.gif',
  '.bmp',
  '.webp'
]

/**
 * 获取文件图标
 */
const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  switch (ext) {
    case 'pdf':
      return <FileText className="w-8 h-8 text-red-500" />
    case 'doc':
    case 'docx':
      return <FileText className="w-8 h-8 text-blue-500" />
    case 'txt':
    case 'md':
    case 'rtf':
      return <FileText className="w-8 h-8 text-gray-500" />
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'bmp':
    case 'webp':
      return <Image className="w-8 h-8 text-green-500" />
    default:
      return <File className="w-8 h-8 text-gray-400" />
  }
}

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 文档上传组件
 * 支持拖拽上传和文件选择
 */
const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadComplete,
  onUploadError,
  onClose,
  maxFiles = 10,
  maxFileSize = 50, // 50MB
  acceptedTypes = defaultAcceptedTypes,
  className
}) => {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  /**
   * 验证文件
   */
  const validateFile = useCallback((file: File): string | null => {
    // 检查文件大小
    if (file.size > maxFileSize * 1024 * 1024) {
      return `文件大小不能超过 ${maxFileSize}MB`
    }
    
    // 检查文件类型
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!acceptedTypes.includes(fileExt)) {
      return `不支持的文件类型: ${fileExt}`
    }
    
    return null
  }, [maxFileSize, acceptedTypes])
  
  /**
   * 添加文件到上传列表
   */
  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)
    const newUploadFiles: UploadFile[] = []
    
    for (const file of fileArray) {
      // 检查文件数量限制
      if (uploadFiles.length + newUploadFiles.length >= maxFiles) {
        toast.error(`最多只能上传 ${maxFiles} 个文件`)
        break
      }
      
      // 验证文件
      const error = validateFile(file)
      if (error) {
        toast.error(`${file.name}: ${error}`)
        continue
      }
      
      // 检查是否已存在
      const exists = uploadFiles.some(uf => 
        uf.file.name === file.name && uf.file.size === file.size
      )
      if (exists) {
        toast.error(`文件 ${file.name} 已存在`)
        continue
      }
      
      newUploadFiles.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        progress: 0,
        status: 'pending'
      })
    }
    
    if (newUploadFiles.length > 0) {
      setUploadFiles(prev => [...prev, ...newUploadFiles])
    }
  }, [uploadFiles, maxFiles, validateFile])
  
  /**
   * 处理拖拽事件
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      addFiles(files)
    }
  }, [addFiles])
  
  /**
   * 处理文件选择
   */
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      addFiles(files)
    }
    // 清空input值，允许重复选择同一文件
    e.target.value = ''
  }, [addFiles])
  
  /**
   * 移除文件
   */
  const removeFile = useCallback((fileId: string) => {
    setUploadFiles(prev => prev.filter(uf => uf.id !== fileId))
  }, [])
  
  /**
   * 模拟文件上传
   */
  const uploadFile = async (uploadFile: UploadFile): Promise<File> => {
    return new Promise((resolve, reject) => {
      // 更新状态为上传中
      setUploadFiles(prev => prev.map(uf => 
        uf.id === uploadFile.id 
          ? { ...uf, status: 'uploading' as const }
          : uf
      ))
      
      // 模拟上传进度
      let progress = 0
      const interval = setInterval(() => {
        progress += Math.random() * 30
        if (progress >= 100) {
          progress = 100
          clearInterval(interval)
          
          // 模拟上传成功/失败
          const success = Math.random() > 0.1 // 90% 成功率
          
          setUploadFiles(prev => prev.map(uf => 
            uf.id === uploadFile.id 
              ? { 
                  ...uf, 
                  progress: 100, 
                  status: success ? 'success' as const : 'error' as const,
                  error: success ? undefined : '上传失败，请重试'
                }
              : uf
          ))
          
          if (success) {
            resolve(uploadFile.file)
          } else {
            reject(new Error('上传失败'))
          }
        } else {
          setUploadFiles(prev => prev.map(uf => 
            uf.id === uploadFile.id 
              ? { ...uf, progress }
              : uf
          ))
        }
      }, 100)
    })
  }
  
  /**
   * 开始上传所有文件
   */
  const startUpload = async () => {
    const pendingFiles = uploadFiles.filter(uf => uf.status === 'pending')
    if (pendingFiles.length === 0) return
    
    setIsUploading(true)
    
    try {
      // 并发上传文件，并根据返回结果计算成功/失败
      const results = await Promise.allSettled(
        pendingFiles.map(file => uploadFile(file))
      )
      const successFiles = results
        .filter(r => r.status === 'fulfilled')
        .map(r => (r as PromiseFulfilledResult<File>).value)
      const errorCount = results.filter(r => r.status === 'rejected').length

      if (successFiles.length > 0) {
        onUploadComplete?.(successFiles)
      }
      if (errorCount > 0) {
        onUploadError?.(`${errorCount} 个文件上传失败`)
      }
    } catch (error) {
      onUploadError?.('上传过程中发生错误')
    } finally {
      setIsUploading(false)
    }
  }
  
  /**
   * 清空所有文件
   */
  const clearFiles = () => {
    setUploadFiles([])
  }
  
  return (
    <div className={cn('bg-white rounded-lg border shadow-sm', className)}>
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="text-lg font-semibold">上传文档</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
      
      {/* 上传区域 */}
      <div className="p-6">
        {/* 拖拽上传区域 */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
            isDragOver 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          )}
        >
          <div className="flex flex-col items-center space-y-4">
            <div className={cn(
              'p-4 rounded-full',
              isDragOver ? 'bg-blue-100' : 'bg-gray-100'
            )}>
              <Cloud className={cn(
                'w-8 h-8',
                isDragOver ? 'text-blue-500' : 'text-gray-400'
              )} />
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900">
                拖拽文件到此处上传
              </p>
              <p className="text-sm text-gray-500 mt-1">
                或者
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-500 hover:text-blue-600 mx-1 underline"
                >
                  点击选择文件
                </button>
              </p>
            </div>
            
            <div className="text-xs text-gray-400">
              <p>支持的格式: {acceptedTypes.join(', ')}</p>
              <p>最大文件大小: {maxFileSize}MB，最多 {maxFiles} 个文件</p>
            </div>
          </div>
        </div>
        
        {/* 隐藏的文件输入 */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
        
        {/* 文件列表 */}
        <AnimatePresence>
          {uploadFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-gray-900">
                  文件列表 ({uploadFiles.length})
                </h4>
                <button
                  onClick={clearFiles}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  清空全部
                </button>
              </div>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {uploadFiles.map((uploadFile) => (
                  <motion.div
                    key={uploadFile.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
                  >
                    {/* 文件图标 */}
                    <div className="flex-shrink-0">
                      {getFileIcon(uploadFile.file.name)}
                    </div>
                    
                    {/* 文件信息 */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {uploadFile.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(uploadFile.file.size)}
                      </p>
                      
                      {/* 进度条 */}
                      {uploadFile.status === 'uploading' && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs">
                            <span>上传中...</span>
                            <span>{Math.round(uploadFile.progress)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                            <div 
                              className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${uploadFile.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* 错误信息 */}
                      {uploadFile.status === 'error' && uploadFile.error && (
                        <p className="text-xs text-red-500 mt-1">
                          {uploadFile.error}
                        </p>
                      )}
                    </div>
                    
                    {/* 状态图标 */}
                    <div className="flex-shrink-0">
                      {uploadFile.status === 'pending' && (
                        <button
                          onClick={() => removeFile(uploadFile.id)}
                          className="p-1 hover:bg-gray-200 rounded-md transition-colors"
                        >
                          <X className="w-4 h-4 text-gray-400" />
                        </button>
                      )}
                      {uploadFile.status === 'uploading' && (
                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                      )}
                      {uploadFile.status === 'success' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {uploadFile.status === 'error' && (
                        <AlertCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* 操作按钮 */}
        {uploadFiles.length > 0 && (
          <div className="flex items-center justify-between mt-6 pt-4 border-t">
            <div className="text-sm text-gray-500">
              {uploadFiles.filter(uf => uf.status === 'pending').length} 个文件待上传
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={clearFiles}
                disabled={isUploading}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
              >
                清空
              </button>
              
              <button
                onClick={startUpload}
                disabled={isUploading || uploadFiles.filter(uf => uf.status === 'pending').length === 0}
                className={cn(
                  'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                  'bg-blue-500 text-white hover:bg-blue-600',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    上传中...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    开始上传
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentUpload
export type { DocumentUploadProps }