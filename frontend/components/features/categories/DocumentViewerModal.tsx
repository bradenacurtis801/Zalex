'use client'

import { useState, useEffect } from 'react'
import { CategoryDocument } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import { getCategoryColor } from '@/utils/categoryUtils'
import { uploadApi } from '@/api'
import ReclassificationModal from './ReclassificationModal'
import OCRTextViewer from './OCRTextViewer'
import PDFViewer from './PDFViewer'

interface DocumentViewerModalProps {
  isOpen: boolean
  onClose: () => void
  document: CategoryDocument
  onReclassify?: (document: CategoryDocument) => void
  availableCategories?: string[]
}

export default function DocumentViewerModal({
  isOpen,
  onClose,
  document,
  onReclassify,
  availableCategories = []
}: DocumentViewerModalProps) {
  const [documentContent, setDocumentContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [contentType, setContentType] = useState<'text' | 'image' | 'pdf'>('text')
  const [showReclassifyModal, setShowReclassifyModal] = useState(false)
  const [showOCRViewer, setShowOCRViewer] = useState(false)


  useEffect(() => {
    if (isOpen && document) {
      loadDocumentContent()
    }
  }, [isOpen, document])

  const loadDocumentContent = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Determine content type based on file extension
      const fileExtension = document.filename.toLowerCase().split('.').pop()
      
      if (['pdf'].includes(fileExtension || '')) {
        setContentType('pdf')
        setDocumentContent('') // No need to fetch content for PDFs
      } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(fileExtension || '')) {
        setContentType('image')
        setDocumentContent('') // No need to fetch content for images
      } else {
        setContentType('text')
        // For text files, try to fetch the content
        const data = await uploadApi.getDocumentContentApiDocumentsDocumentIdContentGet({
          documentId: document.id
        })
        setDocumentContent(data.content || '')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document content')
      console.error('Error loading document content:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      // Use the API to get the download URL
      const response = await uploadApi.downloadDocumentApiDocumentsDocumentIdDownloadGet({
        documentId: document.id
      })
      
      // Create a download link for the document
      const link = window.document.createElement('a')
      link.href = response.url || `/api/documents/${encodeURIComponent(document.id)}/download`
      link.download = document.filename
      window.document.body.appendChild(link)
      link.click()
      window.document.body.removeChild(link)
    } catch (error) {
      console.error('Error downloading document:', error)
      // Fallback to direct URL
      const link = window.document.createElement('a')
      link.href = `/api/documents/${encodeURIComponent(document.id)}/download`
      link.download = document.filename
      window.document.body.appendChild(link)
      link.click()
      window.document.body.removeChild(link)
    }
  }

  const handleClose = () => {
    if (!loading) {
      setShowReclassifyModal(false)
      onClose()
    }
  }

  const handleReclassify = () => {
    setShowReclassifyModal(true)
  }

  const handleReclassifySuccess = () => {
    setShowReclassifyModal(false)
    if (onReclassify) {
      onReclassify(document)
    }
  }

  const handleViewOCR = () => {
    setShowOCRViewer(true)
  }

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Document Viewer
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {document.filename}
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Document Info */}
        <div className="px-6 py-4 bg-gray-50 border-b">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Category:</span>
              <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getCategoryColor(document.category)}`}>
                {document.category}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Confidence:</span>
              <span className={`ml-2 font-medium ${
                document.confidence > 0.8 ? 'text-green-600' :
                document.confidence > 0.5 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {formatConfidence(document.confidence)}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Added:</span>
              <span className="ml-2 text-gray-600">
                {formatDate(document.timestamp)}
              </span>
            </div>
          </div>
          
          {/* Reclassify Link */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <button
              onClick={handleReclassify}
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Did we get this wrong? Click to reclassify
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 p-6 overflow-auto">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="loader mx-auto mb-4"></div>
                <p className="text-gray-600">Loading document content...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="text-center p-8">
              <StatusMessage message={error} type="error" />
              <Button onClick={loadDocumentContent} className="mt-4">
                Retry
              </Button>
            </div>
          )}

          {!loading && !error && contentType === 'text' && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">Document Content:</h4>
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono max-h-96 overflow-auto">
                {documentContent || 'No content available'}
              </pre>
            </div>
          )}

          {!loading && !error && contentType === 'image' && (
            <div className="text-center">
              <img
                src={`/api/documents/${encodeURIComponent(document.id)}/content`}
                alt={document.filename}
                className="max-w-full max-h-96 mx-auto rounded-lg shadow-lg"
                onError={() => setError('Failed to load image')}
              />
            </div>
          )}

          {!loading && !error && contentType === 'pdf' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-medium text-gray-900">PDF Document</h4>
                <Button
                  onClick={handleViewOCR}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  View OCR Text
                </Button>
              </div>
              <PDFViewer
                document={document}
                className="max-h-96"
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
          <Button
            variant="secondary"
            onClick={handleDownload}
          >
            Download
          </Button>
          <Button
            variant="secondary"
            onClick={handleClose}
          >
            Close
          </Button>
        </div>
      </div>

      {/* Reclassification Modal */}
      <ReclassificationModal
        isOpen={showReclassifyModal}
        onClose={() => setShowReclassifyModal(false)}
        document={document}
        onSuccess={handleReclassifySuccess}
        availableCategories={availableCategories}
      />

      {/* OCR Text Viewer */}
      <OCRTextViewer
        isOpen={showOCRViewer}
        onClose={() => setShowOCRViewer(false)}
        document={document}
      />
    </div>
  )
}
