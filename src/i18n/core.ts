// Pure translation core: no globals, no JSON imports, so `node --test` can load it (tests/ui).
export type Lang = "en" | "pt-BR";
export type Catalog = Record<string, string>;
export type Vars = Record<string, string | number>;

export const DEFAULT_LANG: Lang = "en";

/** Replaces {name} with vars.name; an unknown placeholder is left as written, never dropped. */
export function interpolate(text: string, vars?: Vars): string {
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (whole, name: string) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : whole
  );
}

/** The key in `lang`, else in English, else undefined. */
export function lookup(catalogs: Record<Lang, Catalog>, lang: Lang, key: string): string | undefined {
  return catalogs[lang]?.[key] ?? catalogs[DEFAULT_LANG]?.[key];
}

export function translate(catalogs: Record<Lang, Catalog>, lang: Lang, key: string, vars?: Vars): string {
  const text = lookup(catalogs, lang, key);
  return text === undefined ? key : interpolate(text, vars);
}

/** Like translate, but gives `fallback` (e.g. the backend's English text) when the key is unknown. */
export function translateOr(
  catalogs: Record<Lang, Catalog>,
  lang: Lang,
  key: string,
  fallback: string,
  vars?: Vars
): string {
  const text = lookup(catalogs, lang, key);
  return text === undefined ? fallback : interpolate(text, vars);
}
