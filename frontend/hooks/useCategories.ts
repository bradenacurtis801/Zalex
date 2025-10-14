import { useState, useEffect } from 'react'
import { categoryApi } from '@/api'
import { CategoriesResponse, CategoryResponse } from '@/generated'

export interface CategorySummary {
  category: string
  count: number
  lastUpdated?: string
}

export interface CategoryDocument {
  filename: string
  filePath: string
  category: string
  confidence: number
  timestamp: string
}

export function useCategories() {
  const [categories, setCategories] = useState<CategorySummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCategories = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await categoryApi.getAllCategoriesApiCategoriesGet()
      console.log('API Response:', response)
      
      // Ensure response.categories exists and is an object
      if (!response || typeof response.categories !== 'object') {
        console.warn('Invalid response structure:', response)
        setCategories([])
        return
      }
      
      // Convert the categories object to an array of CategorySummary
      const categoriesArray: CategorySummary[] = Object.entries(response.categories).map(([categoryName, documents]) => {
        const docsArray = Array.isArray(documents) ? documents : []
        const lastUpdated = docsArray.length > 0 
          ? docsArray.reduce((latest, doc) => {
              const docTime = new Date(doc.timestamp || 0).getTime()
              const latestTime = new Date(latest.timestamp || 0).getTime()
              return docTime > latestTime ? doc : latest
            }, docsArray[0])?.timestamp
          : undefined

        return {
          category: categoryName,
          count: docsArray.length,
          lastUpdated
        }
      })

      console.log('Processed categories:', categoriesArray)
      setCategories(categoriesArray)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch categories')
      console.error('Error fetching categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCategorySummary = async () => {
    try {
      const response = await categoryApi.getCategoriesSummaryApiCategoriesSummaryGet()
      return response
    } catch (err) {
      console.error('Error fetching category summary:', err)
      throw err
    }
  }

  const fetchDocumentsByCategory = async (category: string) => {
    try {
      const response = await categoryApi.getDocumentsByCategoryApiCategoriesCategoryGet({ category })
      // Convert the response to match our CategoryDocument interface
      const documents: CategoryDocument[] = (response.documents || []).map((doc: any) => ({
        filename: doc.filename || '',
        filePath: doc.filePath || doc.file_path || '',
        category: doc.category || category,
        confidence: doc.confidence || 0,
        timestamp: doc.timestamp || ''
      }))
      return { ...response, documents }
    } catch (err) {
      console.error(`Error fetching documents for category ${category}:`, err)
      throw err
    }
  }

  useEffect(() => {
    fetchCategories()
  }, [])

  return {
    categories,
    loading,
    error,
    fetchCategories,
    fetchCategorySummary,
    fetchDocumentsByCategory,
    refetch: fetchCategories
  }
}
