'use client'

import { useState } from 'react'
import DocumentUpload from '@/components/features/upload/DocumentUpload'
import ChatInterface from '@/components/features/chat/ChatInterface'
import CategoryManager from '@/components/features/categories/CategoryManager'
import { StatusMessage } from '@/components/ui'

export default function Home() {
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [uploadStatusType, setUploadStatusType] = useState<'success' | 'error' | 'warning'>('success')

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-violet-800 text-white shadow-md p-4 flex items-center">
        <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <h1 className="text-2xl font-bold">ScanPro AI Document Agent</h1>
      </header>

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
  )
}
