import * as React from 'react'
import { useState, useEffect, useRef, useCallback } from 'react'
// import { motion } from 'framer-motion'
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Square,
  RotateCcw,
  Check
} from 'lucide-react'
import { toast } from 'sonner'

import { cn } from '@/utils/cn'

// 声明全局类型
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

/**
 * 语音识别状态枚举
 */
export enum VoiceRecognitionStatus {
  IDLE = 'idle',
  LISTENING = 'listening',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error'
}

/**
 * 语音输入组件属性接口
 */
interface VoiceInputProps {
  onTranscript?: (transcript: string) => void
  onFinalTranscript?: (transcript: string) => void
  onError?: (error: string) => void
  placeholder?: string
  autoStart?: boolean
  continuous?: boolean
  language?: string
  className?: string
}

/**
 * 语音输入组件
 * 提供语音转文字功能
 */
const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onFinalTranscript,
  onError,
  placeholder = '点击开始语音输入...',
  autoStart = false,
  continuous = false,
  language = 'zh-CN',
  className
}) => {
  const [status, setStatus] = useState<VoiceRecognitionStatus>(VoiceRecognitionStatus.IDLE)
  const [transcript, setTranscript] = useState('')
  const [finalTranscript, setFinalTranscript] = useState('')
  const [isSupported, setIsSupported] = useState(false)
  const [volume, setVolume] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  
  const recognitionRef = useRef<any>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const animationFrameRef = useRef<number>()
  
  // 检查浏览器支持
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    setIsSupported(!!SpeechRecognition && !!navigator.mediaDevices?.getUserMedia)
    
    if (!SpeechRecognition) {
      onError?.('您的浏览器不支持语音识别功能')
      return
    }
    
    // 初始化语音识别
    const recognition = new SpeechRecognition()
    recognition.continuous = continuous
    recognition.interimResults = true
    recognition.lang = language
    
    // 识别结果处理
    recognition.onresult = (event: any) => {
      let interimTranscript = ''
      let finalTranscriptText = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscriptText += result[0].transcript
        } else {
          interimTranscript += result[0].transcript
        }
      }
      
      setTranscript(interimTranscript)
      onTranscript?.(interimTranscript)
      
      if (finalTranscriptText) {
        setFinalTranscript(prev => prev + finalTranscriptText)
        onFinalTranscript?.(finalTranscriptText)
      }
    }
    
    // 识别开始
    recognition.onstart = () => {
      setStatus(VoiceRecognitionStatus.LISTENING)
      startVolumeMonitoring()
    }
    
    // 识别结束
    recognition.onend = () => {
      setStatus(VoiceRecognitionStatus.IDLE)
      stopVolumeMonitoring()
    }
    
    // 识别错误
    recognition.onerror = (event: any) => {
      setStatus(VoiceRecognitionStatus.ERROR)
      stopVolumeMonitoring()
      
      let errorMessage = '语音识别出错'
      switch (event.error) {
        case 'no-speech':
          errorMessage = '未检测到语音，请重试'
          break
        case 'audio-capture':
          errorMessage = '无法访问麦克风，请检查权限'
          break
        case 'not-allowed':
          errorMessage = '麦克风权限被拒绝'
          break
        case 'network':
          errorMessage = '网络错误，请检查网络连接'
          break
        default:
          errorMessage = `语音识别错误: ${event.error}`
      }
      
      onError?.(errorMessage)
      toast.error(errorMessage)
    }
    
    recognitionRef.current = recognition
    
    // 自动开始
    if (autoStart) {
      startListening()
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      stopVolumeMonitoring()
    }
  }, [language, continuous, autoStart, onTranscript, onFinalTranscript, onError]) // eslint-disable-line react-hooks/exhaustive-deps
  
  /**
   * 更新音量
   */
  const updateVolume = useCallback(() => {
    if (!analyserRef.current) return
    
    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    analyserRef.current.getByteFrequencyData(dataArray)
    
    let sum = 0
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i]
    }
    
    const average = sum / bufferLength
    setVolume(average / 255) // 归一化到 0-1
    
    animationFrameRef.current = requestAnimationFrame(updateVolume)
  }, [])
  
  /**
   * 开始音量监控
   */
  const startVolumeMonitoring = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      const audioContext = new AudioContext()
      const analyser = audioContext.createAnalyser()
      const microphone = audioContext.createMediaStreamSource(stream)
      
      analyser.smoothingTimeConstant = 0.8
      analyser.fftSize = 1024
      
      microphone.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      microphoneRef.current = microphone
      
      updateVolume()
    } catch (error) {
      console.error('无法访问麦克风:', error)
    }
  }, [updateVolume])
  
  /**
   * 停止音量监控
   */
  const stopVolumeMonitoring = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    analyserRef.current = null
    microphoneRef.current = null
    setVolume(0)
  }
  
  /**
   * 开始监听
   */
  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current) {
      toast.error('您的浏览器不支持语音识别')
      return
    }
    
    try {
      setTranscript('')
      setFinalTranscript('')
      setStatus(VoiceRecognitionStatus.LISTENING)
      recognitionRef.current.start()
    } catch (error) {
      console.error('启动语音识别失败:', error)
      toast.error('启动语音识别失败')
    }
  }, [isSupported])
  
  /**
   * 停止监听
   */
  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }
  
  /**
   * 重置
   */
  const reset = () => {
    setTranscript('')
    setFinalTranscript('')
    setStatus(VoiceRecognitionStatus.IDLE)
    stopListening()
  }
  
  /**
   * 确认输入
   */
  const confirmInput = () => {
    const fullTranscript = finalTranscript + transcript
    if (fullTranscript.trim()) {
      onFinalTranscript?.(fullTranscript.trim())
      setStatus(VoiceRecognitionStatus.COMPLETED)
    }
  }
  
  /**
   * 播放转录文本
   */
  const playTranscript = () => {
    const fullTranscript = finalTranscript + transcript
    if (!fullTranscript.trim()) return
    
    if ('speechSynthesis' in window) {
      if (isPlaying) {
        speechSynthesis.cancel()
        setIsPlaying(false)
        return
      }
      
      const utterance = new SpeechSynthesisUtterance(fullTranscript)
      utterance.lang = language
      utterance.rate = 0.9
      utterance.pitch = 1
      
      utterance.onstart = () => setIsPlaying(true)
      utterance.onend = () => setIsPlaying(false)
      utterance.onerror = () => setIsPlaying(false)
      
      speechSynthesis.speak(utterance)
    } else {
      toast.error('您的浏览器不支持语音合成')
    }
  }
  
  if (!isSupported) {
    return (
      <div className={cn('p-4 text-center text-gray-500', className)}>
        <MicOff className="w-8 h-8 mx-auto mb-2" />
        <p className="text-sm">您的浏览器不支持语音输入功能</p>
      </div>
    )
  }
  
  const isListening = status === VoiceRecognitionStatus.LISTENING
  const hasTranscript = transcript || finalTranscript
  
  return (
    <div className={cn('bg-white border border-gray-200 rounded-lg p-4', className)}>
      {/* 状态指示器 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={cn(
            'w-3 h-3 rounded-full',
            isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-300'
          )} />
          <span className="text-sm font-medium text-gray-700">
            {isListening ? '正在监听...' : '语音输入'}
          </span>
        </div>
        
        {/* 音量指示器 */}
        {isListening && (
          <div className="flex items-center space-x-1">
            {volume > 0.1 ? (
              <Volume2 className="w-4 h-4 text-green-500" />
            ) : (
              <VolumeX className="w-4 h-4 text-gray-400" />
            )}
            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-green-500"
                style={{ width: `${volume * 100}%` }}
                transition={{ duration: 0.1 }}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* 转录文本显示 */}
      <div className="min-h-[80px] mb-4">
        {hasTranscript ? (
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-900">
              {finalTranscript && (
                <span className="text-gray-900">{finalTranscript}</span>
              )}
              {transcript && (
                <span className="text-gray-500 italic">{transcript}</span>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-20 text-gray-400 text-sm">
            {placeholder}
          </div>
        )}
      </div>
      
      {/* 控制按钮 */}
      <div className="flex items-center justify-center space-x-3">
        {/* 主控制按钮 */}
        <button
          onClick={isListening ? stopListening : startListening}
          disabled={status === VoiceRecognitionStatus.PROCESSING}
          className={cn(
            'flex items-center justify-center w-12 h-12 rounded-full transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-offset-2',
            isListening
              ? 'bg-red-500 hover:bg-red-600 focus:ring-red-500 text-white'
              : 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-500 text-white',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isListening ? (
            <Square className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>
        
        {/* 播放按钮 */}
        {hasTranscript && (
          <button
            onClick={playTranscript}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-4 h-4 text-gray-600" />
            ) : (
              <Play className="w-4 h-4 text-gray-600" />
            )}
          </button>
        )}
        
        {/* 重置按钮 */}
        {hasTranscript && (
          <button
            onClick={reset}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            <RotateCcw className="w-4 h-4 text-gray-600" />
          </button>
        )}
        
        {/* 确认按钮 */}
        {hasTranscript && (
          <button
            onClick={confirmInput}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-green-500 hover:bg-green-600 text-white transition-colors"
          >
            <Check className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* 提示文本 */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          {isListening
            ? '说话时请保持清晰，完成后点击停止'
            : '点击麦克风按钮开始语音输入'
          }
        </p>
      </div>
    </div>
  )
}

export default VoiceInput
export type { VoiceInputProps }