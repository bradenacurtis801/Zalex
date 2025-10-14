'use client'

import { useState, useEffect } from 'react'
import { useCategories, CategoryDocument } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'

interface CategoryDocumentsProps {
  category: string
  onError: (message: string) => void
}

export default function CategoryDocuments({ category, onError }: CategoryDocumentsProps) {
  const { fetchDocumentsByCategory } = useCategories()
  const [documents, setDocuments] = useState<CategoryDocument[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [category])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const response = await fetchDocumentsByCategory(category)
      setDocuments(response.documents || [])
    } catch (err) {
      onError(`Failed to load documents for ${category}`)
      console.error('Error loading documents:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-center">
          <div className="loader mx-auto mb-2"></div>
          <p className="text-gray-600">Loading documents...</p>
        </div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <div className="text-4xl mb-4">📄</div>
        <h3 className="text-lg font-medium mb-2">No Documents Found</h3>
        <p className="text-sm">No documents found in the {category} category.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600 mb-4">
        Showing {documents.length} document{documents.length !== 1 ? 's' : ''} in {category}
      </div>
      
      {documents.map((doc, index) => (
        <div
          key={`${doc.filename}-${index}`}
          className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gray-900 truncate">
                {doc.filename}
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                {doc.filePath}
              </p>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                  Confidence: {formatConfidence(doc.confidence)}
                </span>
                <span>
                  Added: {formatDate(doc.timestamp)}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-violet-100 text-violet-800">
                {doc.category}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
