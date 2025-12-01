import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enTranslations from '@/locales/en.json'
import esTranslations from '@/locales/es.json'

const resources = {
  en: {
    translation: enTranslations,
  },
  es: {
    translation: esTranslations,
  },
}

// Get language from localStorage or default to 'en'
const getInitialLanguage = (): string => {
  if (typeof window !== 'undefined') {
    const savedLanguage = localStorage.getItem('language')
    if (savedLanguage && (savedLanguage === 'en' || savedLanguage === 'es')) {
      return savedLanguage
    }
  }
  return 'en'
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    react: {
      useSuspense: false, // Disable suspense for Next.js compatibility
    },
  })

// Listen for language changes and save to localStorage
i18n.on('languageChanged', (lng) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('language', lng)
  }
})

export default i18n

