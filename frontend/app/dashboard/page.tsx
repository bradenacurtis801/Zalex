'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import Header from '@/components/layout/Header'
import { categoryApi, queryApi } from '@/api'
import { DocumentClassification } from '@/generated'
import TaskStats from '@/components/features/tasks/TaskStats'

interface DashboardStats {
  totalDocuments: number
  totalCategories: number
  recentUploads: DocumentClassification[]
  categoryCounts: Record<string, number>
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    totalCategories: 0,
    recentUploads: [],
    categoryCounts: {}
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Use the summary endpoint for better performance
      const summaryResponse = await categoryApi.getCategoriesSummaryApiCategoriesSummaryGet()
      
      // summaryResponse is a Dict[str, int] - category name to count
      const categoryCounts = summaryResponse || {}
      const totalDocuments = Object.values(categoryCounts).reduce((sum, count) => sum + count, 0)
      const totalCategories = Object.keys(categoryCounts).length

      setStats({
        totalDocuments,
        totalCategories,
        recentUploads: [], // TODO: Implement recent uploads tracking
        categoryCounts
      })
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center h-screen">
          <div className="text-lg">Loading dashboard...</div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        <Header title="Dashboard" />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto p-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Documents</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalDocuments}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Categories</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalCategories}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Processing Speed</p>
                  <p className="text-2xl font-bold text-gray-900">Fast</p>
                </div>
              </div>
            </div>
          </div>

          {/* Task Stats Section */}
          <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
            <TaskStats />
          </div>

          {/* Category Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Distribution by Category</h3>
              <div className="space-y-3">
                {Object.entries(stats.categoryCounts).map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{category}</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                        <div 
                          className="bg-violet-600 h-2 rounded-full" 
                          style={{ width: `${(count / stats.totalDocuments) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <a 
                  href="/upload" 
                  className="block w-full bg-violet-600 text-white text-center py-2 px-4 rounded-lg hover:bg-violet-700 transition-colors"
                >
                  Upload Documents
                </a>
                <a 
                  href="/categories" 
                  className="block w-full bg-gray-600 text-white text-center py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Manage Categories
                </a>
                <a 
                  href="/search" 
                  className="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Search Documents
                </a>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
