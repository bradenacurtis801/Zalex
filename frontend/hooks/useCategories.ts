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
  // Category summary state (list of categories with counts)
  const [categorySummary, setCategorySummary] = useState<CategorySummary[]>([])
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // Category documents state (documents for a selected category)
  const [categoryDocuments, setCategoryDocuments] = useState<CategoryDocument[]>([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [documentsError, setDocumentsError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const fetchCategories = async (skip: number = 0, limit: number = 100) => {
    setSummaryLoading(true)
    setSummaryError(null)
    try {
      const response = await categoryApi.getAllCategoriesApiCategoriesGet({ skip, limit })
      
      // Ensure response.categories exists and is an object
      if (!response || typeof response.categories !== 'object') {
        console.warn('Invalid response structure:', response)
        setCategorySummary([])
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

      setCategorySummary(categoriesArray)
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : 'Failed to fetch categories')
      console.error('Error fetching categories:', err)
    } finally {
      setSummaryLoading(false)
    }
  }

  const fetchCategorySummary = async () => {
    setSummaryLoading(true)
    setSummaryError(null)
    try {
      const response = await categoryApi.getCategoriesSummaryApiCategoriesSummaryGet()
      
      // Response is Dict[str, int] - category name -> count
      // Convert to CategorySummary[] format
      const categoriesArray: CategorySummary[] = Object.entries(response).map(([categoryName, count]) => ({
        category: categoryName,
        count: count as number,
        // Summary endpoint doesn't provide lastUpdated, so we omit it
        lastUpdated: undefined
      }))

      setCategorySummary(categoriesArray)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch category summary'
      setSummaryError(errorMessage)
      console.error('Error fetching category summary:', err)
      throw err
    } finally {
      setSummaryLoading(false)
    }
  }

  const fetchDocumentsByCategory = async (category: string, skip: number = 0, limit: number = 100) => {
    setDocumentsLoading(true)
    setDocumentsError(null)
    setSelectedCategory(category)
    try {
      const response = await categoryApi.getDocumentsByCategoryApiCategoriesCategoryGet({ 
        category, 
        skip, 
        limit 
      })
      // Convert the response to match our CategoryDocument interface
      const documents: CategoryDocument[] = (response.documents || []).map((doc: DocumentEntry) => ({
        id: doc.id,
        filename: doc.filename,
        category: doc.category,
        confidence: doc.confidence,
        timestamp: doc.timestamp || ''
      }))
      setCategoryDocuments(documents)
      return { ...response, documents }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `Failed to fetch documents for category ${category}`
      setDocumentsError(errorMessage)
      console.error(`Error fetching documents for category ${category}:`, err)
      throw err
    } finally {
      setDocumentsLoading(false)
    }
  }

  const clearSelectedCategory = () => {
    setSelectedCategory(null)
    setCategoryDocuments([])
    setDocumentsError(null)
  }

  useEffect(() => {
    // Use summary endpoint for initial load (more efficient - only gets counts)
    fetchCategorySummary()
  }, [])

  return {
    // Category summary (for list view)
    categorySummary,
    summaryLoading,
    summaryError,
    
    // Category documents (for detail view)
    categoryDocuments,
    documentsLoading,
    documentsError,
    selectedCategory,
    
    // Functions
    fetchCategories,
    fetchCategorySummary,
    fetchDocumentsByCategory,
    clearSelectedCategory,
    
    // Legacy aliases for backward compatibility
    categories: categorySummary,
    loading: summaryLoading,
    error: summaryError,
    refetch: fetchCategorySummary
  }
}
