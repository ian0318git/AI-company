import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { t, type Lang } from './translations'

interface I18nContextType {
  lang: Lang
  setLang: (lang: Lang) => void
  toggleLang: () => void
  tr: (key: string) => string
}

const I18nContext = createContext<I18nContextType | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    return (localStorage.getItem('ai-company-lang') as Lang) || 'en'
  })

  const updateLang = useCallback((newLang: Lang) => {
    localStorage.setItem('ai-company-lang', newLang)
    setLang(newLang)
  }, [])

  const toggleLang = useCallback(() => {
    updateLang(lang === 'en' ? 'zh-TW' : 'en')
  }, [lang, updateLang])

  const tr = useCallback((key: string): string => {
    return t[lang]?.[key] || t['en']?.[key] || key
  }, [lang])

  return (
    <I18nContext.Provider value={{ lang, setLang: updateLang, toggleLang, tr }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used within LanguageProvider')
  return ctx
}
