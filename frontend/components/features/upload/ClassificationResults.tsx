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
      case 'birth_certificate':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'marriage_certificate':
        return 'bg-pink-100 text-pink-800 border-pink-200'
      case 'property_deeds':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'birth_certificate':
        return 'Birth Certificate'
      case 'marriage_certificate':
        return 'Marriage Certificate'
      case 'property_deeds':
        return 'Property Deed'
      default:
        return category
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
            className="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm"
          >
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-900">
                  {classification.filename}
                </span>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(
                    classification.category
                  )}`}
                >
                  {getCategoryLabel(classification.category)}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
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
