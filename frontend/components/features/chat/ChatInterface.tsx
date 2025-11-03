'use client'

import { useState, useRef, useEffect } from 'react'
import { queryApi } from '@/api'
import { Button, Input } from '@/components/ui'
import { SearchResult } from '@/generated/models/SearchResult'
import SearchResultViewer from './SearchResultViewer'

interface Message {
  text: string
  sender: 'user' | 'bot'
  searchResults?: SearchResult[]
  query?: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hello! Ask me anything about your enrolled documents.", sender: 'bot' }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  

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
      const response = await queryApi.queryIndexApiQueryPost({ queryRequest: { query } })
      
      let botResponse = ''
      if (response && response.results && response.results.length > 0) {
        botResponse = `Found ${response.results.length} result${response.results.length !== 1 ? 's' : ''} for your query.`
        
        // Replace loading message with response that includes search results
        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = { 
            text: botResponse, 
            sender: 'bot',
            searchResults: response.results,
            query: query
          }
          return newMessages
        })
      } else {
        botResponse = "I couldn't find any relevant information in your documents for that query."
        
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
          text: `Sorry, an error occurred: ${error instanceof Error ? error.message : 'Search failed'}`, 
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
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask a question..."
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
