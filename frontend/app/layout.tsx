import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import { AuthProvider } from '@/contexts/AuthContext'
import { APP_TITLE, APP_DESCRIPTION } from '@/utils/constants'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: APP_TITLE,
  description: APP_DESCRIPTION,
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
