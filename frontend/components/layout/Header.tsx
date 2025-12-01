'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useLanguage } from '@/contexts/LanguageContext'
import UserProfile from '@/components/features/user/UserProfile'
import UserManagement from '@/components/features/user/UserManagement'
import DocumentManagement from '@/components/features/document/DocumentManagement'
import LanguageSwitcher from '@/components/ui/LanguageSwitcher'

interface HeaderProps {
  title: string
  showBackButton?: boolean
  onBackClick?: () => void
}

export default function Header({ title, showBackButton = false, onBackClick }: HeaderProps) {
  const { user, logout } = useAuth()
  const router = useRouter()
  const { t } = useLanguage()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showUserProfile, setShowUserProfile] = useState(false)
  const [showUserManagement, setShowUserManagement] = useState(false)
  const [showDocumentManagement, setShowDocumentManagement] = useState(false)

  return (
    <>
      <header className="bg-violet-800 text-white shadow-md p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center">
            {showBackButton && (
              <button
                onClick={onBackClick}
                className="mr-4 p-1 hover:bg-violet-700 rounded"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>
            )}
            <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <h1 className="text-2xl font-bold">{title}</h1>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <a href="/dashboard" className="hover:text-violet-200 transition-colors">
              {t('navigation.dashboard')}
            </a>
            <a href="/upload" className="hover:text-violet-200 transition-colors">
              {t('navigation.upload')}
            </a>
            <a href="/categories" className="hover:text-violet-200 transition-colors">
              {t('navigation.categories')}
            </a>
            <a href="/search" className="hover:text-violet-200 transition-colors">
              {t('navigation.search')}
            </a>
          </nav>

          {/* Language Switcher */}
          <div className="hidden md:block mr-4">
            <LanguageSwitcher />
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 hover:bg-violet-700 px-3 py-2 rounded"
            >
              <div className="w-8 h-8 bg-violet-600 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium">
                  {user?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-sm">{user?.username}</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                <button
                  onClick={() => {
                    setShowUserProfile(true)
                    setShowUserMenu(false)
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  {t('user.profile')}
                </button>
                {user?.user_role === 'admin' && (
                  <>
                    <button
                      onClick={() => {
                        setShowUserManagement(true)
                        setShowUserMenu(false)
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      {t('user.manageUsers')}
                    </button>
                    <button
                      onClick={() => {
                        setShowDocumentManagement(true)
                        setShowUserMenu(false)
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      {t('user.manageDocuments')}
                    </button>
                    <button
                      onClick={() => {
                        router.push('/training')
                        setShowUserMenu(false)
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      {t('user.classificationTraining')}
                    </button>
                  </>
                )}
                <button
                  onClick={() => {
                    logout()
                    setShowUserMenu(false)
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  {t('auth.logout')}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      <div className="md:hidden bg-violet-700 px-4 py-2">
        <div className="flex space-x-4 items-center">
          <a href="/dashboard" className="text-white hover:text-violet-200 text-sm">{t('navigation.dashboard')}</a>
          <a href="/upload" className="text-white hover:text-violet-200 text-sm">{t('navigation.upload')}</a>
          <a href="/categories" className="text-white hover:text-violet-200 text-sm">{t('navigation.categories')}</a>
          <a href="/search" className="text-white hover:text-violet-200 text-sm">{t('navigation.search')}</a>
          <div className="ml-auto">
            <LanguageSwitcher />
          </div>
        </div>
      </div>

      {/* Modals */}
      {showUserProfile && (
        <UserProfile onClose={() => setShowUserProfile(false)} />
      )}
      {showUserManagement && (
        <UserManagement onClose={() => setShowUserManagement(false)} />
      )}
      {showDocumentManagement && (
        <DocumentManagement onClose={() => setShowDocumentManagement(false)} />
      )}
    </>
  )
}