interface MessageBubbleProps {
  text: string
  sender: 'user' | 'bot'
  isLoading?: boolean
}

export default function MessageBubble({ text, sender, isLoading = false }: MessageBubbleProps) {
  return (
    <div className={`flex mb-4 ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`rounded-lg p-3 max-w-lg ${sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'}`}>
        {isLoading ? (
          <div className="loader"></div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{text}</p>
        )}
      </div>
    </div>
  )
}
