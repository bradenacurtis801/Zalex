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
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
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
