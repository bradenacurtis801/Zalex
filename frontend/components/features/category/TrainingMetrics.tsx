'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui'
import { categoryApi } from '@/api'
import type { ClassifierInfoResponse } from '@/generated'
import { TrainingMetadataFromJSON } from '@/generated'
import { useLanguage } from '@/contexts/LanguageContext'

interface TrainingMetricsProps {
  onRefresh?: () => void
}

export default function TrainingMetrics({ onRefresh }: TrainingMetricsProps) {
  const { t } = useLanguage()
  const [classifierInfo, setClassifierInfo] = useState<ClassifierInfoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const data = await categoryApi.getTrainingMetricsApiCategoriesTrainingMetricsGet()
      setClassifierInfo(data)
      // Don't call onRefresh here - it causes infinite loops when used with key prop
      // onRefresh should only be called explicitly by parent components
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('training.metrics.fetchError')
      setError(errorMessage)
      console.error('Error fetching training metrics:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="loader mx-auto mb-2"></div>
          <p className="text-gray-600">{t('training.metrics.loading')}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <Button onClick={fetchMetrics} className="mt-2" size="sm">
          {t('training.metrics.retry')}
        </Button>
      </div>
    )
  }

  // Parse training metadata from the metadata object (it's stored as training_metadata in snake_case)
  const rawTrainingMetadata = classifierInfo?.metadata?.training_metadata
  if (!classifierInfo || !rawTrainingMetadata) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        <p>{t('training.metrics.noMetadata')}</p>
      </div>
    )
  }

  // Parse the training metadata using the generated parser (handles snake_case to camelCase conversion)
  const trainingMetadata = TrainingMetadataFromJSON(rawTrainingMetadata)
  const trainingData = trainingMetadata.trainingData
  const performance = trainingMetadata.performanceMetrics
  const distribution = trainingData.distribution as Record<string, {
    total: number
    train: number
    test: number
    train_percentage: number
    test_percentage: number
  }>
  const maxCount = Math.max(...Object.values(distribution).map(d => d.total), 1)

  const formatDate = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return timestamp
    }
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  return (
    <div className="space-y-6">
      {/* Model Information */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('training.metrics.modelInformation')}</h3>
          <Button onClick={fetchMetrics} variant="secondary" size="sm">
            {t('training.metrics.refresh')}
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-600">{t('training.metrics.modelId')}</div>
            <div className="text-base text-gray-900 mt-1">{trainingMetadata.modelId}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">{t('training.metrics.modelType')}</div>
            <div className="text-base text-gray-900 mt-1">{trainingMetadata.modelType}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">{t('training.metrics.trainingTimestamp')}</div>
            <div className="text-base text-gray-900 mt-1">{formatDate(trainingMetadata.trainingTimestamp)}</div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">{t('training.metrics.classifierType')}</div>
            <div className="text-base text-gray-900 mt-1">{classifierInfo.type}</div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-600">{t('training.metrics.totalDocuments')}</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{trainingData.totalDocuments}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-600">{t('training.metrics.categories')}</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{trainingData.totalCategories}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-600">{t('training.metrics.trainSamples')}</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{trainingData.trainSamples}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-600">{t('training.metrics.testSamples')}</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{trainingData.testSamples}</div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('training.metrics.performanceMetrics')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">{t('training.metrics.accuracy')}</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('training.metrics.trainAccuracy')}</span>
                <span className="text-lg font-bold text-blue-600">{formatPercentage(performance.trainAccuracy)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('training.metrics.testAccuracy')}</span>
                <span className="text-lg font-bold text-green-600">{formatPercentage(performance.testAccuracy)}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">{t('training.metrics.confidenceStatistics')}</h4>
            <div className="space-y-2">
              <div>
                <div className="text-xs text-gray-500 mb-1">{t('training.metrics.trainConfidence')}</div>
                <div className="text-sm">
                  {t('training.metrics.mean')}: {formatPercentage(performance.trainConfidence.mean)} | 
                  {t('training.metrics.range')}: {formatPercentage(performance.trainConfidence.min)} - {formatPercentage(performance.trainConfidence.max)}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">{t('training.metrics.testConfidence')}</div>
                <div className="text-sm">
                  {t('training.metrics.mean')}: {formatPercentage(performance.testConfidence.mean)} | 
                  {t('training.metrics.range')}: {formatPercentage(performance.testConfidence.min)} - {formatPercentage(performance.testConfidence.max)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Distribution */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('training.metrics.trainingDataDistribution')}</h3>
        {Object.keys(distribution).length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>{t('training.metrics.noDistribution')}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(distribution).map(([category, data]) => (
              <div key={category} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900">{category}</span>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-lg font-bold text-violet-600">{data.total}</div>
                    <div className="text-xs text-gray-500">{t('training.metrics.totalDocumentsLabel')}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-2">
                  <div>
                    <div className="text-xs text-gray-500">{t('training.metrics.train')}</div>
                    <div className="text-sm font-medium text-blue-600">{data.train} ({data.train_percentage}%)</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">{t('training.metrics.test')}</div>
                    <div className="text-sm font-medium text-green-600">{data.test} ({data.test_percentage}%)</div>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-violet-600 h-2 rounded-full transition-all"
                    style={{ width: `${(data.total / maxCount) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Feature Extraction & Model Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('training.metrics.featureExtraction')}</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.vectorizerType')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.vectorizerType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.maxFeatures')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.maxFeatures.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.ngramRange')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.ngramRange.join('-')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.vocabularySize')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.vocabularySize.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.minDf')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.minDf}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.maxDf')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.maxDf}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.sublinearTf')}</span>
              <span className="font-medium">{trainingMetadata.featureExtraction.sublinearTf ? t('training.metrics.yes') : t('training.metrics.no')}</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('training.metrics.modelParameters')}</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">{t('training.metrics.modelType')}</span>
              <span className="font-medium">{trainingMetadata.modelParameters.modelType}</span>
            </div>
            {trainingMetadata.modelParameters.alpha !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-600">{t('training.metrics.alpha')}</span>
                <span className="font-medium">{trainingMetadata.modelParameters.alpha}</span>
              </div>
            )}
            {trainingMetadata.modelParameters.c !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-600">C</span>
                <span className="font-medium">{trainingMetadata.modelParameters.c}</span>
              </div>
            )}
            {trainingMetadata.modelParameters.solver && (
              <div className="flex justify-between">
                <span className="text-gray-600">{t('training.metrics.solver')}</span>
                <span className="font-medium">{trainingMetadata.modelParameters.solver}</span>
              </div>
            )}
            {trainingMetadata.modelParameters.classWeight && (
              <div className="flex justify-between">
                <span className="text-gray-600">{t('training.metrics.classWeight')}</span>
                <span className="font-medium">{trainingMetadata.modelParameters.classWeight}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


