'use client'

import { useState } from 'react'
import { useCategories } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { StatusMessage } from '@/components/ui'
import CategoryList from './CategoryList'
import CategoryDocuments from './CategoryDocuments'

export default function CategoryManager() {
  const { 
    categorySummary, 
    summaryLoading, 
    summaryError, 
    fetchCategorySummary,
    clearSelectedCategory
  } = useCategories()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [statusType, setStatusType] = useState<'success' | 'error' | 'warning'>('success')

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category)
    setStatusMessage('')
  }

  const handleBackToList = () => {
    setSelectedCategory(null)
    clearSelectedCategory()
    setStatusMessage('')
  }

  const handleRefresh = async () => {
    setStatusMessage('Refreshing categories...')
    setStatusType('success')
    try {
      await fetchCategorySummary()
      setStatusMessage('Categories refreshed successfully!')
      setStatusType('success')
    } catch (err) {
      console.error('Error refreshing categories:', err)
      setStatusMessage('Failed to refresh categories')
      setStatusType('error')
    }
  }


  if (summaryLoading && categorySummary.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="loader mx-auto mb-4"></div>
          <p className="text-gray-600">Loading categories...</p>
        </div>
      </div>
    )
  }

  if (summaryError) {
    return (
      <div className="text-center p-6">
        <StatusMessage message={summaryError} type="error" />
        <Button onClick={handleRefresh} className="mt-4">
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 border-b pb-2">
        <h2 className="text-xl font-semibold text-violet-800">
          {selectedCategory ? `Documents in ${selectedCategory}` : 'Document Categories'}
        </h2>
        <div className="flex gap-2">
          {selectedCategory && (
            <Button 
              variant="secondary" 
              onClick={handleBackToList}
              size="sm"
            >
              ← Back to Categories
            </Button>
          )}
          <Button 
            variant="secondary" 
            onClick={handleRefresh}
            size="sm"
            isLoading={summaryLoading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Message */}
      {statusMessage && (
        <div className="mb-4">
          <StatusMessage message={statusMessage} type={statusType} />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {selectedCategory ? (
          <CategoryDocuments 
            category={selectedCategory}
            onError={(message) => {
              setStatusMessage(message)
              setStatusType('error')
            }}
            availableCategories={categorySummary.map(cat => cat.category)}
          />
        ) : (
          <CategoryList 
            categories={categorySummary}
            onCategorySelect={handleCategorySelect}
            loading={summaryLoading}
          />
        )}
      </div>
    </div>
  )
}
