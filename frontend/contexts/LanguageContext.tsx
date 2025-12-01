'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import '@/lib/i18n' // Initialize i18n

type Language = 'en' | 'es'

interface LanguageContextType {
  language: Language
  changeLanguage: (lang: Language) => void
  t: (key: string, options?: any) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const { i18n, t } = useTranslation()
  const [language, setLanguage] = useState<Language>(() => {
    // Initialize language from i18n (which already loaded from localStorage)
    return (i18n.language as Language) || 'en'
  })

  useEffect(() => {
    // Sync state with i18n language changes
    const updateLanguage = (lng: string) => {
      if (lng === 'en' || lng === 'es') {
        setLanguage(lng)
      }
    }
    
    // Set initial language if different
    const savedLanguage = typeof window !== 'undefined' 
      ? (localStorage.getItem('language') as Language) || 'en'
      : 'en'
    
    if (i18n.language !== savedLanguage) {
      i18n.changeLanguage(savedLanguage).then(() => {
        updateLanguage(savedLanguage)
      })
    } else {
      updateLanguage(i18n.language)
    }

    // Listen for language changes
    i18n.on('languageChanged', updateLanguage)
    
    return () => {
      i18n.off('languageChanged', updateLanguage)
    }
  }, [i18n])

  const changeLanguage = (lang: Language) => {
    i18n.changeLanguage(lang).then(() => {
      setLanguage(lang)
      if (typeof window !== 'undefined') {
        localStorage.setItem('language', lang)
      }
    })
  }

  const contextValue: LanguageContextType = {
    language,
    changeLanguage,
    t,
  }

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

