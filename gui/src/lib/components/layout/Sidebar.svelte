<script lang="ts">
  import { sources, claims, selectedSource, selectedClaim, rightPanel, texSections, editorGoToLine, projectDir, openFileRequest } from "$lib/stores/project";
  import CreateSourceDialog from "$lib/components/sources/CreateSourceDialog.svelte";
  import FileTree from "$lib/components/layout/FileTree.svelte";
  import { searchSources, type SearchResult } from "$lib/utils/ipc";

  let searchQuery = $state("");
  let activeSection = $state<"files" | "sources" | "claims" | "sections" | "search">("sources");
  let searchResults = $state<SearchResult[]>([]);
  let isSearching = $state(false);
  let searchTimeout: ReturnType<typeof setTimeout> | null = null;

  function onSearchInput() {
    if (activeSection !== "search") activeSection = "search";
    if (searchTimeout) clearTimeout(searchTimeout);
    if (!searchQuery.trim()) {
      searchResults = [];
      return;
    }
    isSearching = true;
    searchTimeout = setTimeout(async () => {
      const dir = $projectDir;
      if (!dir || !searchQuery.trim()) {
        searchResults = [];
        isSearching = false;
        return;
      }
      try {
        searchResults = await searchSources(dir, searchQuery.trim());
      } catch {
        searchResults = [];
      }
      isSearching = false;
    }, 300);
  }
  let showCreateSource = $state(false);
  let sortBy = $state<"key" | "year" | "status" | "title">("key");

  const filteredSources = $derived(
    $sources
      .filter((s) => {
        if (!searchQuery || activeSection !== "sources") return true;
        const q = searchQuery.toLowerCase();
        return (
          s.key.toLowerCase().includes(q) ||
          (s.title && s.title.toLowerCase().includes(q)) ||
          (s.tags && s.tags.some((t) => t.toLowerCase().includes(q)))
        );
      })
      .sort((a, b) => {
        switch (sortBy) {
          case "year":
            return (b.year ?? 0) - (a.year ?? 0);
          case "status":
            return (a.status ?? "z").localeCompare(b.status ?? "z");
          case "title":
            return (a.title ?? a.key).localeCompare(b.title ?? b.key);
          default:
            return a.key.localeCompare(b.key);
        }
      })
  );

  function selectSource(key: string) {
    selectedSource.set(key);
    rightPanel.set("source");
  }

  function openSourceInEditor(key: string) {
    const path = `research/sources/${key}.md`;
    openFileRequest.set({ name: `${key}.md`, path });
  }

  function selectClaim(id: string) {
    selectedClaim.set(id);
    rightPanel.set("claim");
  }

  function statusColor(status: string | null): string {
    switch (status) {
      case "verified":
        return "text-success";
      case "flagged":
        return "text-warning";
      case "needs-replacement":
        return "text-danger";
      case "human-added":
        return "text-info";
      default:
        return "text-text-muted";
    }
  }

  function statusIcon(status: string | null): string {
    switch (status) {
      case "verified":
        return "\u2713";
      case "flagged":
        return "\u2691";
      case "needs-replacement":
        return "?";
      case "human-added":
        return "+";
      default:
        return "\u00b7";
    }
  }
</script>

