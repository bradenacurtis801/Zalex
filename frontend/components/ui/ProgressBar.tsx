'use client'

import { useState, useEffect } from 'react'
import { useLanguage } from '@/contexts/LanguageContext'

interface ProgressBarProps {
  progress: number
  currentFile?: string
  totalFiles?: number
  currentFileIndex?: number
  isVisible: boolean
  className?: string
}

export default function ProgressBar({
  progress,
  currentFile,
  totalFiles,
  currentFileIndex,
  isVisible,
  className = ''
}: ProgressBarProps) {
  const { t } = useLanguage()
  const [displayProgress, setDisplayProgress] = useState(0)

  // Smooth progress animation
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        setDisplayProgress(progress)
      }, 100)
      return () => clearTimeout(timer)
    } else {
      setDisplayProgress(0)
    }
  }, [progress, isVisible])

  if (!isVisible) return null

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 shadow-lg ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          {t('progressBar.processingDocuments')}
        </span>
        <span className="text-sm text-gray-500">
          {displayProgress}%
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div
          className="bg-violet-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${displayProgress}%` }}
        />
      </div>
      
      {currentFile && (
        <div className="text-xs text-gray-600">
          <div className="truncate">
            <span className="font-medium">{t('progressBar.current')}</span> {currentFile}
          </div>
          {totalFiles && currentFileIndex && (
            <div className="mt-1">
              {t('progressBar.file', { current: currentFileIndex, total: totalFiles })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
