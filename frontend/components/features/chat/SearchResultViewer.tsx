'use client'

import { useState, useEffect, useRef } from 'react'
import { SearchResult } from '@/generated/models/SearchResult'
import { CategoryDocument } from '@/hooks/useCategories'
import PDFViewer from '../categories/PDFViewer'
import { Button } from '@/components/ui'
import { uploadApi } from '@/api'

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

interface SearchResultItemProps {
  result: SearchResult
  index: number
  onViewDocument: (result: SearchResult) => void
}

function SearchResultItem({ result, index, onViewDocument }: SearchResultItemProps) {
  const [pageImage, setPageImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showText, setShowText] = useState(false)

  useEffect(() => {
    loadPageImage()
  }, [result.source, result.page])

  const loadPageImage = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const pagesData = await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGet({
        documentId: result.source
      })
      
      // Find the specific page
      const page = pagesData.pages?.find((p: {page_number: number, image_data: string, width: number, height: number}) => p.page_number === result.page)
      if (page) {
        setPageImage(page.image_data)
      } else {
        setError('Page not found')
      }
    } catch (err) {
      console.error('Error loading page image:', err)
      setError('Failed to load page image')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-3 hover:border-blue-300 transition-colors">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-gray-600 bg-gray-200 px-2 py-0.5 rounded">
          #{index + 1}
        </span>
        <span className="text-xs text-gray-500">
          Page {result.page}
        </span>
      </div>

      {/* Page Image */}
      <div className="mb-3 bg-white rounded border border-gray-200 overflow-hidden">
        {loading && (
          <div className="flex items-center justify-center h-48">
            <div className="loader"></div>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
            {error}
          </div>
        )}
        {pageImage && !loading && !error && (
          <img
            src={pageImage}
            alt={`Page ${result.page}`}
            className="w-full h-auto max-h-64 object-contain mx-auto"
          />
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowText(!showText)}
          className="text-xs text-gray-600 hover:text-gray-800 hover:underline font-medium"
        >
          {showText ? 'Hide' : 'View'} matched text
        </button>
        <span className="text-gray-300">|</span>
        <button
          onClick={() => onViewDocument(result)}
          className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium"
        >
          View full document →
        </button>
      </div>

      {/* Text Preview */}
      {showText && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-600 mb-1 font-medium">Matched text:</p>
          <p className="text-sm text-gray-800 bg-white p-2 rounded border border-gray-200">
            {result.text}
          </p>
        </div>
      )}
    </div>
  )
}

export default function SearchResultViewer({ results, query }: SearchResultViewerProps) {
  const [selectedResult, setSelectedResult] = useState<{ documentId: string; pageNumber: number } | null>(null)
  const [visibleCount, setVisibleCount] = useState(5)
  const RESULTS_PER_PAGE = 10

  const handleViewDocument = (result: SearchResult) => {
    setSelectedResult({
      documentId: result.source,
      pageNumber: result.page
    })
  }

  const handleLoadMore = () => {
    setVisibleCount(prev => Math.min(prev + RESULTS_PER_PAGE, results.length))
  }

  const hasMore = visibleCount < results.length
  const visibleResults = results.slice(0, visibleCount)

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
    <div className="space-y-3">
      <div className="space-y-2">
        {visibleResults.map((result, index) => (
          <SearchResultItem
            key={index}
            result={result}
            index={index}
            onViewDocument={handleViewDocument}
          />
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <button
            onClick={handleLoadMore}
            className="text-sm text-blue-600 hover:text-blue-800 hover:underline font-medium px-4 py-2 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            Load more ({results.length - visibleCount} remaining)
          </button>
        </div>
      )}

      {/* Total Results Count */}
      {!hasMore && results.length > RESULTS_PER_PAGE && (
        <p className="text-xs text-gray-500 text-center pt-2">
          Showing all {results.length} result{results.length !== 1 ? 's' : ''}
        </p>
      )}

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

