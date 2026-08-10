import { describe, expect, it } from "vitest";

import { languageNames, translations } from "../src/features/i18n/translations";


describe("local translations", () => {
  it("keeps Hindi and Gujarati dictionaries complete against English", () => {
    const englishKeys = Object.keys(translations.en).sort();
    expect(Object.keys(translations.hi).sort()).toEqual(englishKeys);
    expect(Object.keys(translations.gu).sort()).toEqual(englishKeys);
    expect(Object.values(translations.hi).every(Boolean)).toBe(true);
    expect(Object.values(translations.gu).every(Boolean)).toBe(true);
  });

  it("provides native language labels and Unicode generator guidance", () => {
    expect(languageNames.hi).toBe("हिन्दी");
    expect(languageNames.gu).toBe("ગુજરાતી");
    expect(translations.gu["generator.textPlaceholder"]).toContain("ભાષા");
  });
});
