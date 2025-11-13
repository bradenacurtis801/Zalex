'use client'

import { useState, useEffect, useRef } from 'react'
import { SearchResult } from '@/generated/models/SearchResult'
import { Entity } from '@/generated/models/Entity'
import { CategoryDocument } from '@/hooks/useCategories'
import PDFViewer from '../categories/PDFViewer'
import { Button } from '@/components/ui'
import { uploadApi } from '@/api'

function HighlightedText({ text, entities }: { text: string; entities: Entity[] }) {
  if (!entities || entities.length === 0) {
    return <p className="text-sm text-gray-800 bg-white p-2 rounded border border-gray-200">{text}</p>
  }

  // Sort entities by start position
  const sortedEntities = [...entities].sort((a, b) => a.start - b.start)
  
  // Create array of text segments with entity highlights
  const segments: Array<{ text: string; isEntity: boolean; entity?: Entity }> = []
  let lastIndex = 0

  sortedEntities.forEach((entity) => {
    // Add text before entity
    if (entity.start > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, entity.start),
        isEntity: false
      })
    }
    
    // Add entity
    segments.push({
      text: text.slice(entity.start, entity.end),
      isEntity: true,
      entity
    })
    
    lastIndex = entity.end
  })
  
  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      isEntity: false
    })
  }

  // Color mapping for entity types
  const getEntityColor = (label: string) => {
    const colors: Record<string, string> = {
      'PERSON': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'PER': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'ORG': 'bg-green-100 text-green-800 border-green-300',
      'ORGANIZATION': 'bg-green-100 text-green-800 border-green-300',
      'LOC': 'bg-blue-100 text-blue-800 border-blue-300',
      'LOCATION': 'bg-blue-100 text-blue-800 border-blue-300',
      'GPE': 'bg-indigo-100 text-indigo-800 border-indigo-300',
      'DATE': 'bg-purple-100 text-purple-800 border-purple-300',
      'MONEY': 'bg-pink-100 text-pink-800 border-pink-300',
    }
    return colors[label] || 'bg-gray-100 text-gray-800 border-gray-300'
  }

  return (
    <p className="text-sm text-gray-800 bg-white p-2 rounded border border-gray-200">
      {segments.map((segment, idx) => (
        segment.isEntity && segment.entity ? (
          <span
            key={idx}
            className={`px-1 rounded border ${getEntityColor(segment.entity.label)}`}
            title={`${segment.entity.label}: ${segment.entity.text}`}
          >
            {segment.text}
          </span>
        ) : (
          <span key={idx}>{segment.text}</span>
        )
      ))}
    </p>
  )
}

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

  // Page numbers are 0-indexed, PDFViewer also uses 0-indexed
  const currentPage = pageNumber

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
        <div className="flex-1 p-6 overflow-hidden flex flex-col min-h-0">
          <div className="mb-4 text-sm text-gray-600 flex-shrink-0">
            Showing page {pageNumber + 1} of the document
          </div>
          <div className="flex-1 min-h-0 overflow-auto">
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
  category?: string
  onCategoryUpdate?: (documentId: string, category: string) => void
}

function SearchResultItem({ result, index, onViewDocument, category, onCategoryUpdate }: SearchResultItemProps) {
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
      // Request only the specific page we need
      const pagesData = await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGet({
        documentId: result.source,
        pages: `${result.page}` // Pass the page number as a string (comma-separated if multiple)
      })
      
      // Update category from response if available
      if (pagesData.category && result.source && onCategoryUpdate) {
        onCategoryUpdate(result.source, pagesData.category)
      }
      
      // Find the specific page (should only be one page in the response)
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
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-xs font-medium text-gray-600 bg-gray-200 px-2 py-0.5 rounded">
          #{index + 1}
        </span>
        <span className="text-xs text-gray-500">
          Page {result.page + 1}
        </span>
        {category && (
          <>
            <span className="text-gray-300">•</span>
            <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              {category}
            </span>
          </>
        )}
        {/* Entity Type Summary */}
        {result.entities && result.entities.length > 0 && (
          <>
            <span className="text-gray-300">•</span>
            <div className="flex gap-1 flex-wrap">
              {Array.from(new Set(result.entities?.map((e) => e.label) || [])).slice(0, 3).map((label: string, idx: number) => (
                <span
                  key={idx}
                  className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-0.5 rounded border border-purple-200"
                  title={`${label} entities found`}
                >
                  {label}
                </span>
              ))}
              {Array.from(new Set(result.entities?.map((e) => e.label) || [])).length > 3 && (
                <span className="text-xs text-gray-500">
                  +{Array.from(new Set(result.entities?.map((e) => e.label) || [])).length - 3} more
                </span>
              )}
            </div>
          </>
        )}
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
            alt={`Page ${result.page + 1}`}
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
          <HighlightedText text={result.text} entities={result.entities || []} />
          
          {/* NER Entities */}
          {result.entities && result.entities.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-600 mb-2 font-medium">Extracted entities:</p>
              <div className="flex flex-wrap gap-2">
                {result.entities?.map((entity, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-blue-50 text-blue-700 border border-blue-200"
                    title={`${entity.label}: ${entity.text}${entity.confidence ? ` (${(entity.confidence * 100).toFixed(0)}%)` : ''}`}
                  >
                    <span className="font-medium">{entity.label}:</span>
                    <span>{entity.text}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function SearchResultViewer({ results, query }: SearchResultViewerProps) {
  const [selectedResult, setSelectedResult] = useState<{ documentId: string; pageNumber: number } | null>(null)
  const [visibleCount, setVisibleCount] = useState(5)
  const [documentCategories, setDocumentCategories] = useState<Map<string, string>>(new Map())
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
            category={documentCategories.get(result.source)}
            onCategoryUpdate={(documentId: string, category: string) => {
              setDocumentCategories(prev => {
                const newMap = new Map(prev)
                newMap.set(documentId, category)
                return newMap
              })
            }}
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

