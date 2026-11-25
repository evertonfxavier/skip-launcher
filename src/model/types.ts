// Must match what the backend returns (main.py, engine.py).
export interface Status {
  state: "ok" | "pending" | "running" | "error";
  code: string;
  message: string;
}

export interface GameSummary {
  appid: string;
  name: string;
  support: string;
  installed: boolean;
  launcher_exe: string;
  game_exe: string;
  status: Status;
}

export interface OptionView {
  id: string;
  label: string;
  label_key: string;
}

export interface SettingView {
  id: string;
  kind: "toggle" | "choice";
  label: string;
  label_key: string;
  group: string;
  note_key: string | null;
  options: OptionView[];
  current: string | null; // option id, null = custom
}

export interface GameDetail {
  appid: string;
  name: string;
  launcher_exe: string;
  game_exe: string;
  status: Status;
  settings: SettingView[];
  changed: boolean;
}

export interface ActionResult {
  ok: boolean;
  changed: boolean;
  status: Status;
}

export interface LaunchPlan {
  ok: boolean;
  options: string;
  enabled: boolean;
}

export interface LaunchState {
  ok: boolean;
  enabled: boolean;
}
