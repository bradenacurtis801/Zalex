'use client'

import { useState, useEffect, useRef } from 'react'
import { CategoryDocument } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import PDFViewer from './PDFViewer'
import OCRPage from './OCRPage'
import { ocrApi } from '@/api'
import type { OCRDataResponse } from '@/generated/models/OCRDataResponse'

interface OCRTextViewerProps {
  isOpen: boolean
  onClose: () => void
  document: CategoryDocument
}

export default function OCRTextViewer({
  isOpen,
  onClose,
  document
}: OCRTextViewerProps) {
  const [ocrData, setOcrData] = useState<OCRDataResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [showWords, setShowWords] = useState(true)
  const [showLines, setShowLines] = useState(false)
  const [confidenceFilter, setConfidenceFilter] = useState(0)
  
  const pdfContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && document) {
      loadOCRData()
    }
  }, [isOpen, document])



  const loadOCRData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const data = await ocrApi.getDocumentOcrDataApiDocumentsDocumentIdOcrGet({
        documentId: document.id
      })
      
      // Ensure we have the expected data structure
      if (data && Array.isArray(data.ocrData)) {
        data.ocrData.forEach((page: OCRDataResponse, index: number) => {
          if (page.wordsData && page.wordsData.length > 0) {
          }
        })
        
        setOcrData(data.ocrData)
        setCurrentPage(0)
      } else {
        console.warn('Unexpected OCR data structure:', data)
        setOcrData([])
        setError('No OCR data available for this document')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load OCR data')
      console.error('Error loading OCR data:', err)
    } finally {
      setLoading(false)
    }
  }



  const handlePageChange = (pageIndex: number) => {
    console.log(`Auto-switching OCR to page ${pageIndex + 1}`)
    setCurrentPage(pageIndex)
  }

  const jumpToTarget = (targetElement: HTMLElement, container: HTMLElement) => {
    const targetScrollTop = targetElement.offsetTop - container.offsetTop
    container.scrollTop = targetScrollTop
  }

  const handlePageNavigation = (targetPage: number) => {
    if (targetPage < 0 || targetPage >= ocrData.length) return
    
    console.log(`Manual navigation to page ${targetPage + 1}`)
    
    // Set the OCR page immediately
    setCurrentPage(targetPage)
    
    // Jump instantly to the target page in PDF viewer
    if (pdfContainerRef.current) {
      const targetElement = pdfContainerRef.current.querySelector(`[data-page="${targetPage + 1}"]`) as HTMLElement
      if (targetElement) {
        jumpToTarget(targetElement, pdfContainerRef.current)
      }
    }
  }

  const renderOCRPage = (pageData: OCRDataResponse) => {
    return (
      <OCRPage
        pageData={pageData}
        showWords={showWords}
        showLines={showLines}
        confidenceFilter={confidenceFilter}
      />
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-[95vw] h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b bg-gray-50">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              OCR Text Viewer
            </h3>
            <p className="text-sm text-gray-600">
              {document.filename} - Side-by-side PDF and OCR text
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation Bar */}
        {ocrData.length > 1 && (
          <div className="p-3 bg-blue-50 border-b">
            <div className="flex justify-center items-center space-x-4">
              <button
                onClick={() => handlePageNavigation(currentPage - 1)}
                disabled={currentPage === 0}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
              >
                ← Previous
              </button>
              <span className="text-sm text-gray-700 font-medium">
                Page {currentPage + 1} of {ocrData.length}
              </span>
              <button
                onClick={() => handlePageNavigation(currentPage + 1)}
                disabled={currentPage === ocrData.length - 1}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
              >
                Next →
              </button>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* PDF with OCR Overlay */}
          <div className="w-1/2 border-r">
            <div className="h-full flex flex-col">
              <div className="p-3 bg-gray-100 border-b">
                <h4 className="font-medium">PDF Viewer</h4>
              </div>
              <div 
                ref={pdfContainerRef}
                className="flex-1 overflow-auto relative"
              >
                {loading && (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <div className="loader mx-auto mb-4"></div>
                      <p className="text-gray-600">Loading OCR data...</p>
                    </div>
                  </div>
                )}

                {error && (
                  <div className="p-8">
                    <StatusMessage message={error} type="error" />
                    <Button onClick={loadOCRData} className="mt-4">
                      Retry
                    </Button>
                  </div>
                )}

                {!loading && !error && ocrData.length > 0 && (
                  <PDFViewer
                    document={document}
                    className="h-full"
                    containerRef={pdfContainerRef}
                    currentPage={currentPage}
                    onPageChange={handlePageChange}
                  />
                )}

                {!loading && !error && ocrData.length === 0 && (
                  <div className="p-8 text-center">
                    <div className="text-6xl mb-4">📄</div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No OCR Data</h4>
                    <p className="text-gray-600">
                      No OCR data available for this document. The document may not have been processed with OCR yet.
                    </p>
                    <Button 
                      onClick={loadOCRData} 
                      className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      Retry
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* OCR Page Display */}
          <div className="w-1/2">
            <div className="h-full flex flex-col">
              <div className="p-3 bg-gray-100 border-b">
                <h4 className="font-medium">OCR Text Display</h4>
              </div>
              
              <div className="flex-1 overflow-auto">
                {!loading && !error && ocrData.length > 0 && (
                  renderOCRPage(ocrData[currentPage])
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-4 border-t bg-gray-50">
          <Button
            variant="secondary"
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
