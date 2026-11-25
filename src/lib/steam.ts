// Steam's own launch-options value, read and written through the Steam client (the backend cannot: Steam keeps it
// in memory and rewrites its files on exit).
const READ_TIMEOUT_MS = 6000;

/** The game's launch options, or null when Steam does not answer in time. */
export function readLaunchOptions(appid: string): Promise<string | null> {
  return new Promise((resolve) => {
    let done = false;
    let handle: { unregister?: () => void } | undefined;
    const finish = (value: string | null) => {
      if (done) return;
      done = true;
      try {
        handle?.unregister?.();
      } catch {
        /* already gone */
      }
      resolve(value);
    };
    const timer = setTimeout(() => finish(null), READ_TIMEOUT_MS);
    try {
      handle = SteamClient.Apps.RegisterForAppDetails(Number(appid), (details) => {
        clearTimeout(timer);
        finish(typeof details?.strLaunchOptions === "string" ? details.strLaunchOptions : "");
      });
    } catch {
      clearTimeout(timer);
      finish(null);
    }
  });
}

export function writeLaunchOptions(appid: string, value: string): void {
  SteamClient.Apps.SetAppLaunchOptions(Number(appid), value);
}
