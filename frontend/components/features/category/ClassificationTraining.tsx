'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui'

interface ClassificationTrainingProps {
  onSuccess?: () => void
}

export default function ClassificationTraining({ onSuccess }: ClassificationTrainingProps) {
  const [categoryName, setCategoryName] = useState('')
  const [description, setDescription] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (selectedFiles) {
      const newFiles = Array.from(selectedFiles)
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files)
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
    setError(null)
    setSuccess(null)

    if (!categoryName.trim()) {
      setError('Category name is required')
      return
    }

    if (files.length === 0) {
      setError('Please upload at least one training document')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      formData.append('name', categoryName)
      if (description.trim()) {
        formData.append('description', description)
      }
      files.forEach((file) => {
        formData.append('files', file)
      })

      const token = localStorage.getItem('auth_token')
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || ''

      const response = await fetch(`${apiBaseUrl}/api/categories`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create category' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      setSuccess(`Category "${data.category_name}" created successfully with ${data.training_documents_count} training document(s)`)
      
      // Reset form
      setCategoryName('')
      setDescription('')
      setFiles([])
      
      // Notify parent component to refresh metrics
      if (onSuccess) {
        setTimeout(() => {
          onSuccess()
        }, 1000)
      }
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setSuccess(null)
      }, 5000)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create category'
      setError(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Create New Category</h2>
        <p className="text-sm text-gray-600 mt-1">Upload training documents to create a new classification category</p>
      </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="categoryName" className="block text-sm font-medium text-gray-700 mb-1">
                Category Name *
              </label>
              <input
                type="text"
                id="categoryName"
                value={categoryName}
                onChange={(e) => setCategoryName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                placeholder="e.g., mercantil, laboral, civil"
                required
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                rows={3}
                placeholder="Brief description of this category"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Training Documents *
              </label>
              <p className="mb-2 text-sm text-gray-500">
                Upload PDF or image files that are already classified for this category. These will be used to train the classifier.
              </p>
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-violet-500 hover:bg-violet-50 transition-colors"
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
                  onChange={handleFileChange}
                />
                <div className="flex flex-col items-center justify-center">
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
                    {!isUploading && (
                      <button
                        type="button"
                        onClick={() => setFiles([])}
                        className="text-sm font-medium text-red-600 hover:text-red-800"
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                  <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
                    {files.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-100 p-3 rounded-lg">
                        <div className="flex-1 mr-4 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                            {file.name}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </div>
                        </div>
                        {!isUploading && (
                          <button
                            type="button"
                            onClick={() => removeFile(index)}
                            className="text-red-500 hover:text-red-700 text-lg flex-shrink-0"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
                {success}
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="submit"
                variant="primary"
                isLoading={isUploading}
                disabled={isUploading}
              >
                {isUploading ? 'Creating Category...' : 'Create Category'}
              </Button>
            </div>
          </form>
    </div>
  )
}

