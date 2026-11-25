import { pickLanguage } from "../lib/lang";
import type { Lang } from "./core";

// Steam's globals are only partly typed and may be missing while the UI loads: every read is guarded.
const guard = <T,>(read: () => T): T | undefined => {
  try {
    return read();
  } catch {
    return undefined;
  }
};

const steamLocale = () => guard(() => LocalizationManager?.m_rgLocalesToUse?.[0]);
const browserLocale = () => guard(() => navigator?.language);

/** Instant guess for the first render: Steam's locale list, then the browser's. */
export function detectLanguageNow(): Lang {
  return pickLanguage([steamLocale(), browserLocale()]);
}

/** Steam's locale list, then Steam's language setting (async), then the browser's. */
export async function detectLanguage(): Promise<Lang> {
  const locale = steamLocale();
  if (locale) return pickLanguage([locale]);
  const setting = await guard(() => SteamClient?.Settings?.GetCurrentLanguage?.());
  return pickLanguage([setting, browserLocale()]);
}
