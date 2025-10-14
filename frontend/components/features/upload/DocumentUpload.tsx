'use client'

import { useState, useRef } from 'react'
import { uploadApi } from '@/api'
import { Button } from '@/components/ui'
import ClassificationResults from './ClassificationResults'
import { DocumentClassification } from '@/generated'

interface DocumentUploadProps {
  onUploadStatus: (status: string, type?: 'success' | 'error' | 'warning') => void
}

export default function DocumentUpload({ onUploadStatus }: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [classifications, setClassifications] = useState<DocumentClassification[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (files.length === 0) {
      onUploadStatus('Please select files to enroll.', 'warning')
      return
    }

    setIsUploading(true)
    setClassifications([]) // Clear previous classifications
    try {
      const result = await uploadApi.uploadFilesApiUploadPost({ files })
      
      // Handle classification results if available
      if (result.classifications && result.classifications.length > 0) {
        setClassifications(result.classifications)
        onUploadStatus(`${result.message} Documents classified successfully!`, 'success')
      } else {
        onUploadStatus(result.message, 'success')
      }
      
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      let errorMessage = 'Upload failed'
      
      // Handle different error types based on HTTP status codes
      if (error?.response?.status === 503) {
        errorMessage = 'OCR service is not available. Please ensure Tesseract is installed on the server.'
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

      <div className="mt-4 space-y-2">
        {files.map((file, index) => (
          <div key={index} className="flex justify-between items-center bg-gray-100 p-2 rounded">
            <span className="text-sm truncate">{file.name}</span>
            <button
              type="button"
              onClick={() => removeFile(index)}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <Button
        type="submit"
        disabled={isUploading || files.length === 0}
        isLoading={isUploading}
        className="mt-4 w-full"
      >
        Enroll Documents
      </Button>

      {/* Display classification results */}
      <ClassificationResults classifications={classifications} />
    </form>
  )
}
