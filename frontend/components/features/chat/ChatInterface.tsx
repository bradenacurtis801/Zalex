'use client'

import { useState, useRef, useEffect } from 'react'
import { useSearch } from '@/hooks/useSearch'
import { Button, Input } from '@/components/ui'
import { SearchResult } from '@/generated/models/SearchResult'
import { QueryFilters } from '@/generated'
import SearchResultViewer from './SearchResultViewer'
import { useLanguage } from '@/contexts/LanguageContext'

interface Message {
  text: string
  sender: 'user' | 'bot'
  searchResults?: SearchResult[]
  query?: string
}

export default function ChatInterface() {
  const { t } = useLanguage()
  const [messages, setMessages] = useState<Message[]>([
    { text: t('chat.welcomeMessage'), sender: 'bot' }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [dateFrom, setDateFrom] = useState<string | null>(null)
  const [dateTo, setDateTo] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { search } = useSearch()
  

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const query = inputValue.trim()
    setInputValue('')
    
    // Add user message
    setMessages(prev => [...prev, { text: query, sender: 'user' }])
    
    // Add loading message
    setMessages(prev => [...prev, { text: '', sender: 'bot' }])
    setIsLoading(true)

    try {
      // Build typed filters only when the user provided values
      let filters: QueryFilters | undefined = undefined
      if (dateFrom || dateTo || categoryFilter) {
        filters = {}
        if (dateFrom) filters.dateFrom = new Date(dateFrom)
        if (dateTo) filters.dateTo = new Date(dateTo)
        if (categoryFilter) filters.category = categoryFilter
      }

      const results = await search(query, filters)

      let botResponse = ''
      if (results && results.length > 0) {
        // Sort results by score (ascending - lower distance = better match)
        // Results with null/undefined scores go to the end
        const sortedResults = [...results].sort((a, b) => {
          if (a.score == null && b.score == null) return 0
          if (a.score == null) return 1
          if (b.score == null) return -1
          return a.score - b.score
        })

        botResponse = t('chat.foundResults', { count: sortedResults.length })

        // Replace loading message with response that includes search results
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            text: botResponse,
            sender: 'bot',
            searchResults: sortedResults,
            query: query,
          }
          return newMessages
        })
      } else {
        botResponse = t('chat.noResults')

        // Replace loading message with no results message
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = { text: botResponse, sender: 'bot' }
          return newMessages
        })
      }
    } catch (error) {
      // Replace loading message with error
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = { 
          text: t('chat.errorOccurred', { error: error instanceof Error ? error.message : t('chat.searchFailed') }), 
          sender: 'bot' 
        }
        return newMessages
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-grow bg-gray-50 p-4 rounded-lg overflow-y-auto mb-4 border">
        {messages.map((message, index) => (
          <div key={index} className={`flex mb-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {message.sender === 'user' ? (
              <div className={`rounded-lg p-3 max-w-lg ${message.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}`}>
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
              </div>
            ) : (
              <div className="rounded-lg p-3 max-w-4xl w-full chat-bubble-bot">
                {message.text ? (
                  <p className="text-sm whitespace-pre-wrap mb-3">{message.text}</p>
                ) : (
                  <div className="loader"></div>
                )}
                {message.searchResults && message.query && (
                  <div className="mt-3">
                    <SearchResultViewer 
                      results={message.searchResults} 
                      query={message.query}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <div className="flex gap-2 items-center">
          <input
            aria-label={t('chat.filter.dateFrom')}
            type="date"
            value={dateFrom ?? ''}
            onChange={(e) => setDateFrom(e.target.value || null)}
            className="border rounded px-2 py-1"
          />
          <input
            aria-label={t('chat.filter.dateTo')}
            type="date"
            value={dateTo ?? ''}
            onChange={(e) => setDateTo(e.target.value || null)}
            className="border rounded px-2 py-1"
          />
          <input
            aria-label={t('chat.filter.categoryPlaceholder')}
            type="text"
            placeholder={t('chat.filter.categoryPlaceholder')}
            value={categoryFilter ?? ''}
            onChange={(e) => setCategoryFilter(e.target.value || null)}
            className="border rounded px-2 py-1"
          />
        </div>

        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={t('chat.askPlaceholder')}
          disabled={isLoading}
          className="flex-grow"
        />
        <Button
          type="submit"
          disabled={isLoading || !inputValue.trim()}
          size="md"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
        </Button>
      </form>
    </div>
  )
}
