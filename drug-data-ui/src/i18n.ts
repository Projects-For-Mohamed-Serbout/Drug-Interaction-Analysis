import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import i18n_en from './i18n/en.json';
import i18n_es from './i18n/es.json';

const resources = {
  en: {
    translation: i18n_en,
  },
  es: {
    translation: i18n_es,
  }
};

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupQuerystring: 'lng',
    }
  });

export default i18n;