'use client'

import { useState, useEffect, useRef } from 'react'
import { SearchResult } from '@/generated/models/SearchResult'
import { CategoryDocument } from '@/hooks/useCategories'
import PDFViewer from './PDFViewer'
import { Button } from '@/components/ui'

interface SearchResultViewerProps {
  results: SearchResult[]
  query: string
}

interface PDFViewerModalProps {
  isOpen: boolean
  onClose: () => void
  documentId: string
  pageNumber: number
}

function PDFViewerModal({ isOpen, onClose, documentId, pageNumber }: PDFViewerModalProps) {
  const pdfContainerRef = useRef<HTMLDivElement>(null)

  // Create a minimal CategoryDocument object - PDFViewer only needs the id
  const document: CategoryDocument = {
    id: documentId,
    filename: 'Document',
    category: 'unknown',
    confidence: 0,
    timestamp: ''
  }

  // Convert page number from 1-based (from API) to 0-based (for PDFViewer)
  const currentPage = pageNumber - 1

  // Scroll to the specific page when modal opens and pages are loaded
  useEffect(() => {
    if (isOpen && pdfContainerRef.current) {
      // Wait for pages to load, then scroll to the target page
      const scrollToPage = () => {
        const container = pdfContainerRef.current
        if (container) {
          // Find the page element with the matching page number
          const pageElement = container.querySelector(`[data-page="${pageNumber}"]`)
          if (pageElement) {
            pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            return true
          }
        }
        return false
      }

      // Try immediately
      if (!scrollToPage()) {
        // If not found, try again after a delay
        const timer = setTimeout(() => {
          scrollToPage()
        }, 1000) // Longer delay to allow pages to render

        return () => clearTimeout(timer)
      }
    }
  }, [isOpen, pageNumber])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Original Document
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Document ID: {documentId.slice(0, 16)}...
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

        {/* PDF Viewer */}
        <div className="flex-1 p-6 overflow-hidden">
          <div className="mb-4 text-sm text-gray-600">
            Showing page {pageNumber} of the document
          </div>
          <div className="h-full">
            <PDFViewer
              document={document}
              currentPage={currentPage}
              containerRef={pdfContainerRef}
              className="h-full"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
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

export default function SearchResultViewer({ results, query }: SearchResultViewerProps) {
  const [selectedResult, setSelectedResult] = useState<{ documentId: string; pageNumber: number } | null>(null)

  const handleViewDocument = (result: SearchResult) => {
    setSelectedResult({
      documentId: result.source,
      pageNumber: result.page
    })
  }

  const formatScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'N/A'
    // Lower score is better for L2 distance, so we'll show it as-is
    return score.toFixed(4)
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h4 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h4>
        <p className="text-gray-600">No documents match your search query: &quot;{query}&quot;</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Search Results for: &quot;{query}&quot;
        </h3>
        <p className="text-sm text-gray-600">
          Found {results.length} result{results.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="space-y-3">
        {results.map((result, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    Result {index + 1}
                  </span>
                  <span className="text-xs text-gray-500">
                    Document: {result.source.slice(0, 16)}...
                  </span>
                  <span className="text-xs text-gray-500">
                    Page {result.page}
                  </span>
                  {result.score !== null && result.score !== undefined && (
                    <span className="text-xs text-gray-500">
                      Score: {formatScore(result.score)}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 line-clamp-3">
                  {result.text}
                </p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-200">
              <Button
                onClick={() => handleViewDocument(result)}
                className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2"
              >
                Go to original document
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* PDF Viewer Modal */}
      {selectedResult && (
        <PDFViewerModal
          isOpen={true}
          onClose={() => setSelectedResult(null)}
          documentId={selectedResult.documentId}
          pageNumber={selectedResult.pageNumber}
        />
      )}
    </div>
  )
}