<div class="flex h-full flex-col bg-bg-secondary">
  <!-- Search -->
  <div class="p-2">
    <input
      type="text"
      placeholder="Search..."
      bind:value={searchQuery}
      oninput={onSearchInput}
      class="w-full rounded bg-bg-tertiary px-2 py-1 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
    />
  </div>

  <!-- Section tabs -->
  <div class="flex items-center border-b border-border px-2">
    {#each ["files", "sources", "claims", "sections", "search"] as section}
      <button
        class="px-2 py-1 text-xs transition-colors {activeSection === section
          ? 'border-b-2 border-accent text-text-bright'
          : 'text-text-muted hover:text-text'}"
        onclick={() => (activeSection = section as typeof activeSection)}
      >
        {section.charAt(0).toUpperCase() + section.slice(1)}
        {#if section === "sources"}
          <span class="ml-1 text-text-muted">({$sources.length})</span>
        {:else if section === "claims"}
          <span class="ml-1 text-text-muted">({$claims.length})</span>
        {:else if section === "sections"}
          <span class="ml-1 text-text-muted">({$texSections.length})</span>
        {:else if section === "search" && searchResults.length > 0}
          <span class="ml-1 text-text-muted">({searchResults.length})</span>
        {/if}
      </button>
    {/each}
    <button
      class="ml-auto rounded px-1.5 py-0.5 text-xs text-text-muted transition-colors hover:bg-bg-tertiary hover:text-accent"
      onclick={() => (showCreateSource = true)}
      title="Add source"
    >+</button>
  </div>

  <!-- List -->
  <div class="flex-1 overflow-y-auto p-1">
    {#if activeSection === "files"}
      <FileTree />
    {:else if activeSection === "sources"}
      <div class="flex items-center gap-1 px-2 pb-1">
        <span class="text-xs text-text-muted">Sort:</span>
        {#each [{ id: "key", label: "Key" }, { id: "year", label: "Year" }, { id: "status", label: "Status" }, { id: "title", label: "Title" }] as opt}
          <button
            class="rounded px-1 py-px text-xs transition-colors {sortBy === opt.id ? 'bg-accent/20 text-accent' : 'text-text-muted hover:text-text'}"
            onclick={() => (sortBy = opt.id as typeof sortBy)}
          >{opt.label}</button>
        {/each}
      </div>
      {#each filteredSources as source (source.key)}
        <button
          class="flex w-full items-start gap-2 rounded px-2 py-1.5 text-left text-xs transition-all duration-150 hover:bg-bg-tertiary hover:translate-x-0.5 {$selectedSource === source.key ? 'bg-bg-tertiary' : ''}"
          onclick={() => selectSource(source.key)}
          ondblclick={() => openSourceInEditor(source.key)}
        >
          <span class="mt-0.5 {statusColor(source.status)}">{statusIcon(source.status)}</span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-text-bright">{source.title || source.key}</div>
            <div class="truncate text-text-muted">
              {source.authors?.slice(0, 2).join(", ") || ""}
              {source.year ? ` (${source.year})` : ""}
            </div>
          </div>
        </button>
      {:else}
        <div class="px-2 py-4 text-center text-xs text-text-muted">No sources found</div>
      {/each}
    {:else if activeSection === "claims"}
      {#each $claims as claim (claim.id)}
        <button
          class="flex w-full items-start gap-2 rounded px-2 py-1.5 text-left text-xs transition-all duration-150 hover:bg-bg-tertiary hover:translate-x-0.5"
          onclick={() => selectClaim(claim.id)}
        >
          <span class="mt-0.5 text-accent">&diamond;</span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-text-bright">{claim.statement}</div>
            <div class="text-text-muted">
              {claim.confidence} &middot; {claim.evidence_density} sources
            </div>
          </div>
        </button>
      {:else}
        <div class="px-2 py-4 text-center text-xs text-text-muted">No claims found</div>
      {/each}
    {:else if activeSection === "search"}
      {#if isSearching}
        <div class="px-2 py-4 text-center text-xs text-text-muted">Searching...</div>
      {:else if searchQuery && searchResults.length === 0}
        <div class="px-2 py-4 text-center text-xs text-text-muted">No results</div>
      {:else}
        {#each searchResults as result (result.source_key + '-' + result.line_number)}
          <button
            class="flex w-full flex-col gap-0.5 rounded px-2 py-1.5 text-left text-xs transition-all duration-150 hover:bg-bg-tertiary"
            onclick={() => selectSource(result.source_key)}
            ondblclick={() => openSourceInEditor(result.source_key)}
          >
            <div class="flex items-center gap-1">
              <span class="font-medium text-text-bright">{result.source_title || result.source_key}</span>
              <span class="text-text-muted">L{result.line_number}</span>
            </div>
            <div class="truncate text-text-muted">{result.line_content.trim()}</div>
          </button>
        {/each}
      {/if}
    {:else}
      {#each $texSections as section (section.line)}
        <button
          class="flex w-full items-center gap-1 rounded px-2 py-1.5 text-left text-xs transition-all duration-150 hover:bg-bg-tertiary hover:translate-x-0.5"
          style="padding-left: {8 + (section.level - 1) * 12}px"
          onclick={() => editorGoToLine.set(section.line)}
        >
          <span class="text-text-muted">{section.level === 1 ? '\u00a7' : section.level === 2 ? '\u2022' : '\u2013'}</span>
          <span class="truncate {section.level === 1 ? 'text-text-bright font-medium' : 'text-text'}">{section.title}</span>
          <span class="ml-auto text-text-muted">L{section.line}</span>
        </button>
      {:else}
        <div class="px-2 py-4 text-center text-xs text-text-muted">Open main.tex to see sections</div>
      {/each}
    {/if}
  </div>
</div>

<CreateSourceDialog open={showCreateSource} onclose={() => (showCreateSource = false)} />
