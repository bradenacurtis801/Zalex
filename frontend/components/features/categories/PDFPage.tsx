'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useLanguage } from '@/contexts/LanguageContext'

interface PDFPageData {
  page_number: number
  image_data: string
  width: number
  height: number
}

interface PDFPageProps {
  page: PDFPageData
  className?: string
}

export default function PDFPage({ page, className = '' }: PDFPageProps) {
  const { t } = useLanguage()
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)
  const imageRef = useRef<HTMLImageElement>(null)

  const handleImageLoad = () => {
    setImageLoaded(true)
    setImageError(false)
  }

  const handleImageError = () => {
    console.error(`Failed to load page ${page.page_number + 1} image`)
    setImageError(true)
  }


  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`} data-page={page.page_number}>
      <div className="p-3 border-b bg-gray-50">
        <h4 className="font-medium text-gray-700">{t('pdfPage.page', { number: page.page_number + 1 })}</h4>
      </div>
      <div className="p-4 relative">
        {imageError ? (
          <div className="flex items-center justify-center h-64 bg-gray-100 rounded">
            <div className="text-center">
              <div className="text-4xl mb-2">📄</div>
              <p className="text-gray-600">{t('pdfPage.loadError')}</p>
            </div>
          </div>
        ) : (
          <>
            <img
              ref={imageRef}
              src={page.image_data}
              alt={t('pdfPage.altText', { number: page.page_number + 1 })}
              className="max-w-full h-auto mx-auto"
              style={{ maxHeight: '80vh' }}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
            
            
          </>
        )}
      </div>
    </div>
  )
}
