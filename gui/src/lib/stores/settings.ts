import { writable } from "svelte/store";

export type FontFamily = "mono" | "sans" | "serif";
export type AccentColor = "blue" | "purple" | "green" | "orange" | "pink" | "teal";
export type CursorStyle = "line" | "block" | "underline" | "line-thin" | "block-outline";
export type LineHighlight = "none" | "gutter" | "line" | "all";

export interface AppSettings {
  // Appearance
  fontFamily: FontFamily;
  uiFontSize: number;
  accentColor: AccentColor;
  // Editor
  editorFontSize: number;
  editorTabSize: number;
  editorMinimap: boolean;
  showLineNumbers: boolean;
  wordWrap: boolean;
  bracketPairColorization: boolean;
  smoothScrolling: boolean;
  cursorStyle: CursorStyle;
  lineHighlight: LineHighlight;
  autoSaveDelay: number;
  // Pipeline
  autoCompileOnSave: boolean;
}

export const DEFAULTS: AppSettings = {
  fontFamily: "mono",
  uiFontSize: 16,
  accentColor: "blue",
  editorFontSize: 13,
  editorTabSize: 2,
  editorMinimap: true,
  showLineNumbers: true,
  wordWrap: true,
  bracketPairColorization: true,
  smoothScrolling: true,
  cursorStyle: "line",
  lineHighlight: "gutter",
  autoSaveDelay: 1000,
  autoCompileOnSave: false,
};

export const ACCENT_COLORS: Record<AccentColor, { accent: string; hover: string }> = {
  blue:   { accent: "#7aa2f7", hover: "#89b4fa" },
  purple: { accent: "#bb9af7", hover: "#cba6ff" },
  green:  { accent: "#9ece6a", hover: "#b5e87d" },
  orange: { accent: "#e0af68", hover: "#ebc07c" },
  pink:   { accent: "#f7768e", hover: "#ff8fa3" },
  teal:   { accent: "#7dcfff", hover: "#94d8ff" },
};

function createSettingsStore() {
  let initial = DEFAULTS;
  if (typeof localStorage !== "undefined") {
    try {
      const saved = localStorage.getItem("research-agent-settings");
      if (saved) {
        initial = { ...DEFAULTS, ...JSON.parse(saved) };
      }
    } catch {}
  }

  const { subscribe, set, update } = writable<AppSettings>(initial);

  function persist(settings: AppSettings) {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(
        "research-agent-settings",
        JSON.stringify(settings)
      );
    }
  }

  return {
    subscribe,
    set(value: AppSettings) {
      set(value);
      persist(value);
    },
    update(fn: (s: AppSettings) => AppSettings) {
      update((s) => {
        const next = fn(s);
        persist(next);
        return next;
      });
    },
  };
}

export const settings = createSettingsStore();
