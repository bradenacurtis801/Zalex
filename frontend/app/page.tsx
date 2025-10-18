'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import DocumentUpload from '@/components/features/upload/DocumentUpload'
import ChatInterface from '@/components/features/chat/ChatInterface'
import CategoryManager from '@/components/features/categories/CategoryManager'
import Header from '@/components/layout/Header'
import { StatusMessage } from '@/components/ui'

export default function Home() {
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [uploadStatusType, setUploadStatusType] = useState<'success' | 'error' | 'warning'>('success')

  return (
    <ProtectedRoute>
      <div className="flex flex-col h-screen bg-gray-100">
        <Header title="ScanPro AI Document Agent" />

        {/* Main Content */}
        <main className="flex-grow flex flex-col lg:flex-row p-4 gap-4 overflow-hidden">
          {/* Left Panel: Document Enrollment */}
          <div className="lg:w-1/4 w-full bg-white p-6 rounded-lg shadow-lg flex flex-col">
            <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-violet-800">Document Enrollment</h2>
            <DocumentUpload onUploadStatus={(status, type = 'success') => {
              setUploadStatus(status)
              setUploadStatusType(type)
            }} />
            {uploadStatus && (
              <div className="mt-4 text-center">
                <StatusMessage 
                  message={uploadStatus} 
                  type={uploadStatusType}
                />
              </div>
            )}
          </div>

          {/* Middle Panel: Category Management */}
          <div className="lg:w-1/3 w-full bg-white p-6 rounded-lg shadow-lg flex flex-col">
            <CategoryManager />
          </div>

          {/* Right Panel: Chat Retrieval */}
          <div className="lg:w-2/5 w-full bg-white p-6 rounded-lg shadow-lg flex flex-col">
            <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-violet-800">Chat & Retrieve</h2>
            <ChatInterface />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
