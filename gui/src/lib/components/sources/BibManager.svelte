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

  // --- Field completeness & format checking ---

  const REQUIRED_FIELDS: Record<string, string[]> = {
    article: ["author", "title", "journal", "year"],
    inproceedings: ["author", "title", "booktitle", "year"],
    conference: ["author", "title", "booktitle", "year"],
    book: ["title", "publisher", "year"], // author OR editor checked separately below
    incollection: ["author", "title", "booktitle", "publisher", "year"],
    phdthesis: ["author", "title", "school", "year"],
    mastersthesis: ["author", "title", "school", "year"],
    techreport: ["author", "title", "institution", "year"],
    inbook: ["title", "publisher", "year"], // author OR editor checked separately below
    misc: [],
    unpublished: ["author", "title"],
  };

  interface FieldIssue {
    type: "missing" | "format";
    message: string;
  }

  function getEntryIssues(entry: BibEntry): FieldIssue[] {
    const issues: FieldIssue[] = [];
    const required = REQUIRED_FIELDS[entry.type] ?? [];

    for (const field of required) {
      if (!entry.fields[field]) {
        issues.push({ type: "missing", message: `Missing required field: ${field}` });
      }
    }

    // book/inbook need author OR editor
    if ((entry.type === "book" || entry.type === "inbook") && !entry.fields["author"] && !entry.fields["editor"]) {
      issues.push({ type: "missing", message: "Missing required field: author or editor" });
    }

    // Format issues
    if (entry.title && /\\(?:textit|textbf|emph|textsc)\{/.test(entry.title)) {
      issues.push({ type: "format", message: "Title contains LaTeX markup (use BibTeX braces instead)" });
    }

    return issues;
  }

  // --- Derived data ---

  let citeKeys = $derived(parseCiteKeys($texContent));

  let duplicateKeys = $derived.by(() => {
    const seen = new Map<string, number>();
    for (const e of entries) {
      seen.set(e.key, (seen.get(e.key) ?? 0) + 1);
    }
    return new Set([...seen.entries()].filter(([, c]) => c > 1).map(([k]) => k));
  });

  // Memoize issues per entry to avoid redundant recomputation in templates
  let issuesByKey = $derived.by(() => {
    const map = new Map<string, FieldIssue[]>();
    for (const e of entries) {
      map.set(e.key, getEntryIssues(e));
    }
    return map;
  });

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

  let totalIssues = $derived(
    entries.reduce((n, e) => n + (issuesByKey.get(e.key)?.length ?? 0) + (duplicateKeys.has(e.key) ? 1 : 0), 0)
  );

  let summary = $derived(
    `${entries.length} refs (${usedEntries.length} used, ${unusedEntries.length} unused, ${missingKeys.length} missing)` +
      (totalIssues > 0 ? ` \u00b7 ${totalIssues} issues` : "")
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
            {@const issues = issuesByKey.get(entry.key) ?? []}
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
                {#if issues.length > 0 || duplicateKeys.has(entry.key)}
                  <span class="flex-shrink-0 rounded-full bg-warning/20 px-1.5 text-[9px] font-medium text-warning">
                    {issues.length + (duplicateKeys.has(entry.key) ? 1 : 0)}
                  </span>
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
            {@const issues = issuesByKey.get(entry.key) ?? []}
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
                {#if issues.length > 0 || duplicateKeys.has(entry.key)}
                  <span class="flex-shrink-0 rounded-full bg-warning/20 px-1.5 text-[9px] font-medium text-warning">
                    {issues.length + (duplicateKeys.has(entry.key) ? 1 : 0)}
                  </span>
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
    {@const issues = issuesByKey.get(selectedEntry.key) ?? []}
    <div class="flex-shrink-0 border-t border-border bg-bg-secondary">
      <div class="flex items-center justify-between px-3 pt-2 pb-1">
        <h3 class="font-mono text-xs font-semibold text-text-bright">{selectedEntry.key}</h3>
        <button class="text-xs text-text-muted hover:text-text" onclick={() => (selectedKey = null)}>close</button>
      </div>
      {#if issues.length > 0 || duplicateKeys.has(selectedEntry.key)}
        <div class="mx-3 mb-2 space-y-1">
          {#if duplicateKeys.has(selectedEntry.key)}
            <div class="rounded bg-danger/10 px-2 py-1 text-xs text-danger">
              Duplicate key: "{selectedEntry.key}" appears multiple times
            </div>
          {/if}
          {#each issues as issue}
            <div class="rounded px-2 py-1 text-xs {issue.type === 'missing' ? 'bg-warning/10 text-warning' : 'bg-accent/10 text-accent'}">
              {issue.message}
            </div>
          {/each}
        </div>
      {/if}
      <pre class="max-h-40 overflow-y-auto px-3 pb-3 text-xs leading-relaxed text-text">{selectedEntry.raw}</pre>
    </div>
  {/if}
</div>
