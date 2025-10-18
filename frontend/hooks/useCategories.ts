import { useState, useEffect } from 'react'
import { categoryApi } from '@/api'
import { CategoriesResponse, CategoryResponse, DocumentEntry } from '@/generated'

export interface CategorySummary {
  category: string
  count: number
  lastUpdated?: string
}

export interface CategoryDocument {
  id: string
  filename: string
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
      
      // Ensure response.categories exists and is an object
      if (!response || typeof response.categories !== 'object') {
        console.warn('Invalid response structure:', response)
        setCategories([])
        return
      }
      
      // Convert the categories object to an array of CategorySummary
      // response.categories is now typed as Dict[str, Dict[str, Any]] (category_name -> {filename -> document_data})
      const categoriesArray: CategorySummary[] = Object.entries(response.categories).map(([categoryName, documents]) => {
        // documents is Dict[str, Any] where keys are filenames and values are document metadata
        const docsArray = Object.values(documents || {})
        
        const lastUpdated = docsArray.length > 0 
          ? docsArray.reduce((latest: any, doc: any) => {
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
      const documents: CategoryDocument[] = (response.documents || []).map((doc: DocumentEntry) => ({
        id: doc.id,
        filename: doc.filename,
        category: doc.category,
        confidence: doc.confidence,
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
