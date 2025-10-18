import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import { AuthProvider } from '@/contexts/AuthContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ScanPro AI Document Agent',
  description: 'A self-contained application for document ingestion, OCR, indexing, and retrieval.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
