'use client'

import { useState, useEffect, useRef } from 'react'
import { CategoryDocument } from '@/hooks/useCategories'
import { uploadApi } from '@/api'
import PDFPage from './PDFPage'
import { useLanguage } from '@/contexts/LanguageContext'

interface PDFViewerProps {
  document: CategoryDocument
  className?: string
  onScroll?: (scrollTop: number) => void
  containerRef?: React.RefObject<HTMLDivElement>
  currentPage?: number
  onPageChange?: (pageIndex: number) => void
}

export default function PDFViewer({
  document,
  className = '',
  onScroll,
  containerRef,
  currentPage = 0,
  onPageChange
}: PDFViewerProps) {
  const { t } = useLanguage()
  const [pdfPages, setPdfPages] = useState<Array<{page_number: number, image_data: string, width: number, height: number}>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const internalRef = useRef<HTMLDivElement>(null)
  const scrollRef = containerRef || internalRef

  useEffect(() => {
    loadPDFPages()
  }, [document])

  // Scroll to the current page when pages are loaded or currentPage changes
  useEffect(() => {
    if (!loading && pdfPages.length > 0 && currentPage >= 0) {
      const targetPageNumber = currentPage // data-page is 0-indexed
      const scrollToTargetPage = () => {
        const container = scrollRef.current
        if (container) {
          const pageElement = container.querySelector(`[data-page="${targetPageNumber}"]`)
          if (pageElement) {
            pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            return true
          }
        }
        return false
      }

      // Try immediately
      if (!scrollToTargetPage()) {
        // If not found, try again after a short delay to allow images to render
        const timer = setTimeout(() => {
          scrollToTargetPage()
        }, 500)

        return () => clearTimeout(timer)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadPDFPages = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const pagesData = await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGet({
        documentId: document.id
      })
      setPdfPages(pagesData.pages || [])
    } catch (err) {
      console.error('Error loading PDF pages:', err)
      setError(t('pdfViewer.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (onScroll) {
      onScroll(e.currentTarget.scrollTop)
    }
    
    // Auto-switch to page that's more than 50% in view
    const container = e.currentTarget
    const containerRect = container.getBoundingClientRect()
    const containerHeight = containerRect.height
    const scrollTop = container.scrollTop
    
    // Find which page is most visible
    let mostVisiblePageNumber = 0
    let maxVisibility = 0
    
    pdfPages.forEach((page) => {
      const pageElement = container.querySelector(`[data-page="${page.page_number}"]`)
      if (pageElement) {
        const pageRect = pageElement.getBoundingClientRect()
        const pageTop = pageRect.top - containerRect.top + scrollTop
        const pageBottom = pageTop + pageRect.height
        
        // Calculate visible portion
        const visibleTop = Math.max(pageTop, scrollTop)
        const visibleBottom = Math.min(pageBottom, scrollTop + containerHeight)
        const visibleHeight = Math.max(0, visibleBottom - visibleTop)
        const visibility = visibleHeight / pageRect.height
        
        if (visibility > maxVisibility) {
          maxVisibility = visibility
          mostVisiblePageNumber = page.page_number
        }
      }
    })
    
    // If the most visible page is more than 50% visible, switch to it
    if (maxVisibility > 0.5 && mostVisiblePageNumber !== currentPage) {
      console.log(`Auto-switching to page ${mostVisiblePageNumber + 1} (${(maxVisibility * 100).toFixed(1)}% visible)`)
      // This will be handled by the parent component
      if (onPageChange) {
        onPageChange(mostVisiblePageNumber)
      }
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="loader mx-auto mb-4"></div>
          <p className="text-gray-600">{t('pdfViewer.loading')}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="text-6xl mb-4">📄</div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">{t('pdfViewer.loadError')}</h4>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadPDFPages}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {t('pdfViewer.tryAgain')}
          </button>
        </div>
      </div>
    )
  }

  if (pdfPages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="text-6xl mb-4">📄</div>
          <h4 className="text-lg font-medium text-gray-900 mb-2">{t('pdfViewer.noPages')}</h4>
          <p className="text-gray-600">{t('pdfViewer.noPagesDescription')}</p>
        </div>
      </div>
    )
  }

  return (
    <div 
      ref={scrollRef}
      className={`overflow-auto ${className}`}
      onScroll={handleScroll}
    >
      <div className="space-y-4 p-4">
        {pdfPages.map((page) => {
          const isCurrentPage = page.page_number === currentPage
          
          return (
            <PDFPage
              key={page.page_number}
              page={page}
            />
          )
        })}
      </div>
    </div>
  )
}
