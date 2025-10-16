'use client'

import { DocumentClassification } from '@/generated'

interface ClassificationResultsProps {
  classifications: DocumentClassification[]
}

export default function ClassificationResults({ classifications }: ClassificationResultsProps) {
  if (!classifications || classifications.length === 0) {
    return null
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'personas':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'mercantil':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'inmuebles':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'other':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-indigo-100 text-indigo-800 border-indigo-200'
    }
  }

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'personas':
        return 'Personas'
      case 'mercantil':
        return 'Mercantil'
      case 'inmuebles':
        return 'Inmuebles'
      case 'other':
        return 'Other'
      default:
        return category.charAt(0).toUpperCase() + category.slice(1)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="mt-4 space-y-3">
      <h3 className="text-lg font-semibold text-gray-900">Document Classifications</h3>
      <div className="space-y-2">
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
              <span className="text-sm text-gray-500">Confidence:</span>
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
