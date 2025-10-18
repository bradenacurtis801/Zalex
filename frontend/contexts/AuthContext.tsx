'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi, setAuthToken } from '@/api'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  user_role: string
}

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (token) {
      // Verify token and get user info
      verifyToken()
    } else {
      setLoading(false)
    }
  }, [])

  const verifyToken = async () => {
    try {
      // Update API clients with current token
      setAuthToken(localStorage.getItem('auth_token'))
      
      const response = await authApi.getCurrentUserInfoApiAuthMeGet()
      // Map User to User interface
      setUser({
        id: response.id,
        username: response.username,
        email: response.email,
        full_name: response.fullName,
        user_role: response.userRole,
      })
    } catch (error) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
      }
      setAuthToken(null) // Update API clients to remove invalid token
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      
      const response = await authApi.loginApiAuthLoginPost({
        userLogin: {
          username,
          password,
        }
      })
      
      
      if (!response || !response.sessionToken) {
        throw new Error('Invalid login response - no session token received')
      }
      
      const { sessionToken } = response
      // Set token into API layer and localStorage atomically
      setAuthToken(sessionToken)
      
      // Get user info using the updated API client
      const userResponse = await authApi.getCurrentUserInfoApiAuthMeGet()
      
      if (!userResponse) {
        throw new Error('Failed to get user information')
      }
      
      // Map User to User interface
      setUser({
        id: userResponse.id,
        username: userResponse.username,
        email: userResponse.email,
        full_name: userResponse.fullName,
        user_role: userResponse.userRole,
      })
      
    } catch (error: any) {
      console.error('❌ Login error:', error)
      
      let errorMessage = 'Login failed'
      
      // Use HTTP status codes for simple, reliable error handling
      if (error.response) {
        switch (error.response.status) {
          case 401:
            errorMessage = 'Incorrect username or password'
            break
          case 403:
            errorMessage = 'Account is disabled'
            break
          case 429:
            errorMessage = 'Too many login attempts. Please try again later'
            break
          case 500:
            errorMessage = 'Server error. Please try again later'
            break
          default:
            errorMessage = 'Login failed. Please try again'
        }
      } else {
        errorMessage = error?.message || 'Login failed'
      }
      
      throw new Error(errorMessage)
    }
  }

  const logout = () => {
    setAuthToken(null) // clears localStorage and updates clients
    setUser(null)
  }

  const value = {
    user,
    login,
    logout,
    loading,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
