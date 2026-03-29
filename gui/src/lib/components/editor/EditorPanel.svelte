<script lang="ts">
  import { onMount } from "svelte";
  import { readFile, writeFile } from "$lib/utils/ipc";
  import { projectDir, texSections, texContent, wordCount, editorGoToLine, selectedSource, rightPanel, openFileRequest, closeActiveTabRequest, saveActiveTabRequest, cycleTabRequest, showSnippetMenu } from "$lib/stores/project";
  import { sources } from "$lib/stores/project";
  import SnippetMenu from "./SnippetMenu.svelte";
  import { parseTexSections, countWords, parseCiteKeys } from "$lib/utils/latex";
  import { settings } from "$lib/stores/settings";
  import { toasts } from "$lib/stores/toast";
  import { compileLatex } from "$lib/utils/ipc";
  import { get } from "svelte/store";

  interface Tab {
    name: string;
    path: string;
    dirty: boolean;
    language: string;
  }

  let tabs = $state<Tab[]>([{ name: "main.tex", path: "main.tex", dirty: false, language: "latex" }]);
  let activeTab = $state(0);
  let previousTab = -1;
  let editorContainer: HTMLDivElement;
  let tabStrip: HTMLDivElement;
  let editor: any = null;
  let monaco: typeof import("monaco-editor") | null = null;
  let saveTimeout: ReturnType<typeof setTimeout> | null = null;

  function extToLanguage(path: string): string {
    const ext = path.split(".").pop()?.toLowerCase() ?? "";
    switch (ext) {
      case "tex": return "latex";
      case "md": return "markdown";
      case "json": return "json";
      case "bib": return "bibtex";
      case "py": return "python";
      case "js": return "javascript";
      case "ts": return "typescript";
      case "yaml": case "yml": return "yaml";
      case "toml": return "toml";
      case "sh": case "bash": return "shell";
      case "css": return "css";
      case "html": return "html";
      default: return "plaintext";
    }
  }

  function extToIcon(path: string): string {
    const ext = path.split(".").pop()?.toLowerCase() ?? "";
    switch (ext) {
      case "tex": return "T";
      case "md": return "M";
      case "json": return "{}";
      case "bib": return "B";
      case "py": return "Py";
      default: return "#";
    }
  }

  function defineLatexLanguage(m: typeof import("monaco-editor")) {
    m.languages.register({ id: "latex" });
    m.languages.setMonarchTokensProvider("latex", {
      tokenizer: {
        root: [
          [/\\[a-zA-Z@]+/, "keyword"],
          [/\{/, "delimiter.curly"],
          [/\}/, "delimiter.curly"],
          [/\[/, "delimiter.square"],
          [/\]/, "delimiter.square"],
          [/%.*$/, "comment"],
          [/\$\$/, { token: "string.math", next: "@mathDisplay" }],
          [/\$/, { token: "string.math", next: "@mathInline" }],
          [/\\begin\{(equation|align|gather|multline)\*?\}/, { token: "keyword", next: "@mathEnv" }],
          [/&/, "operator"],
          [/\\\\/, "operator"],
          [/[~^_]/, "operator"],
        ],
        mathInline: [
          [/[^$\\]+/, "string.math"],
          [/\\[a-zA-Z@]+/, "keyword"],
          [/\$/, { token: "string.math", next: "@pop" }],
        ],
        mathDisplay: [
          [/[^$\\]+/, "string.math"],
          [/\\[a-zA-Z@]+/, "keyword"],
          [/\$\$/, { token: "string.math", next: "@pop" }],
        ],
        mathEnv: [
          [/[^\\]+/, "string.math"],
          [/\\end\{(equation|align|gather|multline)\*?\}/, { token: "keyword", next: "@pop" }],
          [/\\[a-zA-Z@]+/, "keyword"],
        ],
      },
    });
  }

  function defineTheme(m: typeof import("monaco-editor")) {
    m.editor.defineTheme("research-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "7aa2f7" },
        { token: "comment", foreground: "565f89", fontStyle: "italic" },
        { token: "string.math", foreground: "9ece6a" },
        { token: "delimiter.curly", foreground: "e0af68" },
        { token: "delimiter.square", foreground: "7dcfff" },
        { token: "operator", foreground: "f7768e" },
      ],
      colors: {
        "editor.background": "#1a1b26",
        "editor.foreground": "#c0caf5",
        "editor.lineHighlightBackground": "#24283b",
        "editor.selectionBackground": "#3b3f5c",
        "editorCursor.foreground": "#7aa2f7",
        "editorLineNumber.foreground": "#565f89",
        "editorLineNumber.activeForeground": "#c0caf5",
        "editorIndentGuide.background": "#2f3350",
        "editorWidget.background": "#24283b",
        "editorWidget.border": "#3b3f5c",
        "input.background": "#2f3350",
        "input.foreground": "#c0caf5",
        "input.border": "#3b3f5c",
        "list.hoverBackground": "#2f3350",
        "list.activeSelectionBackground": "#3b3f5c",
        "minimap.background": "#1a1b26",
      },
    });
  }

  async function loadFileContent(tab: Tab): Promise<string> {
    const dir = $projectDir;
    if (!dir) return "";
    try {
      return await readFile(`${dir}/${tab.path}`);
    } catch {
      return `% ${tab.name}\n`;
    }
  }

  async function saveTab(tab: Tab): Promise<void> {
    const dir = $projectDir;
    if (!dir || !editor) return;
    const idx = tabs.indexOf(tab);
    if (idx !== activeTab) return; // can only save content if it's the active editor
    const content = editor.getValue();
    try {
      await writeFile(`${dir}/${tab.path}`, content);
      tab.dirty = false;
      tabs = [...tabs];

      // Auto-compile if enabled and this is a .tex file
      if (tab.language === "latex" && get(settings).autoCompileOnSave) {
        compileLatex(dir).then((r) => {
          if (r.success) toasts.success("Auto-compiled");
          else toasts.warning("Auto-compile failed");
        });
      }
    } catch {
      // save failed silently
    }
  }

  function scheduleSave() {
    if (saveTimeout) clearTimeout(saveTimeout);
    const tab = tabs[activeTab];
    if (!tab) return;
    tab.dirty = true;
    tabs = [...tabs];

    saveTimeout = setTimeout(async () => {
      await saveTab(tab);
      if (tab.language === "latex") {
        updateTexMetadata();
      }
    }, 1000);
  }

  function openFile(name: string, path: string) {
    // Check if already open
    const existingIdx = tabs.findIndex((t) => t.path === path);
    if (existingIdx >= 0) {
      activeTab = existingIdx;
      return;
    }
    // Add new tab
    const language = extToLanguage(path);
    tabs = [...tabs, { name, path, dirty: false, language }];
    activeTab = tabs.length - 1;
  }

  async function closeTab(idx: number) {
    if (idx === 0) return; // main.tex is pinned
    const tab = tabs[idx];
    // Save if dirty and this is the active tab
    if (tab.dirty && idx === activeTab) {
      await saveTab(tab);
    }
    tabs = tabs.filter((_, i) => i !== idx);
    // Adjust activeTab
    if (activeTab === idx) {
      activeTab = Math.min(idx, tabs.length - 1);
    } else if (activeTab > idx) {
      activeTab = activeTab - 1;
    }
    previousTab = -1; // force reload
  }

  onMount(async () => {
    const m = await import("monaco-editor");
    monaco = m;

    self.MonacoEnvironment = {
      getWorker() {
        return new Worker(
          new URL("monaco-editor/esm/vs/editor/editor.worker.js", import.meta.url),
          { type: "module" }
        );
      },
    };

    defineLatexLanguage(m);
    defineTheme(m);

    const content = await loadFileContent(tabs[activeTab]);

    editor = m.editor.create(editorContainer, {
      value: content,
      language: tabs[activeTab].language,
      theme: "research-dark",
      fontFamily: "var(--font-mono)",
      fontSize: 15,
      lineHeight: 24,
      minimap: { enabled: true, scale: 2 },
      wordWrap: "on",
      lineNumbers: "on",
      renderLineHighlight: "gutter",
      scrollBeyondLastLine: false,
      padding: { top: 8, bottom: 8 },
      bracketPairColorization: { enabled: true },
      automaticLayout: false,
      tabSize: 2,
      smoothScrolling: true,
      cursorBlinking: "smooth",
      cursorSmoothCaretAnimation: "on",
    });

    editor.onDidChangeModelContent(() => {
      scheduleSave();
      if (tabs[activeTab]?.language === "latex") {
        updateTexMetadata();
      }
    });

    // Citation autocomplete: suggest source keys inside \cite{...}
    m.languages.registerCompletionItemProvider("latex", {
      triggerCharacters: ["{", ","],
      provideCompletionItems(model, position) {
        const textUntilPosition = model.getValueInRange({
          startLineNumber: position.lineNumber,
          startColumn: 1,
          endLineNumber: position.lineNumber,
          endColumn: position.column,
        });
        if (!/\\cite[tp]?\*?\{[^}]*$/.test(textUntilPosition)) {
          return { suggestions: [] };
        }

        // Determine the word range at the cursor for replacement
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };

        const sourceList = get(sources);
        return {
          suggestions: sourceList.map((src) => ({
            label: src.key,
            kind: m.languages.CompletionItemKind.Reference,
            detail: src.title || "",
            documentation: `${src.authors?.join(", ") || ""} (${src.year || ""})`,
            insertText: src.key,
            range,
          })),
        };
      },
    });

    // Initial metadata parse
    updateTexMetadata();
    previousTab = activeTab;
  });

  function updateTexMetadata() {
    if (!editor || tabs[activeTab]?.language !== "latex") return;
    const content = editor.getValue();
    texContent.set(content);
    texSections.set(parseTexSections(content));
    wordCount.set(countWords(content));
  }

  $effect(() => {
    const handleResize = () => editor?.layout();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  });

  $effect(() => {
    return () => {
      if (saveTimeout) clearTimeout(saveTimeout);
      editor?.dispose();
    };
  });

  // Tab switching: load new content and set language
  $effect(() => {
    const current = activeTab;
    if (!editor || !monaco || current === previousTab) return;
    previousTab = current;
    const tab = tabs[current];
    if (!tab) return;
    loadFileContent(tab).then((content) => {
      editor.setValue(content);
      const model = editor.getModel();
      if (model) {
        monaco!.editor.setModelLanguage(model, tab.language);
      }
    });
  });

  $effect(() => {
    if (!editorContainer) return;
    const observer = new ResizeObserver(() => editor?.layout());
    observer.observe(editorContainer);
    return () => observer.disconnect();
  });

  // Go-to-line from sidebar section clicks
  $effect(() => {
    const line = $editorGoToLine;
    if (line && editor) {
      // Switch to main.tex if not already there
      if (activeTab !== 0) {
        activeTab = 0;
      }
      editor.revealLineInCenter(line);
      editor.setPosition({ lineNumber: line, column: 1 });
      editor.focus();
      editorGoToLine.set(null);
    }
  });

  // Handle openFileRequest store
  $effect(() => {
    const req = $openFileRequest;
    if (req) {
      openFile(req.name, req.path);
      openFileRequest.set(null);
    }
  });

  // Cmd+W → Close active tab
  $effect(() => {
    if ($closeActiveTabRequest) {
      closeActiveTabRequest.set(false);
      if (activeTab > 0) {
        closeTab(activeTab);
      }
    }
  });

  // Cmd+S → Save active tab immediately
  $effect(() => {
    if ($saveActiveTabRequest) {
      saveActiveTabRequest.set(false);
      const tab = tabs[activeTab];
      if (tab) {
        if (saveTimeout) clearTimeout(saveTimeout);
        saveTab(tab);
        if (tab.language === "latex") {
          updateTexMetadata();
        }
      }
    }
  });

  // Ctrl+Tab → Cycle tabs
  $effect(() => {
    const dir = $cycleTabRequest;
    if (dir !== 0) {
      cycleTabRequest.set(0);
      if (tabs.length > 1) {
        activeTab = (activeTab + dir + tabs.length) % tabs.length;
      }
    }
  });

  // Settings: font size changes
  $effect(() => {
    const fontSize = $settings.editorFontSize;
    if (editor) {
      editor.updateOptions({ fontSize });
    }
  });

  // Settings: minimap toggle
  $effect(() => {
    const minimap = $settings.editorMinimap;
    if (editor) {
      editor.updateOptions({ minimap: { enabled: minimap } });
    }
  });

  // Settings: word wrap toggle
  $effect(() => {
    const wrap = $settings.wordWrap;
    if (editor) {
      editor.updateOptions({ wordWrap: wrap ? "on" : "off" });
    }
  });

  // Citation click-through: detect \cite{key} clicks
  $effect(() => {
    if (!editor || !monaco) return;
    const disposable = editor.onMouseDown((e: any) => {
      if (!e.target?.position || !monaco) return;
      const model = editor.getModel();
      if (!model) return;
      const line = model.getLineContent(e.target.position.lineNumber);
      const col = e.target.position.column;

      // Find \cite{...} at cursor position
      const citePattern = /\\cite[tp]?\*?\{([^}]+)\}/g;
      let match;
      while ((match = citePattern.exec(line)) !== null) {
        const start = match.index;
        const end = start + match[0].length;
        if (col >= start + 1 && col <= end + 1) {
          // Find which key the cursor is on
          const keysStr = match[1];
          const keys = keysStr.split(",").map((k: string) => k.trim());
          if (keys.length > 0) {
            selectedSource.set(keys[0]);
            rightPanel.set("source");
          }
          break;
        }
      }
    });
    return () => disposable.dispose();
  });
