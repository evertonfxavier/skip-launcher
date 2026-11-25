import { useCallback, useEffect, useRef, useState } from "react";
import { getGame, launchState, listGames, planLaunchOption, restoreGame, setOption } from "../api";
import { pickGame, readLaunchOptions, writeLaunchOptions } from "../lib";
import type { ActionResult, GameDetail, GameSummary } from "../model";

// The list survives closing and reopening the panel (it renders at once, then refreshes).
let cachedGames: GameSummary[] | null = null;
// The chosen game outlives the panel: Steam remounts it when it re-renders (reading another game's details does that),
// and a choice kept only in component state would snap back to the first game each time.
let lastSelected: string | null = null;

export type Notice = { kind: "saved" | "restored" | "skip-failed" | "skip-unavailable" } | { kind: "status"; result: ActionResult };

export function useSkipLauncher() {
  const [games, setGames] = useState<GameSummary[]>(cachedGames ?? []);
  const [loaded, setLoaded] = useState(cachedGames !== null);
  const [selected, setSelected] = useState<string | null>(lastSelected);
  const [detail, setDetail] = useState<GameDetail | null>(null);
  const [skip, setSkip] = useState<boolean | null>(null); // null = not known (yet)
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const seq = useRef(0); // ignores answers that belong to a game the user already left

  const refreshList = useCallback(async () => {
    try {
      const reply = JSON.parse(await listGames());
      cachedGames = reply.games ?? [];
      setGames(cachedGames ?? []);
    } catch {
      /* keep what we have */
    }
    setLoaded(true);
  }, []);

  const refreshGame = useCallback(async (appid: string) => {
    const mine = ++seq.current;
    try {
      const reply = JSON.parse(await getGame(appid));
      if (mine === seq.current) setDetail(reply.game ?? null);
    } catch {
      if (mine === seq.current) setDetail(null);
    }
    const options = await readLaunchOptions(appid);
    if (mine !== seq.current) return;
    if (options === null) {
      setSkip(null);
      return;
    }
    const state = await launchState(appid, options);
    if (mine === seq.current) setSkip(state.ok ? state.enabled : null);
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  useEffect(() => {
    const pick = pickGame(games, selected);
    if (pick !== null && pick !== selected) {
      lastSelected = pick;
      setSelected(pick);
    }
  }, [games, selected]);

  useEffect(() => {
    if (selected) {
      setDetail(null);
      setSkip(null);
      void refreshGame(selected);
    }
  }, [selected, refreshGame]);

  const selectGame = useCallback((appid: string) => {
    setNotice(null);
    lastSelected = appid;
    setSelected(appid);
  }, []);

  const toggleSkip = useCallback(
    async (enable: boolean) => {
      if (!selected || busy) return;
      setBusy(true);
      setNotice(null);
      try {
        const current = await readLaunchOptions(selected);
        if (current === null) {
          setNotice({ kind: "skip-unavailable" });
          return;
        }
        const plan = await planLaunchOption(selected, current, enable);
        if (!plan.ok) {
          setNotice({ kind: "skip-failed" });
          return;
        }
        writeLaunchOptions(selected, plan.options);
        const after = await readLaunchOptions(selected); // Steam must have kept it
        const state = after === null ? null : await launchState(selected, after);
        if (state && state.ok && state.enabled === enable) setSkip(enable);
        else setNotice({ kind: "skip-failed" });
      } finally {
        setBusy(false);
      }
    },
    [selected, busy]
  );

  const change = useCallback(
    async (settingId: string, optionId: string) => {
      if (!selected || busy) return;
      setBusy(true);
      try {
        const result = await setOption(selected, settingId, optionId);
        setNotice(result.ok ? { kind: "saved" } : { kind: "status", result });
        await refreshGame(selected);
      } finally {
        setBusy(false);
      }
    },
    [selected, busy, refreshGame]
  );

  const restore = useCallback(async () => {
    if (!selected || busy) return;
    setBusy(true);
    try {
      const result = await restoreGame(selected);
      setNotice(result.ok ? { kind: "restored" } : { kind: "status", result });
      await refreshGame(selected);
    } finally {
      setBusy(false);
    }
  }, [selected, busy, refreshGame]);

  const summary = games.find((g) => g.appid === selected) ?? null;
  return { games, loaded, selected, summary, detail, skip, busy, notice, selectGame, toggleSkip, change, restore };
}

export type SkipLauncherModel = ReturnType<typeof useSkipLauncher>;
