import { useState } from 'react'
import { uploadApi } from '@/api'

export function useUpload() {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string>('')

  const addFiles = (newFiles: File[]) => {
    setFiles(prev => [...prev, ...newFiles])
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearFiles = () => {
    setFiles([])
  }

  const upload = async () => {
    if (files.length === 0) {
      throw new Error('No files to upload')
    }

    setIsUploading(true)
    try {
      const result = await uploadApi.uploadFilesApiUploadPost({ files })
      setUploadStatus(result.message)
      clearFiles()
      return result
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
      
      setUploadStatus(`Error: ${errorMessage}`)
      throw error
    } finally {
      setIsUploading(false)
    }
  }

  return {
    files,
    isUploading,
    uploadStatus,
    addFiles,
    removeFile,
    clearFiles,
    upload
  }
}
