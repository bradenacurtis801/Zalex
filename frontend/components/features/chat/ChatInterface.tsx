'use client'

import { useState, useRef, useEffect } from 'react'
import { queryApi } from '@/api'
import { Button, Input } from '@/components/ui'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Array<{ text: string; sender: 'user' | 'bot' }>>([
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
      const results = await queryApi.queryIndexApiQueryPost({ queryRequest: { query } })
      
      let botResponse = ''
      if (results && results.results && results.results.length > 0) {
        botResponse = 'Here are the most relevant results from your documents:\n\n'
        // Limit to first 10 results for readability
        const displayResults = results.results.slice(0, 10)
        displayResults.forEach((result: any, index: number) => {
          botResponse += `${index + 1}. "${result.text}"\n   Source: ${result.source} (Page ${result.page})\n\n`
        })
        if (results.results.length > 10) {
          botResponse += `... and ${results.results.length - 10} more results.\n`
        }
      } else {
        botResponse = "I couldn't find any relevant information in your documents for that query."
      }

      // Replace loading message with actual response
      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = { text: botResponse, sender: 'bot' }
        return newMessages
      })
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
            <div className={`rounded-lg p-3 max-w-lg ${message.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}`}>
              {message.text ? (
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
              ) : (
                <div className="loader"></div>
              )}
            </div>
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
