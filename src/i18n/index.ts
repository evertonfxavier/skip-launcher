import en from "./en.json";
import ptBR from "./pt-BR.json";
import { DEFAULT_LANG, translate, translateOr } from "./core";
import type { Catalog, Lang, Vars } from "./core";

export type { Lang, Vars } from "./core";
export type TKey = keyof typeof en;

const CATALOGS: Record<Lang, Catalog> = { en, "pt-BR": ptBR };

// One language per panel mount (resolved by detectLanguage, see ./detect); English until then.
let current: Lang = DEFAULT_LANG;

export const getLanguage = (): Lang => current;
export const setLanguage = (lang: Lang): void => {
  current = lang;
};

/** Typed keys: a typo is a compile error. Missing in the active language falls back to English. */
export const t = (key: TKey, vars?: Vars): string => translate(CATALOGS, current, key, vars);

/** For keys built at run time (`setting.<id>`, `code.<code>`): `fallback` when the key does not exist. */
export const tOr = (key: string, fallback: string, vars?: Vars): string =>
  translateOr(CATALOGS, current, key, fallback, vars);
