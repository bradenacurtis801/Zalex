'use client'

import { useState, useEffect } from 'react'
import { categoryApi, uploadApi } from '@/api'
import { DocumentClassification, UserInfo, CategoryDocument, CategoryDocumentFromJSON } from '@/generated'
import { getCategoryColor, getCategoryLabel } from '@/utils/categoryUtils'
import { useLanguage } from '@/contexts/LanguageContext'

interface DocumentManagementProps {
  onClose: () => void
}

interface DocumentInfo {
  id: string
  filename: string
  category: string
  confidence: number
  fileSize: number
  mimeType: string
  createdAt: string
  user?: UserInfo
}

export default function DocumentManagement({ onClose }: DocumentManagementProps) {
  const { t } = useLanguage()
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [categories, setCategories] = useState<string[]>([])

  // Load documents and categories
  useEffect(() => {
    loadDocuments()
    loadCategories()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get all categories first
      const categoriesResponse = await categoryApi.getAllCategoriesApiCategoriesGet()
      const allDocuments: DocumentInfo[] = []
      
      // Extract documents from all categories
      if (categoriesResponse.categories) {
        for (const [categoryName, categoryData] of Object.entries(categoriesResponse.categories)) {
          if (categoryData && typeof categoryData === 'object') {
            for (const [docId, docData] of Object.entries(categoryData)) {
              if (docData && typeof docData === 'object' && 'filename' in docData) {
                // Convert the raw JSON data to proper CategoryDocument type
                const categoryDoc = CategoryDocumentFromJSON(docData)
                
                allDocuments.push({
                  id: docId,
                  filename: categoryDoc.filename || t('documentManagement.unknown'),
                  category: categoryName,
                  confidence: categoryDoc.confidence || 0,
                  fileSize: categoryDoc.fileSize || 0,
                  mimeType: categoryDoc.mimeType || 'unknown',
                  createdAt: categoryDoc.timestamp || new Date().toISOString(),
                  user: categoryDoc.user ? {
                    username: categoryDoc.user.username || t('documentManagement.unknown'),
                    fullName: categoryDoc.user.fullName || t('documentManagement.unknown')
                  } : undefined
                })
              }
            }
          }
        }
      }
      
      setDocuments(allDocuments)
    } catch (err) {
      console.error('Error loading documents:', err)
      setError(t('documentManagement.loadError'))
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await categoryApi.getAllCategoriesApiCategoriesGet()
      if (response.categories) {
        setCategories(Object.keys(response.categories))
      }
    } catch (err) {
      console.error('Error loading categories:', err)
    }
  }

  const handleDeleteDocument = async (documentId: string, filename: string) => {
    if (!confirm(t('documentManagement.confirmDelete', { filename }))) {
      return
    }

    try {
      setDeleting(documentId)
      setError(null)
      
      // Call the delete API using the generated client
      const result = await uploadApi.deleteDocumentApiDocumentsDocumentIdDelete({
        documentId: documentId
      })
      
      console.log('Delete result:', result)
      
      // Remove document from local state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId))
      
      // Show success message
      alert(t('documentManagement.deleteSuccess', { filename }))
      
    } catch (err) {
      console.error('Error deleting document:', err)
      setError(err instanceof Error ? err.message : t('documentManagement.deleteError'))
    } finally {
      setDeleting(null)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return `0 ${t('documentManagement.bytes')}`
    const k = 1024
    const sizes = [t('documentManagement.bytes'), t('documentManagement.kb'), t('documentManagement.mb'), t('documentManagement.gb')]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Filter documents based on search and category
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.category.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-violet-800 text-white p-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">{t('documentManagement.title')}</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-violet-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex flex-col h-full">
          {/* Fixed Header Section */}
          <div className="p-6 pb-4">
            {/* Filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder={t('documentManagement.searchPlaceholder')}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
              <div className="sm:w-48">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
                >
                  <option value="all">{t('documentManagement.allCategories')}</option>
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {getCategoryLabel(category)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            )}
          </div>

          {/* Scrollable Documents Table */}
          <div className="flex-1 overflow-hidden px-6 min-h-0">
            <div className="h-full overflow-y-auto">
              <div className="overflow-x-auto min-w-full">
            {loading ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div>
                <p className="mt-2 text-gray-600">{t('documentManagement.loading')}</p>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {searchTerm || selectedCategory !== 'all' 
                  ? t('documentManagement.noDocumentsMatch')
                  : t('documentManagement.noDocumentsFound')
                }
              </div>
            ) : (
              <table className="w-full border-collapse min-w-full">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-gray-50">
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.filename')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.category')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.confidence')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.size')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.uploaded')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.user')}</th>
                    <th className="text-left py-3 px-4 border-b font-medium text-gray-700">{t('documentManagement.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocuments.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 border-b">
                        <div className="font-medium text-gray-900 truncate max-w-xs" title={doc.filename}>
                          {doc.filename}
                        </div>
                        <div className="text-sm text-gray-500">{doc.mimeType}</div>
                      </td>
                      <td className="py-3 px-4 border-b">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full border ${getCategoryColor(doc.category)}`}
                        >
                          {getCategoryLabel(doc.category)}
                        </span>
                      </td>
                      <td className="py-3 px-4 border-b">
                        <span className="text-sm text-gray-600">
                          {(doc.confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 border-b text-sm text-gray-600">
                        {formatFileSize(doc.fileSize)}
                      </td>
                      <td className="py-3 px-4 border-b text-sm text-gray-600">
                        {formatDate(doc.createdAt)}
                      </td>
                      <td className="py-3 px-4 border-b text-sm text-gray-600">
                        {doc.user ? (
                          <div>
                            <div className="font-medium">{doc.user.username}</div>
                            <div className="text-xs text-gray-500">{doc.user.fullName}</div>
                          </div>
                        ) : (
                          <span className="text-gray-400">{t('documentManagement.unknown')}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 border-b">
                        <button
                          onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                          disabled={deleting === doc.id}
                          className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {deleting === doc.id ? (
                            <div className="flex items-center">
                              <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin mr-2"></div>
                              {t('documentManagement.deleting')}
                            </div>
                          ) : (
                            t('documentManagement.delete')
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
              </div>
            </div>
          </div>

          {/* Fixed Footer */}
          <div className="p-6 pt-4 border-t border-gray-200 bg-gray-50">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                {t('documentManagement.showing', { filtered: filteredDocuments.length, total: documents.length })}
              </div>
              <div className="flex gap-3">
                <button
                  onClick={loadDocuments}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  {t('documentManagement.refresh')}
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  {t('documentManagement.close')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
