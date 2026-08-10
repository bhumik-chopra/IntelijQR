import { createContext, useCallback, useEffect, useMemo, useState, type PropsWithChildren } from "react";

import { translations, type Locale } from "../translations";


const STORAGE_KEY = "intelliqr_locale";
const supported = new Set<Locale>(["en", "hi", "gu"]);

export interface LocaleContextValue { locale: Locale; setLocale: (locale: Locale) => void; t: (key: string) => string; }
export const LocaleContext = createContext<LocaleContextValue | undefined>(undefined);

export function LocaleProvider({ children }: PropsWithChildren) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Locale | null;
    if (saved && supported.has(saved)) return saved;
    const browser = navigator.language.toLowerCase().split("-")[0] as Locale;
    return supported.has(browser) ? browser : "en";
  });
  const setLocale = useCallback((value: Locale) => { setLocaleState(value); localStorage.setItem(STORAGE_KEY, value); }, []);
  useEffect(() => { document.documentElement.lang = locale; }, [locale]);
  const value = useMemo(() => ({ locale, setLocale, t: (key: string) => translations[locale][key] ?? translations.en[key] ?? key }), [locale, setLocale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}
