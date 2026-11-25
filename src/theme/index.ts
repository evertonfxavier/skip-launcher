export const MUTED = "#9aa3b2";

// Status dots (the only place a tone shows: no coloured borders or boxes). Never colour alone: "none" is a hollow ring and the panel has a legend.
export const DOT_COLOR = {
  full: "#4caf50",
  partial: "#f2c744",
  error: "#ff6b6b",
  ingame: "#4aa3ff", // blue: distinct from the green / yellow / red of the plugin's own states
  none: "#c4c9d2",
} as const;

// Spacing rhythm (px) for custom rows; PanelSectionRow already adds its own padding.
export const GAP = { tight: 4, row: 6, block: 8 } as const;
