/**
 * Phase 10 — i18n configuration
 * react-i18next with browser language detector and localStorage persistence.
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import en from './locales/en.json'
import hi from './locales/hi.json'
import te from './locales/te.json'

const SUPPORTED = ['en', 'hi', 'te']
const DEFAULT   = 'en'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      te: { translation: te },
    },
    fallbackLng:  DEFAULT,
    supportedLngs: SUPPORTED,
    interpolation: { escapeValue: false },
    detection: {
      order:  ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'ruralbiz_language',
    },
    react: { useSuspense: false },
  })

export default i18n
export { SUPPORTED, DEFAULT }