</script>

<div class="flex h-full flex-col bg-bg">
  <div class="flex items-center border-b border-border bg-bg-secondary" bind:this={tabStrip}>
    <div class="flex flex-1 items-center overflow-x-auto scrollbar-thin">
      {#each tabs as tab, i}
        <button
          class="group flex shrink-0 items-center gap-1.5 border-r border-border px-3 py-1.5 text-xs transition-colors
            {i === activeTab ? 'bg-bg text-text-bright' : 'text-text-muted hover:text-text hover:bg-bg-tertiary'}"
          onclick={() => (activeTab = i)}
        >
          <span class="text-accent opacity-60">{extToIcon(tab.path)}</span>
          <span class="whitespace-nowrap">{tab.name}</span>
          {#if tab.dirty}
            <span class="ml-0.5 h-2 w-2 shrink-0 rounded-full bg-accent"></span>
          {/if}
          {#if i > 0}
            <span
              class="ml-1 flex h-4 w-4 shrink-0 items-center justify-center rounded opacity-0 transition-opacity hover:bg-bg-tertiary group-hover:opacity-100"
              role="button"
              tabindex="-1"
              onclick={(e) => { e.stopPropagation(); closeTab(i); }}
              onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); closeTab(i); } }}
            >&times;</span>
          {/if}
        </button>
      {/each}
    </div>
    <button
      class="flex shrink-0 items-center gap-1 px-2.5 py-1.5 text-xs text-text-muted transition-colors hover:text-text-bright hover:bg-bg-tertiary border-l border-border"
      title="Insert Snippet (Cmd+J)"
      onclick={() => showSnippetMenu.update((v) => !v)}
    >
      <svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M4 2L4 14M8 5L8 14M12 8L12 14" stroke-linecap="round"/>
      </svg>
      <span>Snippet</span>
    </button>
  </div>

  <div class="relative flex-1 overflow-hidden" bind:this={editorContainer}></div>
</div>

<SnippetMenu {editor} {monaco} />

<style>
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: rgba(86, 95, 137, 0.4) transparent;
  }
  .scrollbar-thin::-webkit-scrollbar {
    height: 4px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: rgba(86, 95, 137, 0.4);
    border-radius: 2px;
  }
</style>
