<script lang="ts">
  import { get } from "svelte/store";
  import {
    showCommandPalette,
    sources,
    texSections,
    editorGoToLine,
    openFileRequest,
    selectedSource,
    rightPanel,
    activePage,
    projectDir,
    showSettings,
  } from "$lib/stores/project";
  import { compileLatex } from "$lib/utils/ipc";
  import { exportResearchSummary } from "$lib/utils/export";
  import { toasts } from "$lib/stores/toast";

  type CommandCategory = "file" | "section" | "action";

  interface CommandItem {
    id: string;
    category: CommandCategory;
    label: string;
    hint: string;
    prefix: string;
    execute: () => void;
  }

  let query = $state("");
  let selectedIndex = $state(0);
  let inputEl: HTMLInputElement | undefined = $state();

  // Build the full command list from stores
  let allItems = $derived.by((): CommandItem[] => {
    const items: CommandItem[] = [];

    // Files: main.tex is always available
    items.push({
      id: "file:main.tex",
      category: "file",
      label: "main.tex",
      hint: "LaTeX manuscript",
      prefix: "T",
      execute: () => openFileRequest.set({ name: "main.tex", path: "main.tex" }),
    });

    // Files: common project files
    const commonFiles = [
      { name: "references.bib", hint: "Bibliography", prefix: "B" },
      { name: ".paper.json", hint: "Paper config", prefix: "{}" },
    ];
    for (const f of commonFiles) {
      items.push({
        id: `file:${f.name}`,
        category: "file",
        label: f.name,
        hint: f.hint,
        prefix: f.prefix,
        execute: () => openFileRequest.set({ name: f.name, path: f.name }),
      });
    }

    // Files: source files from the sources store
    const srcList = get(sources);
    for (const src of srcList) {
      const filename = `${src.key}.md`;
      items.push({
        id: `file:source:${src.key}`,
        category: "file",
        label: filename,
        hint: src.title ?? `research/sources/${filename}`,
        prefix: "S",
        execute: () => {
          selectedSource.set(src.key);
          rightPanel.set("source");
        },
      });
    }

    // Sections: from texSections store
    const secList = get(texSections);
    for (const sec of secList) {
      const indent = sec.level > 1 ? "\u2003".repeat(sec.level - 1) : "";
      items.push({
        id: `section:${sec.line}:${sec.title}`,
        category: "section",
        label: `${indent}${sec.title}`,
        hint: `L${sec.line}`,
        prefix: "\u00A7",
        execute: () => {
          editorGoToLine.set(sec.line);
          activePage.set("workspace");
        },
      });
    }

    // Actions
    const actions: Omit<CommandItem, "id" | "category">[] = [
      {
        label: "Compile LaTeX",
        hint: "\u2318\u21E7B",
        prefix: "\u25B6",
        execute: () => {
          const dir = get(projectDir);
          if (dir) {
            toasts.info("Compiling LaTeX...");
            compileLatex(dir).then((r) => {
              if (r.success) toasts.success("Compiled successfully");
              else toasts.error("Compilation failed");
            });
          }
        },
      },
      {
        label: "Export Research Summary",
        hint: "\u2318\u21E7E",
        prefix: "\u2913",
        execute: () => {
          const dir = get(projectDir);
          if (dir) {
            exportResearchSummary(dir);
          }
        },
      },
      {
        label: "Toggle Graph",
        hint: "\u2318\u21E7G",
        prefix: "\u25C9",
        execute: () => {
          const cur = get(rightPanel);
          rightPanel.set(cur === "graph" ? "source" : "graph");
        },
      },
      {
        label: "Toggle PDF",
        hint: "\u2318\u21E7P",
        prefix: "\u25A2",
        execute: () => {
          const cur = get(rightPanel);
          rightPanel.set(cur === "pdf" ? "source" : "pdf");
        },
      },
      {
        label: "Toggle Timeline",
        hint: "\u2318\u21E7T",
        prefix: "\u23F1",
        execute: () => {
          const cur = get(rightPanel);
          rightPanel.set(cur === "timeline" ? "source" : "timeline");
        },
      },
      {
        label: "Open Settings",
        hint: "\u2318,",
        prefix: "\u2699",
        execute: () => showSettings.set(true),
      },
      {
        label: "Switch to Workspace",
        hint: "\u23181",
        prefix: "\u2395",
        execute: () => activePage.set("workspace"),
      },
      {
        label: "Switch to Terminal",
        hint: "\u23182",
        prefix: ">_",
        execute: () => activePage.set("terminal"),
      },
    ];

    for (const action of actions) {
      items.push({
        id: `action:${action.label}`,
        category: "action",
        ...action,
      });
    }

    return items;
  });

  // Fuzzy filter + sort by match position
  let filteredItems = $derived.by((): (CommandItem & { matchIndices: number[] })[] => {
    const q = query.toLowerCase().trim();
    if (!q) {
      return allItems.map((item) => ({ ...item, matchIndices: [] }));
    }

    const results: (CommandItem & { matchIndices: number[]; matchPos: number })[] = [];

    for (const item of allItems) {
      const label = item.label.toLowerCase();
      const indices = fuzzyMatch(label, q);
      if (indices) {
        results.push({ ...item, matchIndices: indices, matchPos: indices[0] ?? Infinity });
      }
    }

    results.sort((a, b) => a.matchPos - b.matchPos);
    return results;
  });

  function fuzzyMatch(text: string, pattern: string): number[] | null {
    const indices: number[] = [];
    let pi = 0;
    for (let ti = 0; ti < text.length && pi < pattern.length; ti++) {
      if (text[ti] === pattern[pi]) {
        indices.push(ti);
        pi++;
      }
    }
    return pi === pattern.length ? indices : null;
  }

  // Reset selection when query changes
  $effect(() => {
    query;
    selectedIndex = 0;
  });

  // Auto-focus input when palette opens
  $effect(() => {
    if ($showCommandPalette && inputEl) {
      query = "";
      selectedIndex = 0;
      // Delay focus to ensure DOM is ready
      requestAnimationFrame(() => inputEl?.focus());
    }
  });

  function executeSelected() {
    const item = filteredItems[selectedIndex];
    if (item) {
      showCommandPalette.set(false);
      item.execute();
    }
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, filteredItems.length - 1);
      scrollToSelected();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      scrollToSelected();
    } else if (e.key === "Enter") {
      e.preventDefault();
      executeSelected();
    } else if (e.key === "Escape") {
      e.preventDefault();
      showCommandPalette.set(false);
    }
  }

  function scrollToSelected() {
    requestAnimationFrame(() => {
      const el = document.querySelector(`[data-cmd-index="${selectedIndex}"]`);
      el?.scrollIntoView({ block: "nearest" });
    });
  }

  function onBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      showCommandPalette.set(false);
    }
  }

  function highlightLabel(label: string, indices: number[]): string {
    if (indices.length === 0) return escapeHtml(label);
    const chars = [...label];
    const indexSet = new Set(indices);
    let result = "";
    for (let i = 0; i < chars.length; i++) {
      const ch = escapeHtml(chars[i]);
      if (indexSet.has(i)) {
        result += `<span class="text-accent font-bold">${ch}</span>`;
      } else {
        result += ch;
      }
    }
    return result;
  }

  function escapeHtml(s: string): string {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function categoryLabel(cat: CommandCategory): string {
    switch (cat) {
      case "file": return "Files";
      case "section": return "Sections";
      case "action": return "Actions";
    }
  }

  // Group items by category for display, preserving order within each group
  let groupedItems = $derived.by(() => {
    const groups: { category: CommandCategory; label: string; items: (typeof filteredItems) }[] = [];
    const catOrder: CommandCategory[] = ["file", "section", "action"];
    for (const cat of catOrder) {
      const catItems = filteredItems.filter((i) => i.category === cat);
      if (catItems.length > 0) {
        groups.push({ category: cat, label: categoryLabel(cat), items: catItems });
      }
    }
    return groups;
  });

  // Flat index mapping for keyboard nav
  let flatItems = $derived(filteredItems);
</script>

{#if $showCommandPalette}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh]"
    onclick={onBackdropClick}
  >
    <div
      class="flex max-h-[60vh] w-full max-w-[600px] flex-col overflow-hidden rounded-lg border border-border bg-bg-secondary shadow-2xl"
      role="dialog"
      aria-label="Command palette"
    >
      <!-- Search input -->
      <div class="flex items-center border-b border-border px-3">
        <span class="mr-2 text-sm text-text-muted">></span>
        <input
          bind:this={inputEl}
          bind:value={query}
          onkeydown={onKeydown}
          class="w-full bg-transparent py-3 text-sm text-text outline-none placeholder:text-text-muted"
          placeholder="Type to search files, sections, and actions..."
          spellcheck="false"
          autocomplete="off"
        />
      </div>

      <!-- Results list -->
      <div class="overflow-y-auto">
        {#if flatItems.length === 0}
          <div class="px-4 py-8 text-center text-sm text-text-muted">
            No matching commands
          </div>
        {:else}
          {#each groupedItems as group}
            <div class="px-3 pt-2 pb-1 text-xs font-semibold uppercase tracking-wider text-text-muted">
              {group.label}
            </div>
            {#each group.items as item, i}
              {@const flatIdx = flatItems.indexOf(item)}
              <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
              <div
                data-cmd-index={flatIdx}
                class="mx-1 flex cursor-pointer items-center gap-2 rounded px-3 py-1.5 text-sm transition-colors
                  {flatIdx === selectedIndex ? 'bg-bg-tertiary text-text-bright' : 'text-text hover:bg-bg-tertiary/50'}"
                onclick={() => { selectedIndex = flatIdx; executeSelected(); }}
                onmouseenter={() => { selectedIndex = flatIdx; }}
              >
                <span class="w-6 shrink-0 text-center text-xs text-text-muted">{item.prefix}</span>
                <span class="min-w-0 flex-1 truncate">
                  {@html highlightLabel(item.label, item.matchIndices)}
                </span>
                <span class="shrink-0 text-xs text-text-muted">{item.hint}</span>
              </div>
            {/each}
          {/each}
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex items-center gap-4 border-t border-border px-3 py-1.5 text-xs text-text-muted">
        <span><kbd class="rounded bg-bg-tertiary px-1 py-0.5">\u2191\u2193</kbd> navigate</span>
        <span><kbd class="rounded bg-bg-tertiary px-1 py-0.5">\u21B5</kbd> select</span>
        <span><kbd class="rounded bg-bg-tertiary px-1 py-0.5">esc</kbd> close</span>
      </div>
    </div>
  </div>
{/if}
