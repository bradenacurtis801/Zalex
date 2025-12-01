'use client'

import { useState, useEffect } from 'react'
import { useFeedback } from '@/hooks/useFeedback'
import { ReclassificationRequest } from '@/generated'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import { useLanguage } from '@/contexts/LanguageContext'

interface ReclassificationModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  document: {
    id: string
    filename: string
    category: string
    confidence: number
  }
  availableCategories: string[]
}

export default function ReclassificationModal({
  isOpen,
  onClose,
  onSuccess,
  document,
  availableCategories
}: ReclassificationModalProps) {
  const { t } = useLanguage()
  const { reclassifyDocument, loading, error } = useFeedback()
  const [selectedCategory, setSelectedCategory] = useState(document.category)
  const [userComment, setUserComment] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusType, setStatusType] = useState<'success' | 'error' | 'warning'>('success')

  useEffect(() => {
    if (isOpen) {
      setSelectedCategory(document.category)
      setUserComment('')
      setStatusMessage('')
    }
  }, [isOpen, document])

  const handleReclassify = async () => {
    if (selectedCategory === document.category) {
      setStatusMessage(t('reclassification.selectDifferentCategory'))
      setStatusType('warning')
      return
    }

    try {
      const request: ReclassificationRequest = {
        id: document.id,
        filename: document.filename,
        currentCategory: document.category,
        newCategory: selectedCategory,
        confidence: document.confidence,
        userComment: userComment.trim() || undefined
      }

      const response = await reclassifyDocument(request)
      
      if (response.success) {
        setStatusMessage(response.message)
        setStatusType('success')
        
        // Close modal after a short delay
        setTimeout(() => {
          onSuccess()
          onClose()
        }, 1500)
      } else {
        setStatusMessage(response.message)
        setStatusType('error')
      }
    } catch (err) {
      setStatusMessage(t('reclassification.error'))
      setStatusType('error')
    }
  }

  const handleClose = () => {
    if (!loading) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {t('reclassification.title')}
          </h3>
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

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('reclassification.document')}
            </label>
            <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {document.filename}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {t('reclassification.current')} {document.category} ({(document.confidence * 100).toFixed(1)}% {t('documentViewer.confidence').toLowerCase()})
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('reclassification.newCategory')}
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              disabled={loading}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50"
            >
              {availableCategories.map((category) => (
                <option key={category} value={category}>
                  {category === 'other' ? t('reclassification.other') : category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('reclassification.comment')}
            </label>
            <textarea
              value={userComment}
              onChange={(e) => setUserComment(e.target.value)}
              disabled={loading}
              placeholder={t('reclassification.commentPlaceholder')}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-violet-500 focus:border-violet-500 disabled:opacity-50"
              rows={3}
            />
          </div>

          {statusMessage && (
            <StatusMessage message={statusMessage} type={statusType} />
          )}

          {error && (
            <StatusMessage message={error} type="error" />
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              variant="secondary"
              onClick={handleClose}
              disabled={loading}
            >
              {t('common.cancel')}
            </Button>
            <Button
              onClick={handleReclassify}
              disabled={loading || selectedCategory === document.category}
              isLoading={loading}
            >
              {loading ? t('reclassification.reclassifying') : t('reclassification.reclassifyButton')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
