import { callable } from "@decky/api";
import type { ActionResult, LaunchPlan, LaunchState } from "../model";

export const pingBackend = callable<[], Record<string, string>>("ping");
export const listGames = callable<[], string>("list_games");
export const getGame = callable<[appid: string], string>("get_game");
export const setOption = callable<[appid: string, settingId: string, optionId: string], ActionResult>("set_option");
export const restoreGame = callable<[appid: string], ActionResult>("restore_game");
export const planLaunchOption = callable<[appid: string, current: string, enable: boolean], LaunchPlan>(
  "plan_launch_option"
);
export const launchState = callable<[appid: string, current: string], LaunchState>("launch_state");
