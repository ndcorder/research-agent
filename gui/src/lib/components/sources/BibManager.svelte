<script lang="ts">
  import { projectDir, texContent, openFileRequest } from "$lib/stores/project";
  import { readFile } from "$lib/utils/ipc";
  import { parseCiteKeys } from "$lib/utils/latex";

  // --- Types ---

  interface BibEntry {
    key: string;
    type: string;
    title: string;
    author: string;
    year: string;
    raw: string;
    fields: Record<string, string>;
  }

  // --- State ---

  let entries = $state<BibEntry[]>([]);
  let bibPath = $state<string | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let searchQuery = $state("");
  let sortBy = $state<"key" | "year" | "type">("key");
  let selectedKey = $state<string | null>(null);

  // --- BibTeX parser ---

  function parseBibtex(content: string): BibEntry[] {
    const results: BibEntry[] = [];
    // Match @type{key, ... } blocks — handles nested braces one level deep
    const entryPattern = /@(\w+)\s*\{\s*([^,\s]+)\s*,([\s\S]*?)(?=\n@|\n*$)/g;
    let match;
    while ((match = entryPattern.exec(content)) !== null) {
      const type = match[1].toLowerCase();
      if (type === "string" || type === "preamble" || type === "comment") continue;
      const key = match[2].trim();
      const body = match[3];
      const fields = parseFields(body);
      results.push({
        key,
        type,
        title: fields["title"] || "",
        author: fields["author"] || "",
        year: fields["year"] || "",
        raw: match[0].trim(),
        fields,
      });
    }
    return results;
  }

  function parseFields(body: string): Record<string, string> {
    const fields: Record<string, string> = {};
    // Match field = {value} or field = "value" or field = number
    const fieldPattern = /(\w+)\s*=\s*(?:\{([^}]*(?:\{[^}]*\}[^}]*)*)\}|"([^"]*)"|(\d+))/g;
    let m;
    while ((m = fieldPattern.exec(body)) !== null) {
      const name = m[1].toLowerCase();
      const value = (m[2] ?? m[3] ?? m[4] ?? "").trim();
      fields[name] = value;
    }
    return fields;
  }

  // --- Derived data ---

  let citeKeys = $derived(parseCiteKeys($texContent));

  let usedEntries = $derived(
    filteredSorted().filter((e) => citeKeys.includes(e.key))
  );

  let unusedEntries = $derived(
    filteredSorted().filter((e) => !citeKeys.includes(e.key))
  );

  let missingKeys = $derived(
    citeKeys.filter((k) => !entries.some((e) => e.key === k))
  );

  let filteredMissing = $derived(
    searchQuery
      ? missingKeys.filter((k) => k.toLowerCase().includes(searchQuery.toLowerCase()))
      : missingKeys
  );

  let summary = $derived(
    `${entries.length} references (${usedEntries.length} used, ${unusedEntries.length} unused, ${missingKeys.length} missing)`
  );

  let selectedEntry = $derived(
    entries.find((e) => e.key === selectedKey) ?? null
  );

  function filteredSorted(): BibEntry[] {
    let list = entries;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (e) =>
          e.key.toLowerCase().includes(q) ||
          e.title.toLowerCase().includes(q) ||
          e.author.toLowerCase().includes(q) ||
          e.year.includes(q) ||
          e.type.toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => {
      if (sortBy === "key") return a.key.localeCompare(b.key);
      if (sortBy === "year") return (b.year || "0").localeCompare(a.year || "0");
      if (sortBy === "type") return a.type.localeCompare(b.type);
      return 0;
    });
  }

  // --- Load bib file ---

  $effect(() => {
    const dir = $projectDir;
    if (!dir) {
      entries = [];
      bibPath = null;
      return;
    }

    loading = true;
    error = null;

    readFile(`${dir}/references.bib`)
      .then((content) => {
        bibPath = `${dir}/references.bib`;
        entries = parseBibtex(content);
        loading = false;
      })
      .catch(() => {
        // Try fallback
        readFile(`${dir}/main.bib`)
          .then((content) => {
            bibPath = `${dir}/main.bib`;
            entries = parseBibtex(content);
          })
          .catch(() => {
            error = "No .bib file found (tried references.bib and main.bib)";
            entries = [];
            bibPath = null;
          })
          .finally(() => {
            loading = false;
          });
      });
  });

  // --- Handlers ---

  function selectEntry(key: string) {
    selectedKey = selectedKey === key ? null : key;
  }

  function openBibFile() {
    if (!bibPath) return;
    const name = bibPath.split("/").pop() || "references.bib";
    openFileRequest.set({ name, path: bibPath });
  }

  function typeLabel(type: string): string {
    const map: Record<string, string> = {
      article: "Art",
      inproceedings: "Conf",
      book: "Book",
      incollection: "Chap",
      phdthesis: "PhD",
      mastersthesis: "MSc",
      techreport: "Tech",
      misc: "Misc",
      unpublished: "Unpub",
    };
    return map[type] || type.slice(0, 4);
  }

  function typeColor(type: string): string {
    switch (type) {
      case "article":
        return "bg-accent/20 text-accent";
      case "inproceedings":
      case "conference":
        return "bg-success/20 text-success";
      case "book":
      case "incollection":
        return "bg-warning/20 text-warning";
      default:
        return "bg-bg-tertiary text-text-muted";
    }
  }

  function truncate(s: string, max: number): string {
    if (s.length <= max) return s;
    return s.slice(0, max - 1) + "\u2026";
  }
</script>

