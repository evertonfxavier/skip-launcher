import type { GameSummary } from "../model";

/** The game to show: the remembered one while it is still in the list, else the first installed, else the first. */
export function pickGame(games: Pick<GameSummary, "appid" | "installed">[], remembered: string | null): string | null {
  if (!games.length) return null;
  if (remembered !== null && games.some((g) => g.appid === remembered)) return remembered;
  return (games.find((g) => g.installed) ?? games[0]).appid;
}
