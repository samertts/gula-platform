import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { Language, translations, Translation } from '../translations';
import { getDir } from '../lib/utils';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translation;
  dir: 'rtl' | 'ltr';
  isRtl: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('EN');

  useEffect(() => {
    document.documentElement.lang = language.toLowerCase();
    document.documentElement.dir = getDir(language);
  }, [language]);

  const value = {
    language,
    setLanguage,
    t: translations[language],
    dir: getDir(language),
    isRtl: getDir(language) === 'rtl'
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
