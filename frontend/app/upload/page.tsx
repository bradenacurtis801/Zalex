'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Header from '@/components/layout/Header'
import DocumentUpload from '@/components/features/upload/DocumentUpload'
import { StatusMessage } from '@/components/ui'
import { useLanguage } from '@/contexts/LanguageContext'

export default function UploadPage() {
  const { t } = useLanguage()
  const { user } = useAuth()
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [uploadStatusType, setUploadStatusType] = useState<'success' | 'error' | 'warning'>('success')

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        <Header title={t('upload.title')} />

        {/* Main Content */}
        <main className="max-w-4xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('upload.title')}</h2>
              <p className="text-gray-600">
                {t('upload.description', 'Upload PDF, JPG, or PNG files to be processed and classified by our AI system.')}
              </p>
            </div>

            <DocumentUpload 
              onUploadStatus={(status, type = 'success') => {
                setUploadStatus(status)
                setUploadStatusType(type)
              }} 
            />

            {uploadStatus && (
              <div className="mt-6">
                <StatusMessage 
                  message={uploadStatus} 
                  type={uploadStatusType}
                />
              </div>
            )}

            {/* Upload Guidelines */}
            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">{t('upload.guidelinesTitle', 'Upload Guidelines')}</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• {t('upload.supportedFormats', 'Supported formats: PDF, JPG, JPEG, PNG')}</li>
                <li>• {t('upload.maxFileSize', 'Maximum file size: 10MB per file')}</li>
                <li>• {t('upload.autoClassification', 'Documents will be automatically classified by AI')}</li>
                <li>• {t('upload.ocr', 'OCR will be performed on scanned documents')}</li>
                <li>• {t('upload.multiUpload', 'You can upload multiple files at once')}</li>
              </ul>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
