'use client'

import ProtectedRoute from '@/components/ProtectedRoute'
import Header from '@/components/layout/Header'
import ChatInterface from '@/components/features/chat/ChatInterface'

export default function SearchPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        <Header title="Document Search" />

        {/* Main Content */}
        <main className="max-w-4xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Search Documents</h2>
              <p className="text-gray-600">
                Search through your documents using natural language queries.
              </p>
            </div>

            <ChatInterface />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
