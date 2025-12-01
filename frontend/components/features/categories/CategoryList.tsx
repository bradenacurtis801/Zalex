'use client'

import { CategorySummary } from '@/hooks/useCategories'
import { Button } from '@/components/ui'
import { useLanguage } from '@/contexts/LanguageContext'

interface CategoryListProps {
  categories: CategorySummary[]
  onCategorySelect: (category: string) => void
  loading: boolean
}

export default function CategoryList({ categories, onCategorySelect, loading }: CategoryListProps) {
  const { t } = useLanguage()

  // Ensure categories is an array
  const safeCategories = Array.isArray(categories) ? categories : []

  if (safeCategories.length === 0 && !loading) {
    return (
      <div className="text-center p-8 text-gray-500">
        <div className="text-6xl mb-4">📁</div>
        <h3 className="text-lg font-medium mb-2">{t('categories.noCategories', 'No Categories Found')}</h3>
        <p className="text-sm">
          {t(
            'categories.noCategoriesDescription',
            'Upload some documents to see categories appear here.'
          )}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {safeCategories.map((category) => (
        <div
          key={category.category}
          className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:bg-gray-100 transition-colors cursor-pointer"
          onClick={() => onCategorySelect(category.category)}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 capitalize">
                {category.category.replace('_', ' ')}
              </h3>
              <p className="text-sm text-gray-600">
                {category.count} {t('categories.document', 'document')}{category.count !== 1 ? 's' : ''}
              </p>
              {category.lastUpdated && (
                <p className="text-xs text-gray-500 mt-1">
                  {t('categories.lastUpdated', 'Last updated')}: {new Date(category.lastUpdated).toLocaleDateString()}
                </p>
              )}
            </div>
            <div className="flex items-center text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
