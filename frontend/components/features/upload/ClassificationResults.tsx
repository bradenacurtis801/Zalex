'use client'

import { DocumentClassification } from '@/generated'
import { getCategoryColor, getCategoryLabel } from '@/utils/categoryUtils'
import { useLanguage } from '@/contexts/LanguageContext'

interface ClassificationResultsProps {
  classifications: DocumentClassification[]
}

export default function ClassificationResults({ classifications }: ClassificationResultsProps) {
  const { t } = useLanguage()
  if (!classifications || classifications.length === 0) {
    return null
  }


  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="mt-4 space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">{t('classificationResults.title')}</h3>
        <span className="text-sm text-gray-500">({classifications.length} {t('classificationResults.documents')})</span>
      </div>
      <div className="max-h-96 overflow-y-auto space-y-2 border border-gray-200 rounded-lg p-2">
        {classifications.map((classification, index) => (
          <div
            key={index}
            className="flex items-start justify-between p-3 bg-white border rounded-lg shadow-sm"
          >
            <div className="flex-1 min-w-0 mr-4">
              <div className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-2">
                <span 
                  className="text-sm font-medium text-gray-900 truncate"
                  title={classification.filename}
                >
                  {classification.filename.length > 30 
                    ? `${classification.filename.substring(0, 30)}...` 
                    : classification.filename
                  }
                </span>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full border flex-shrink-0 ${getCategoryColor(
                    classification.category
                  )}`}
                >
                  {getCategoryLabel(classification.category)}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              <span className="text-sm text-gray-500">{t('classificationResults.confidence')}</span>
              <span
                className={`text-sm font-medium ${getConfidenceColor(
                  classification.confidence
                )}`}
              >
                {(classification.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
