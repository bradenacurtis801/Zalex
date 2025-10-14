'use client'

import { useState, useEffect } from 'react'
import { CategoryDocument } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import ReclassificationModal from './ReclassificationModal'

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
  const [pdfLoadError, setPdfLoadError] = useState(false)
  const [pdfPages, setPdfPages] = useState<Array<{page_number: number, image_data: string, width: number, height: number}>>([])
  const [showReclassifyModal, setShowReclassifyModal] = useState(false)

  useEffect(() => {
    if (isOpen && document) {
      loadDocumentContent()
      setPdfLoadError(false) // Reset PDF error state when opening new document
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
        
        // Fetch PDF pages (converted to images) - backend handles caching transparently
        try {
          const pagesResponse = await fetch(`/api/documents/${encodeURIComponent(document.filename)}/pages`)
          if (pagesResponse.ok) {
            const pagesData = await pagesResponse.json()
            setPdfPages(pagesData.pages || [])
          } else {
            throw new Error('Failed to load PDF pages')
          }
        } catch (err) {
          console.error('Error loading PDF pages:', err)
          setPdfLoadError(true)
        }
      } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(fileExtension || '')) {
        setContentType('image')
        setDocumentContent('') // No need to fetch content for images
      } else {
        setContentType('text')
        // For text files, try to fetch the content
        const response = await fetch(`/api/documents/${encodeURIComponent(document.filename)}/content`)
        
        if (!response.ok) {
          throw new Error(`Failed to load document content: ${response.status}`)
        }
        
        const data = await response.json()
        setDocumentContent(data.content || '')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document content')
      console.error('Error loading document content:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    // Create a download link for the document
    const link = window.document.createElement('a')
    link.href = `/api/documents/${encodeURIComponent(document.filename)}/download`
    link.download = document.filename
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
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
              <span className="ml-2 px-2 py-1 bg-violet-100 text-violet-800 rounded-full text-xs">
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
              <span className="font-medium text-gray-700">File Path:</span>
              <span className="ml-2 text-gray-600 text-xs break-all">
                {document.filePath}
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
                src={`/api/documents/${encodeURIComponent(document.filename)}/content`}
                alt={document.filename}
                className="max-w-full max-h-96 mx-auto rounded-lg shadow-lg"
                onError={() => setError('Failed to load image')}
              />
            </div>
          )}

          {!loading && !error && contentType === 'pdf' && !pdfLoadError && pdfPages.length > 0 && (
            <div className="space-y-4">
              {pdfPages.map((page) => (
                <div key={page.page_number} className="bg-white rounded-lg shadow-sm border">
                  <div className="p-3 border-b bg-gray-50">
                    <h4 className="font-medium text-gray-700">Page {page.page_number}</h4>
                  </div>
                  <div className="p-4">
                    <img
                      src={page.image_data}
                      alt={`Page ${page.page_number}`}
                      className="max-w-full h-auto mx-auto"
                      style={{ maxHeight: '80vh' }}
                      onError={() => {
                        console.error(`Failed to load page ${page.page_number} image`)
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {!loading && !error && contentType === 'pdf' && pdfPages.length === 0 && !pdfLoadError && (
            <div className="text-center p-8">
              <div className="text-6xl mb-4">📄</div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Loading PDF...</h4>
              <p className="text-gray-600 mb-4">
                Converting PDF pages to images...
              </p>
            </div>
          )}

          {!loading && !error && contentType === 'pdf' && pdfLoadError && (
            <div className="text-center p-8">
              <div className="text-6xl mb-4">📄</div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">PDF Load Error</h4>
              <p className="text-gray-600 mb-4">
                Unable to convert PDF to images. You can download it to view.
              </p>
              <div className="space-x-3">
                <Button onClick={handleDownload}>
                  Download PDF
                </Button>
                <Button 
                  variant="secondary" 
                  onClick={() => {
                    setPdfLoadError(false)
                    loadDocumentContent()
                  }}
                >
                  Try Again
                </Button>
              </div>
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
    </div>
  )
}
