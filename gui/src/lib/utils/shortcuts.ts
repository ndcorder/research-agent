import { get } from "svelte/store";
import {
  activePage,
  rightPanel,
  projectDir,
  closeActiveTabRequest,
  saveActiveTabRequest,
  cycleTabRequest,
  showCommandPalette,
  showSettings,
  showSnippetMenu,
  bottomTerminalVisible,
} from "$lib/stores/project";
import { settings } from "$lib/stores/settings";
import { compileLatex } from "$lib/utils/ipc";
import { exportResearchSummary } from "$lib/utils/export";
import { toasts } from "$lib/stores/toast";

const isMac =
  typeof navigator !== "undefined" &&
  /Mac|iPod|iPhone|iPad/.test(navigator.platform);

function modKey(e: KeyboardEvent): boolean {
  return isMac ? e.metaKey : e.ctrlKey;
}

export function setupShortcuts(): () => void {
  function handler(e: KeyboardEvent) {
    const key = e.key.toLowerCase();

    // Escape → Close command palette / settings
    if (key === "escape") {
      const cp = get(showCommandPalette);
      const sp = get(showSettings);
      if (cp) {
        e.preventDefault();
        showCommandPalette.set(false);
        return;
      }
      if (sp) {
        e.preventDefault();
        showSettings.set(false);
        return;
      }
    }

    if (!modKey(e)) return;

    // Cmd+` → Toggle bottom terminal
    if (key === "`" && !e.shiftKey) {
      e.preventDefault();
      bottomTerminalVisible.update((v) => !v);
      return;
    }

    // Cmd+W → Close active editor tab
    if (key === "w" && !e.shiftKey && !e.altKey) {
      e.preventDefault();
      e.stopPropagation();
      closeActiveTabRequest.set(true);
      return;
    }

    // Cmd+S → Save active tab
    if (key === "s" && !e.shiftKey) {
      e.preventDefault();
      saveActiveTabRequest.set(true);
      return;
    }

    // Cmd+P → Command palette
    if (key === "p" && !e.shiftKey) {
      e.preventDefault();
      showCommandPalette.update((v) => !v);
      return;
    }

    // Cmd+, → Settings
    if (key === ",") {
      e.preventDefault();
      showSettings.update((v) => !v);
      return;
    }

    // Cmd+Shift+B → Compile LaTeX
    if (e.shiftKey && key === "b") {
      e.preventDefault();
      const dir = get(projectDir);
      if (dir) {
        toasts.info("Compiling LaTeX...");
        compileLatex(dir).then((r) => {
          if (r.success) toasts.success("Compiled successfully");
          else toasts.error("Compilation failed");
        });
      }
      return;
    }

    // Cmd+Shift+E → Export research summary
    if (e.shiftKey && key === "e") {
      e.preventDefault();
      const dir = get(projectDir);
      if (dir) {
        exportResearchSummary(dir);
      }
      return;
    }

    // Cmd+1 → Workspace
    if (key === "1" && !e.shiftKey) {
      e.preventDefault();
      activePage.set("workspace");
      return;
    }

    // Cmd+2 → Terminal
    if (key === "2" && !e.shiftKey) {
      e.preventDefault();
      activePage.set("terminal");
      return;
    }

    // Cmd+= / Cmd+- → Zoom editor font
    if (key === "=" || key === "+") {
      e.preventDefault();
      settings.update((s) => ({
        ...s,
        editorFontSize: Math.min(s.editorFontSize + 1, 24),
      }));
      return;
    }
    if (key === "-" && !e.shiftKey) {
      e.preventDefault();
      settings.update((s) => ({
        ...s,
        editorFontSize: Math.max(s.editorFontSize - 1, 9),
      }));
      return;
    }

    // Cmd+0 → Reset font size
    if (key === "0" && !e.shiftKey) {
      e.preventDefault();
      settings.update((s) => ({ ...s, editorFontSize: 13 }));
      return;
    }

    // Cmd+J → Toggle snippet menu
    if (key === "j" && !e.shiftKey && !e.altKey) {
      e.preventDefault();
      showSnippetMenu.update((v) => !v);
      return;
    }

    // Cmd+Shift+G → Toggle graph
    if (e.shiftKey && key === "g") {
      e.preventDefault();
      const current = get(rightPanel);
      rightPanel.set(current === "graph" ? "source" : "graph");
      return;
    }

    // Cmd+Shift+P → Toggle PDF
    if (e.shiftKey && key === "p") {
      e.preventDefault();
      const current = get(rightPanel);
      rightPanel.set(current === "pdf" ? "source" : "pdf");
      return;
    }

    // Cmd+Shift+T → Toggle timeline
    if (e.shiftKey && key === "t") {
      e.preventDefault();
      const current = get(rightPanel);
      rightPanel.set(current === "timeline" ? "source" : "timeline");
      return;
    }

    // Cmd+Shift+F → Focus search
    if (e.shiftKey && key === "f") {
      e.preventDefault();
      const input = document.querySelector<HTMLInputElement>(
        'input[placeholder="Search..."]'
      );
      input?.focus();
      return;
    }

    // Cmd+[ → Previous right panel tab
    if (key === "[" && !e.shiftKey) {
      e.preventDefault();
      const panels = ["graph", "source", "pdf", "claim", "timeline", "figures", "dashboard", "bib"] as const;
      const current = get(rightPanel);
      const idx = panels.indexOf(current);
      rightPanel.set(panels[(idx - 1 + panels.length) % panels.length]);
      return;
    }

    // Cmd+] → Next right panel tab
    if (key === "]" && !e.shiftKey) {
      e.preventDefault();
      const panels = ["graph", "source", "pdf", "claim", "timeline", "figures", "dashboard", "bib"] as const;
      const current = get(rightPanel);
      const idx = panels.indexOf(current);
      rightPanel.set(panels[(idx + 1) % panels.length]);
      return;
    }
  }

  // Ctrl+Tab / Ctrl+Shift+Tab for tab cycling (not Cmd on Mac - matches browser convention)
  function tabHandler(e: KeyboardEvent) {
    if (e.key === "Tab" && e.ctrlKey) {
      e.preventDefault();
      cycleTabRequest.set(e.shiftKey ? -1 : 1);
      return;
    }
  }

  window.addEventListener("keydown", handler, true);
  window.addEventListener("keydown", tabHandler, true);
  return () => {
    window.removeEventListener("keydown", handler, true);
    window.removeEventListener("keydown", tabHandler, true);
  };
}
