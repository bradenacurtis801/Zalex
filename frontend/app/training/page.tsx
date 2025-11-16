'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Header from '@/components/layout/Header'
import TrainingMetrics from '@/components/features/category/TrainingMetrics'
import ClassificationTraining from '@/components/features/category/ClassificationTraining'

export default function TrainingPage() {
  const { user } = useAuth()
  const [refreshKey, setRefreshKey] = useState(0)

  // Check if user is admin
  if (user?.user_role !== 'admin') {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-100">
          <Header title="Classification Training" />
          <main className="max-w-7xl mx-auto p-6">
            <div className="bg-white border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-600">Access denied. Admin privileges required.</p>
            </div>
          </main>
        </div>
      </ProtectedRoute>
    )
  }

  const handleCategoryCreated = () => {
    // Trigger refresh of metrics by changing the key, which forces a remount
    setRefreshKey(prev => prev + 1)
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        <Header title="Classification Training" />
        
        <main className="max-w-7xl mx-auto p-6">
          <div className="space-y-6">
            {/* Training Metrics Section */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Training Metrics</h2>
              {/* Using key prop to force remount when refreshKey changes */}
              <TrainingMetrics key={refreshKey} />
            </div>

            {/* Create Category Section */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Category</h2>
              <ClassificationTraining onSuccess={handleCategoryCreated} />
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}


