'use client'

import ProtectedRoute from '@/components/ProtectedRoute'
import Header from '@/components/layout/Header'
import CategoryManager from '@/components/features/categories/CategoryManager'

export default function CategoriesPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        <Header title="Category Management" />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto p-6">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Document Categories</h2>
              <p className="text-gray-600">
                Manage document categories and view classified documents.
              </p>
            </div>

            <CategoryManager />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
