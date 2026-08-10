import { Languages } from "lucide-react";

import { languageNames, type Locale } from "../translations";
import { useLocale } from "../hooks/useLocale";


export function LanguageSelector({ onLocaleChange, compact = false }: { onLocaleChange?: (locale: Locale) => void; compact?: boolean }) {
  const { locale, setLocale, t } = useLocale();
  return <label className="relative flex items-center gap-2 text-xs text-slate-500">
    <Languages className="h-4 w-4" aria-hidden="true" />
    {!compact && <span className="sr-only">{t("common.language")}</span>}
    <select aria-label={t("common.language")} value={locale} onChange={(event) => { const value = event.target.value as Locale; setLocale(value); onLocaleChange?.(value); }}
      className="h-9 rounded-xl border border-white/8 bg-[#141428] px-2 text-xs text-slate-300 outline-none focus:border-violet-500/60">
      {(Object.keys(languageNames) as Locale[]).map((value) => <option key={value} value={value}>{languageNames[value]}</option>)}
    </select>
  </label>;
}