<div class="flex h-full flex-col overflow-hidden bg-bg">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-border bg-bg-secondary p-3">
    <!-- Search bar -->
    <input
      type="text"
      placeholder="Filter references..."
      bind:value={searchQuery}
      class="mb-2 w-full rounded bg-bg-tertiary px-2.5 py-1.5 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
    />

    <!-- Sort + summary -->
    <div class="flex items-center justify-between">
      <div class="flex gap-1">
        {#each ["key", "year", "type"] as s}
          <button
            class="rounded px-1.5 py-0.5 text-xs transition-colors {sortBy === s
              ? 'bg-accent/20 text-accent'
              : 'text-text-muted hover:text-text'}"
            onclick={() => (sortBy = s as "key" | "year" | "type")}
          >
            {s}
          </button>
        {/each}
      </div>
      <span class="text-xs text-text-muted">{summary}</span>
    </div>
  </div>

  {#if loading}
    <div class="flex flex-1 items-center justify-center">
      <span class="text-xs text-text-muted">Loading .bib file...</span>
    </div>
  {:else if error}
    <div class="flex flex-1 items-center justify-center p-4">
      <span class="text-xs text-text-muted">{error}</span>
    </div>
  {:else}
    <div class="flex flex-1 flex-col overflow-y-auto">
      <!-- Missing references -->
      {#if filteredMissing.length > 0}
        <div class="border-b border-border px-3 py-2">
          <h3 class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-danger">
            Missing ({filteredMissing.length})
          </h3>
          {#each filteredMissing as key}
            <div class="mb-1 rounded border border-danger/30 bg-danger/10 px-2 py-1 text-xs text-danger">
              <span class="font-mono">{key}</span>
              <span class="ml-1 text-xs opacity-70">-- cited but not in .bib</span>
            </div>
          {/each}
        </div>
      {/if}

      <!-- Used entries -->
      {#if usedEntries.length > 0}
        <div class="border-b border-border px-3 py-2">
          <h3 class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Used ({usedEntries.length})
          </h3>
          {#each usedEntries as entry}
            <button
              class="mb-1 w-full rounded border border-border bg-bg-secondary px-2 py-1.5 text-left transition-colors hover:bg-bg-tertiary {selectedKey === entry.key ? 'ring-1 ring-accent' : ''}"
              onclick={() => selectEntry(entry.key)}
              ondblclick={openBibFile}
            >
              <div class="flex items-center gap-1.5">
                <span class="flex-shrink-0 rounded px-1 py-0.5 text-[9px] font-medium {typeColor(entry.type)}">
                  {typeLabel(entry.type)}
                </span>
                <span class="min-w-0 flex-1 truncate font-mono text-xs text-text-bright">
                  {entry.key}
                </span>
                {#if entry.year}
                  <span class="flex-shrink-0 text-xs text-text-muted">{entry.year}</span>
                {/if}
              </div>
              {#if entry.title}
                <p class="mt-0.5 truncate text-xs text-text-muted">
                  {truncate(entry.title, 80)}
                </p>
              {/if}
              {#if entry.author}
                <p class="truncate text-xs text-text-muted opacity-60">
                  {truncate(entry.author, 60)}
                </p>
              {/if}
            </button>
          {/each}
        </div>
      {/if}

      <!-- Unused entries -->
      {#if unusedEntries.length > 0}
        <div class="px-3 py-2">
          <h3 class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Unused ({unusedEntries.length})
          </h3>
          {#each unusedEntries as entry}
            <button
              class="mb-1 w-full rounded border border-border bg-bg-secondary px-2 py-1.5 text-left opacity-50 transition-colors hover:opacity-80 {selectedKey === entry.key ? 'ring-1 ring-accent opacity-80' : ''}"
              onclick={() => selectEntry(entry.key)}
              ondblclick={openBibFile}
            >
              <div class="flex items-center gap-1.5">
                <span class="flex-shrink-0 rounded px-1 py-0.5 text-[9px] font-medium {typeColor(entry.type)}">
                  {typeLabel(entry.type)}
                </span>
                <span class="min-w-0 flex-1 truncate font-mono text-xs text-text-bright">
                  {entry.key}
                </span>
                {#if entry.year}
                  <span class="flex-shrink-0 text-xs text-text-muted">{entry.year}</span>
                {/if}
              </div>
              {#if entry.title}
                <p class="mt-0.5 truncate text-xs text-text-muted">
                  {truncate(entry.title, 80)}
                </p>
              {/if}
              {#if entry.author}
                <p class="truncate text-xs text-text-muted opacity-60">
                  {truncate(entry.author, 60)}
                </p>
              {/if}
            </button>
          {/each}
        </div>
      {/if}

      <!-- Empty state -->
      {#if entries.length === 0 && missingKeys.length === 0}
        <div class="flex flex-1 items-center justify-center p-4">
          <span class="text-xs text-text-muted">No BibTeX entries found</span>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Detail panel -->
  {#if selectedEntry}
    <div class="flex-shrink-0 border-t border-border bg-bg-secondary">
      <div class="flex items-center justify-between px-3 pt-2 pb-1">
        <h3 class="font-mono text-xs font-semibold text-text-bright">{selectedEntry.key}</h3>
        <button
          class="text-xs text-text-muted hover:text-text"
          onclick={() => (selectedKey = null)}
        >
          close
        </button>
      </div>
      <pre class="max-h-40 overflow-y-auto px-3 pb-3 text-xs leading-relaxed text-text">{selectedEntry.raw}</pre>
    </div>
  {/if}
</div>
