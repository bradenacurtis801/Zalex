'use client'

import { useLanguage } from '@/contexts/LanguageContext'

export default function LanguageSwitcher() {
  const { language, changeLanguage, t } = useLanguage()

  return (
    <div className="relative">
      <select
        value={language}
        onChange={(e) => changeLanguage(e.target.value as 'en' | 'es')}
        className="bg-violet-700 text-white border-none rounded px-3 py-1 text-sm cursor-pointer hover:bg-violet-600 focus:outline-none focus:ring-2 focus:ring-violet-400"
        aria-label={t('language.selectLanguage')}
      >
        <option value="en">{t('language.english')}</option>
        <option value="es">{t('language.spanish')}</option>
      </select>
    </div>
  )
}

