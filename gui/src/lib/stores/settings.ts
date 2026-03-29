import { writable } from "svelte/store";

export interface AppSettings {
  editorFontSize: number;
  editorMinimap: boolean;
  autoCompileOnSave: boolean;
  showLineNumbers: boolean;
  wordWrap: boolean;
}

const DEFAULTS: AppSettings = {
  editorFontSize: 13,
  editorMinimap: true,
  autoCompileOnSave: false,
  showLineNumbers: true,
  wordWrap: true,
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
