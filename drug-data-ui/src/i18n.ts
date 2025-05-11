import i18n from 'i18next'
import Cache from 'i18next-localstorage-backend'
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
  },
};

const detectionOptions = {
  order: ['localStorage', 'navigator'],
  caches: ['localStorage'],
  lookupQuerystring: 'lng',
};

void i18n
  .use(Cache) // Only uses localStorage
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    detection: detectionOptions,
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
