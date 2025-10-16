'use client'

import { useState, useRef, useEffect } from 'react'
import { uploadApi, createWebSocketUrl, generateClientId } from '@/api'
import { Button } from '@/components/ui'
import ProgressBar from '@/components/ui/ProgressBar'
import ClassificationResults from './ClassificationResults'
import { DocumentClassification } from '@/generated'
import { useWebSocket } from '@/hooks/useWebSocket'

interface DocumentUploadProps {
  onUploadStatus: (status: string, type?: 'success' | 'error' | 'warning') => void
}

export default function DocumentUpload({ onUploadStatus }: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [classifications, setClassifications] = useState<DocumentClassification[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Progress tracking state
  const [progress, setProgress] = useState(0)
  const [currentFile, setCurrentFile] = useState<string>('')
  const [totalFiles, setTotalFiles] = useState(0)
  const [currentFileIndex, setCurrentFileIndex] = useState(0)
  const [showProgress, setShowProgress] = useState(false)
  
  // WebSocket state
  const [clientId] = useState(() => generateClientId())
  const [wsUrl] = useState(() => {
    const url = createWebSocketUrl(clientId)
    console.log('WebSocket URL:', url)
    return url
  })
  

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (selectedFiles) {
      const newFiles = Array.from(selectedFiles)
      setFiles(prev => [...prev, ...newFiles])
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
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearAllFiles = () => {
    setFiles([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // WebSocket message handler
  const handleWebSocketMessage = (message: any) => {
    console.log('📨 WebSocket message received:', message)
    
    if (message.type === 'file_start') {
      console.log('🚀 File start:', message.filename)
      setCurrentFile(message.filename)
      setTotalFiles(message.total_files)
      setCurrentFileIndex(message.current_file)
      setProgress(message.progress_percent)
      setShowProgress(true)
    } else if (message.type === 'file_complete') {
      console.log('✅ File complete:', message.filename, 'Progress:', message.progress_percent + '%')
      setProgress(message.progress_percent)
      setCurrentFileIndex(message.current_file)
      
      // If this is the last file, hide progress after a short delay
      if (message.current_file === message.total_files) {
        console.log('🎉 All files processed!')
        setTimeout(() => {
          setShowProgress(false)
          setProgress(0)
          setCurrentFile('')
        }, 1000)
      }
    } else if (message.type === 'error') {
      console.error('❌ WebSocket error message:', message.error)
      onUploadStatus(`WebSocket Error: ${message.error}`, 'error')
      setShowProgress(false)
    } else {
      console.log('❓ Unknown message type:', message.type)
    }
  }

  // WebSocket connection
  const { isConnected, connect, disconnect } = useWebSocket({
    url: wsUrl,
    onMessage: handleWebSocketMessage,
    onError: (error) => {
      console.error('WebSocket error:', error)
      console.error('WebSocket URL:', wsUrl)
    },
    onOpen: () => {
      console.log('WebSocket connected successfully')
    },
    onClose: () => {
      console.log('WebSocket disconnected')
    }
  })

  // Connect to WebSocket when component mounts
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (files.length === 0) {
      onUploadStatus('Please select files to enroll.', 'warning')
      return
    }

    setIsUploading(true)
    setClassifications([]) // Clear previous classifications
    setShowProgress(true) // Show progress bar
    try {
      const result = await uploadApi.uploadFilesApiUploadPost({ 
        files,
        clientId: clientId
      })
      
      // Handle classification results if available
      if (result.classifications && result.classifications.length > 0) {
        setClassifications(result.classifications)
        
        // Create detailed classification message
        const classificationDetails = result.classifications
          .map((classification: DocumentClassification) => {
            const truncatedFilename = classification.filename.length > 25 
              ? `${classification.filename.substring(0, 25)}...` 
              : classification.filename
            return `${truncatedFilename}: ${classification.category} (${(classification.confidence * 100).toFixed(1)}%)`
          })
          .join(', ')
        
        // Add special message for already classified documents
        const statusMessage = result.alreadyClassified 
          ? `📋 ${result.message} Classifications: ${classificationDetails}`
          : `${result.message} Classifications: ${classificationDetails}`
        
        onUploadStatus(statusMessage, 'success')
      } else {
        // Add special message for already classified documents even without classifications
        const statusMessage = result.alreadyClassified 
          ? `📋 ${result.message}`
          : result.message
        
        onUploadStatus(statusMessage, 'success')
      }
      
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      setShowProgress(false) // Hide progress bar on success
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
          <p className="mt-2 text-gray-500">Drag & drop files here, or click to select</p>
          <p className="text-xs text-gray-400 mt-1">PDF, JPG, PNG</p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Selected files ({files.length})
            </span>
            <button
              type="button"
              onClick={clearAllFiles}
              className="text-sm text-red-600 hover:text-red-800 font-medium"
            >
              Clear All
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
            {files.map((file, index) => (
              <div key={index} className="flex justify-between items-center bg-gray-100 p-2 rounded">
                <span className="text-sm truncate flex-1 mr-2">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="text-red-500 hover:text-red-700 flex-shrink-0"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <Button
        type="submit"
        disabled={isUploading || files.length === 0}
        isLoading={isUploading}
        className="mt-4 w-full"
      >
        Enroll Documents
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

      {/* Display classification results */}
      <ClassificationResults classifications={classifications} />
    </form>
  )
}
