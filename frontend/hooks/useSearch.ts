import { useState } from 'react'
import { queryApi } from '@/api'
import { SearchResult } from '@/generated'

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async (query: string): Promise<SearchResult[]> => {
    if (!query.trim()) {
      setResults([])
      return []
    }

    setIsSearching(true)
    setError(null)

    try {
      const searchResults = await queryApi.queryIndexApiQueryPost({ queryRequest: { query } })
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
