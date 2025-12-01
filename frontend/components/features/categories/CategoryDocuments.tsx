'use client'

import { useState, useEffect } from 'react'
import { useCategories, CategoryDocument } from '@/hooks/useCategories'
import { useFeedback } from '@/hooks/useFeedback'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import { getCategoryColor } from '@/utils/categoryUtils'
import ReclassificationModal from './ReclassificationModal'
import DocumentViewerModal from './DocumentViewerModal'
import { useLanguage } from '@/contexts/LanguageContext'

interface CategoryDocumentsProps {
  category: string
  onError: (message: string) => void
  availableCategories?: string[]
}

export default function CategoryDocuments({ category, onError, availableCategories = [] }: CategoryDocumentsProps) {
  const { t } = useLanguage()
  const { 
    categoryDocuments, 
    documentsLoading, 
    documentsError,
    fetchDocumentsByCategory 
  } = useCategories()
  const [reclassifyModal, setReclassifyModal] = useState<{
    isOpen: boolean
    document: CategoryDocument | null
  }>({ isOpen: false, document: null })
  const [viewerModal, setViewerModal] = useState<{
    isOpen: boolean
    document: CategoryDocument | null
  }>({ isOpen: false, document: null })

  useEffect(() => {
    loadDocuments()
  }, [category])

  const loadDocuments = async () => {
    try {
      await fetchDocumentsByCategory(category)
    } catch (err) {
      onError(`Failed to load documents for ${category}`)
      console.error('Error loading documents:', err)
    }
  }

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }


  const handleReclassify = (document: CategoryDocument) => {
    setReclassifyModal({ isOpen: true, document })
  }

  const handleReclassifySuccess = async () => {
    // Reload documents after successful reclassification
    await loadDocuments()
  }

  const handleCloseModal = () => {
    setReclassifyModal({ isOpen: false, document: null })
  }

  const handleViewDocument = (document: CategoryDocument) => {
    setViewerModal({ isOpen: true, document })
  }

  const handleCloseViewer = () => {
    setViewerModal({ isOpen: false, document: null })
  }

  if (documentsLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-center">
          <div className="loader mx-auto mb-2"></div>
          <p className="text-gray-600">{t('categories.loadingDocuments')}</p>
        </div>
      </div>
    )
  }

  if (documentsError) {
    return (
      <div className="text-center p-6">
        <StatusMessage message={documentsError} type="error" />
        <Button onClick={loadDocuments} className="mt-4" size="sm">
          {t('categories.tryAgain')}
        </Button>
      </div>
    )
  }

  if (categoryDocuments.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <div className="text-4xl mb-4">📄</div>
        <h3 className="text-lg font-medium mb-2">{t('categories.noDocuments')}</h3>
        <p className="text-sm">{t('categories.noDocumentsInCategory', { category })}</p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-3">
        <div className="text-sm text-gray-600 mb-4">
          {t('categories.showingDocuments', { count: categoryDocuments.length })}
        </div>
        
        <div className="max-h-96 overflow-y-auto space-y-3 border border-gray-200 rounded-lg p-2">
          {categoryDocuments.map((doc, index) => (
          <div
            key={`${doc.filename}-${index}`}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate max-w-xs">
                  {doc.filename}
                </h4>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                      {t('categories.confidence')}: {formatConfidence(doc.confidence)}
                  </span>
                  <span>
                    {t('categories.added')}: {formatDate(doc.timestamp)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(doc.category)}`}>
                  {doc.category}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleViewDocument(doc)}
                  className="text-xs"
                >
                  {t('categories.view')}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleReclassify(doc)}
                  className="text-xs"
                >
                  {t('categories.reclassify')}
                </Button>
              </div>
            </div>
          </div>
        ))}
        </div>
      </div>

      {/* Reclassification Modal */}
      {reclassifyModal.document && (
        <ReclassificationModal
          isOpen={reclassifyModal.isOpen}
          onClose={handleCloseModal}
          onSuccess={handleReclassifySuccess}
          document={{
            id: reclassifyModal.document.id,
            filename: reclassifyModal.document.filename,
            category: reclassifyModal.document.category,
            confidence: reclassifyModal.document.confidence
          }}
          availableCategories={availableCategories}
        />
      )}

      {/* Document Viewer Modal */}
      {viewerModal.document && (
        <DocumentViewerModal
          isOpen={viewerModal.isOpen}
          onClose={handleCloseViewer}
          document={viewerModal.document}
          onReclassify={handleReclassify}
          availableCategories={availableCategories}
        />
      )}
    </>
  )
}
