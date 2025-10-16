interface StatusMessageProps {
  message: string
  type: 'success' | 'error' | 'warning'
  className?: string
}

export default function StatusMessage({ message, type, className = '' }: StatusMessageProps) {
  const getStatusStyles = () => {
    switch (type) {
      case 'error':
        return 'bg-red-100 text-red-800 border border-red-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
      case 'success':
      default:
        return 'bg-green-100 text-green-800 border border-green-200'
    }
  }

  return (
    <div className={`p-2 rounded-md text-sm ${getStatusStyles()} ${className}`}>
      <div className="max-h-32 overflow-y-auto break-words">
        {message}
      </div>
    </div>
  )
}
