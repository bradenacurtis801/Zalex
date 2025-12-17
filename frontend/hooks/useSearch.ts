import { useState } from 'react'
import { queryApi } from '@/api'
import { SearchResult, QueryFilters } from '@/generated'

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Accept optional typed filters (generated models expect QueryFilters shape)
  const search = async (query: string, filters?: QueryFilters): Promise<SearchResult[]> => {
    if (!query.trim()) {
      setResults([])
      return []
    }

    setIsSearching(true)
    setError(null)

    try {
  const queryRequest: any = { query }
  if (filters !== undefined) queryRequest.filters = filters
  const searchResults = await queryApi.queryIndexApiQueryPost({ queryRequest })
      setResults(searchResults.results)
      return searchResults.results
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed'
      setError(errorMessage)
      throw err
    } finally {
      setIsSearching(false)
    }
  }

  const clearResults = () => {
    setResults([])
    setError(null)
  }

  return {
    results,
    isSearching,
    error,
    search,
    clearResults
  }
}
