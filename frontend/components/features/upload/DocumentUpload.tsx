'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { uploadApi } from '@/api'
import { Button } from '@/components/ui'
import ProgressBar from '@/components/ui/ProgressBar'
import { DocumentClassification } from '@/generated'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { WebSocketMessageType } from '@/websocket-protocol'
import { getCategoryColor, getCategoryLabel } from '@/utils/categoryUtils'
import { FileStartMessage, FileCompleteMessage, UploadProgressEvent, ErrorMessage } from '@/websocket-protocol'
import { useLanguage } from '@/contexts/LanguageContext'

interface DocumentUploadProps {
  onUploadStatus: (status: string, type?: 'success' | 'error' | 'warning') => void
}

export default function DocumentUpload({ onUploadStatus }: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Progress tracking state
  const [progress, setProgress] = useState(0)
  const [currentFile, setCurrentFile] = useState<string>('')
  const [totalFiles, setTotalFiles] = useState(0)
  const [currentFileIndex, setCurrentFileIndex] = useState(0)
  const [showProgress, setShowProgress] = useState(false)
  
  // File processing status tracking
  const [fileStatuses, setFileStatuses] = useState<Record<string, {
    status: 'pending' | 'processing' | 'completed' | 'error'
    classification?: DocumentClassification
    wasCached?: boolean
  }>>({})
  
  // Track if upload was successful to show clear results button
  const [uploadCompleted, setUploadCompleted] = useState(false)
  const { t } = useLanguage()
  
  // WebSocket context
  const { register } = useWebSocket()
  

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (selectedFiles) {
      const newFiles = Array.from(selectedFiles)
      
      // If there are completed files (upload was successful), clear everything for new upload
      if (uploadCompleted) {
        setFiles(newFiles)
        setFileStatuses({})
        setUploadCompleted(false)
      } else {
        // If there are only pending files, add to them
        setFiles(prev => [...prev, ...newFiles])
      }
      
      // Initialize file statuses for new files
      const newStatuses: Record<string, { status: 'pending', classification?: DocumentClassification }> = {}
      newFiles.forEach(file => {
        newStatuses[file.name] = { status: 'pending' }
      })
      setFileStatuses(prev => ({ ...prev, ...newStatuses }))
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    handleFileSelect(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const removeFile = (index: number) => {
    const fileToRemove = files[index]
    setFiles(prev => prev.filter((_, i) => i !== index))
    
    // Remove file status
    if (fileToRemove) {
      setFileStatuses(prev => {
        const updated = { ...prev }
        delete updated[fileToRemove.name]
        return updated
      })
    }
  }

  const clearAllFiles = () => {
    setFiles([])
    setFileStatuses({})
    setUploadCompleted(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // WebSocket event handlers
  const handleFileStart = useCallback((data: FileStartMessage) => {
    setCurrentFile(data.filename)
    // Don't override totalFiles - it's set from actual upload count
    // Only update if it's not already set
    setTotalFiles(prev => prev || data.total_files || 1)
    // Don't update progress here - it will be calculated in handleFileComplete
    // Don't update currentFileIndex here - it will be calculated in handleFileComplete
    setShowProgress(true)
    
    // Mark file as processing
    setFileStatuses(prev => ({
      ...prev,
      [data.filename]: { ...prev[data.filename], status: 'processing' }
    }))
  }, [])

  const handleFileComplete = useCallback((data: FileCompleteMessage) => {
    // Mark file as completed with classification data if available
    setFileStatuses(prev => {
      const updated: Record<string, {
        status: 'pending' | 'processing' | 'completed' | 'error'
        classification?: DocumentClassification
        wasCached?: boolean
      }> = {
        ...prev,
        [data.filename]: { 
          ...prev[data.filename], 
          status: 'completed',
          classification: data.classification ? {
            filename: data.filename,
            category: data.classification.category,
            confidence: data.classification.confidence
          } : undefined,
          wasCached: data.was_cached || false
        }
      }
      
      // Calculate progress based on completed files out of total
      const allFiles = Object.keys(updated)
      const completedFiles = allFiles.filter(filename => {
        const fileStatus = updated[filename]
        return fileStatus && fileStatus.status === 'completed'
      })
      
      // Update progress based on actual completion count
      const totalFiles = allFiles.length
      const completedCount = completedFiles.length
      const progressPercent = totalFiles > 0 ? Math.round((completedCount / totalFiles) * 100) : 0
      
      setProgress(progressPercent)
      setCurrentFileIndex(completedCount)
      
      // If all files are completed, mark upload as completed and hide progress after a short delay
      if (completedCount === totalFiles && totalFiles > 0) {
        setUploadCompleted(true)
        setTimeout(() => {
          setShowProgress(false)
          setProgress(0)
          setCurrentFile('')
        }, 1000)
      }
      
      return updated
    })
  }, [])

  const handleError = useCallback((data: ErrorMessage) => {
    console.error('❌ WebSocket error message:', data.message)
    onUploadStatus(`WebSocket Error: ${data.message}`, 'error')
    setShowProgress(false)
  }, [onUploadStatus])

  // Handle upload progress messages that contain nested file events
  const handleUploadProgress = useCallback((data: UploadProgressEvent) => {
    console.log('📨 Received WebSocket UPLOAD_PROGRESS message:', data)
    
    // Check the nested type in the data
    if (data.type === 'file_start') {
      console.log('✅ Handling file_start event for:', data.filename)
      handleFileStart(data)
    } else if (data.type === 'file_complete') {
      console.log('✅ Handling file_complete event for:', data.filename)
      handleFileComplete(data)
    } else {
      console.warn('⚠️ Unknown event type in UPLOAD_PROGRESS:', (data as any).type, 'Full data:', data)
    }
  }, [handleFileStart, handleFileComplete])

  // Register for WebSocket events
  useEffect(() => {
    const unsubscribeUploadProgress = register(WebSocketMessageType.UPLOAD_PROGRESS, handleUploadProgress as (data: Record<string, any>) => void)
    const unsubscribeError = register(WebSocketMessageType.ERROR, handleError as (data: Record<string, any>) => void)
    
    return () => {
      unsubscribeUploadProgress()
      unsubscribeError()
    }
  }, [register, handleUploadProgress, handleError])


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (files.length === 0) {
      onUploadStatus(t('upload.pleaseSelectFiles'), 'warning')
      return
    }

    setIsUploading(true)
    setShowProgress(true) // Show progress bar
    setUploadCompleted(false) // Reset upload completed state
    setTotalFiles(files.length) // Set total files from actual upload count
    setCurrentFileIndex(0) // Reset current file index
    setProgress(0) // Reset progress
    
    // Mark all files as processing
    const processingStatuses: Record<string, { status: 'processing', classification?: DocumentClassification }> = {}
    files.forEach(file => {
      processingStatuses[file.name] = { status: 'processing' }
    })
    setFileStatuses(processingStatuses)
    try {
      const result = await uploadApi.uploadFilesApiUploadPost({ 
        files
      })
      
      // Files are now uploaded to database and submitted to processing queue
      // Keep all files as 'processing' - WebSocket events will update their status
      // as they are actually processed in the background
      
      // Show message that files are being processed
      onUploadStatus(result.message || 'Files uploaded successfully. Processing in background...', 'success')
      
      // Don't mark files as completed here - let WebSocket events handle that
      // Don't hide progress bar - keep it visible until all files are processed
      // Don't set uploadCompleted - that will be set when all files are done via WebSocket
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      let errorMessage = 'Upload failed'
      
      // Handle different error types based on HTTP status codes
      if (error?.response?.data?.detail) {
        // Use the specific error message from the backend first
        errorMessage = error.response.data.detail
      } else if (error?.response?.status === 503) {
        errorMessage = 'Service temporarily unavailable. Please try again later.'
      } else if (error?.response?.status === 500) {
        errorMessage = 'Server error occurred while processing your files. Please try again.'
      } else if (error?.response?.status === 400) {
        errorMessage = 'Invalid request. Please check your files and try again.'
      } else if (error?.response?.status === 413) {
        errorMessage = 'File too large. Please select smaller files.'
      } else if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error instanceof Error) {
        errorMessage = error.message
      }
      
      onUploadStatus(`Error: ${errorMessage}`, 'error')
      setShowProgress(false) // Hide progress bar on error
      
      // Mark all files as error status
      setFileStatuses(prev => {
        const updated = { ...prev }
        Object.keys(updated).forEach(filename => {
          updated[filename] = { ...updated[filename], status: 'error' }
        })
        return updated
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col flex-grow">
      <div
        className="flex-grow border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-violet-500 hover:bg-violet-50 transition-colors"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png"
          multiple
          onChange={(e) => handleFileSelect(e.target.files)}
        />
        <div className="flex flex-col items-center justify-center h-full">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
          </svg>
          <p className="mt-2 text-gray-500">{t('upload.dragOrClick')}</p>
          <p className="text-xs text-gray-400 mt-1">{t('upload.fileTypes')}</p>
          {uploadCompleted && (
            <p className="text-xs text-blue-600 mt-2 font-medium">
              {t('upload.dropToStartFresh')}
            </p>
          )}
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              {t('upload.selectedFiles', { count: files.length, processed: uploadCompleted })}
            </span>
            {!isUploading && (
              <button
                type="button"
                onClick={clearAllFiles}
                className={`text-sm font-medium ${
                  uploadCompleted 
                    ? 'text-blue-600 hover:text-blue-800' 
                    : 'text-red-600 hover:text-red-800'
                }`}
              >
                {uploadCompleted ? t('upload.clearResults') : t('upload.clearAll')}
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
            {files.map((file, index) => {
              const fileStatus = fileStatuses[file.name]
              const status = fileStatus?.status || 'pending'
              
              return (
                <div key={index} className="flex items-start justify-between bg-gray-100 p-3 rounded-lg">
                  <div className="flex-1 mr-4 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                      {file.name}
                    </div>
                    
                    {status === 'completed' && fileStatus?.classification && (
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(
                              fileStatus.classification.category
                            )}`}
                          >
                            {getCategoryLabel(fileStatus.classification.category)}
                          </span>
                          <span className="text-xs text-gray-500">
                            {(fileStatus.classification.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        {fileStatus.wasCached && (
                          <div className="text-xs text-blue-600 font-medium">
                            {t('upload.previouslyClassified')}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {status === 'error' && (
                      <div className="text-xs text-red-600 mt-1">
                        {t('upload.processingFailed')}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-shrink-0 flex items-center space-x-2">
                    {status === 'pending' && !isUploading && (
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700 text-lg"
                      >
                        ×
                      </button>
                    )}
                    {status === 'processing' && (
                      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    )}
                    {status === 'completed' && (
                      <div className="text-green-500 text-lg">✓</div>
                    )}
                    {status === 'error' && (
                      <div className="text-red-500 text-lg">✗</div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <Button
        type="submit"
        disabled={isUploading || files.length === 0 || uploadCompleted}
        isLoading={isUploading}
        className={`mt-4 w-full ${
          uploadCompleted 
            ? 'bg-green-600 hover:bg-green-700 text-white' 
            : ''
        }`}
      >
        {uploadCompleted ? t('upload.uploadComplete') : t('upload.enrollDocuments')}
      </Button>

      {/* Progress bar */}
      <ProgressBar
        progress={progress}
        currentFile={currentFile}
        totalFiles={totalFiles}
        currentFileIndex={currentFileIndex}
        isVisible={showProgress}
        className="mt-4"
      />

    </form>
  )
}
