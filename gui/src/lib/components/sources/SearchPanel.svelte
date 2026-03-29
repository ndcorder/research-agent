<script lang="ts">
  import { sources, selectedSource, rightPanel, projectDir } from "$lib/stores/project";
  import { readFile } from "$lib/utils/ipc";
  import type { SourceMeta } from "$lib/types";

  interface SearchResult {
    source: SourceMeta;
    line: string;
    lineNumber: number;
    matchStart: number;
    matchEnd: number;
  }

  let query = $state("");
  let results = $state<SearchResult[]>([]);
  let searching = $state(false);
  let searched = $state(false);
  let debounceTimer = $state<ReturnType<typeof setTimeout> | null>(null);

  let resultCount = $derived(results.length);

  $effect(() => {
    const q = query;
    if (debounceTimer) clearTimeout(debounceTimer);

    if (!q.trim()) {
      results = [];
      searched = false;
      return;
    }

    debounceTimer = setTimeout(() => {
      performSearch(q.trim());
    }, 300);
  });

  async function performSearch(q: string) {
    if (!$sources.length) return;

    searching = true;
    searched = true;
    const found: SearchResult[] = [];
    const lowerQ = q.toLowerCase();

    const promises = $sources.map(async (source) => {
      try {
        const content = await readFile(source.path);
        const lines = content.split("\n");
        for (let i = 0; i < lines.length; i++) {
          if (found.length >= 50) break;
          const lowerLine = lines[i].toLowerCase();
          const idx = lowerLine.indexOf(lowerQ);
          if (idx !== -1) {
            found.push({
              source,
              line: lines[i],
              lineNumber: i + 1,
              matchStart: idx,
              matchEnd: idx + q.length,
            });
          }
        }
      } catch {
        // Skip unreadable files
      }
    });

    await Promise.all(promises);
    results = found.slice(0, 50);
    searching = false;
  }

  function selectResult(result: SearchResult) {
    selectedSource.set(result.source.key);
    rightPanel.set("source");
  }

  function highlightMatch(line: string, start: number, end: number): string {
    const before = line.slice(0, start);
    const match = line.slice(start, end);
    const after = line.slice(end);
    const esc = (s: string) =>
      s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return `${esc(before)}<mark class="rounded bg-accent/30 px-0.5 text-accent">${esc(match)}</mark>${esc(after)}`;
  }
</script>

<div class="flex h-full flex-col overflow-hidden bg-bg">
  <!-- Search input -->
  <div class="flex-shrink-0 border-b border-border bg-bg-secondary p-3">
    <div class="relative">
      <svg
        class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-muted"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      <input
        type="text"
        bind:value={query}
        placeholder="Search across all sources..."
        class="w-full rounded bg-bg-tertiary py-1.5 pl-8 pr-3 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
      />
    </div>
    {#if searched}
      <p class="mt-1.5 text-xs text-text-muted">
        {#if searching}
          Searching...
        {:else}
          {resultCount} result{resultCount !== 1 ? "s" : ""}{resultCount >= 50 ? " (showing first 50)" : ""}
        {/if}
      </p>
    {/if}
  </div>

  <!-- Results list -->
  <div class="flex-1 overflow-y-auto">
    {#if !searched}
      <div class="flex h-full items-center justify-center p-8">
        <div class="text-center">
          <div class="mb-2 text-3xl text-text-muted">&#128269;</div>
          <p class="text-sm text-text-muted">Search full text of all source files</p>
        </div>
      </div>
    {:else if !searching && results.length === 0}
      <div class="flex h-full items-center justify-center p-8">
        <p class="text-sm text-text-muted">No matches found</p>
      </div>
    {:else}
      {#each results as result}
        <button
          class="w-full border-b border-border px-3 py-2.5 text-left transition-colors hover:bg-bg-secondary"
          onclick={() => selectResult(result)}
        >
          <div class="mb-1 flex items-center justify-between gap-2">
            <span class="truncate text-xs font-medium text-text-bright">
              {result.source.title || result.source.key}
            </span>
            <span class="flex-shrink-0 text-xs text-text-muted">
              L{result.lineNumber}
            </span>
          </div>
          {@const trimmed = result.line.trimStart()}
          {@const offset = result.line.length - trimmed.length}
          <p class="truncate text-xs leading-relaxed text-text-muted">
            {@html highlightMatch(trimmed, result.matchStart - offset, result.matchEnd - offset)}
          </p>
        </button>
      {/each}
    {/if}
  </div>
</div>
