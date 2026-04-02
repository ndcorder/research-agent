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
          case "status": {
            const ai = statusOrder.indexOf((a.status ?? null) as any);
            const bi = statusOrder.indexOf((b.status ?? null) as any);
            return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
          }
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

  function shortName(name: string): string {
    // "Last, First" → "Last"
    if (name.includes(",")) return name.split(",")[0].trim();
    const parts = name.trim().split(/\s+/);
    // Single word or org-like name (all caps, or 3+ words) → first word
    if (parts.length === 1) return parts[0];
    if (parts.length >= 3) return parts[0];
    // "First Last" → "Last"
    return parts[parts.length - 1];
  }

  function formatAuthors(authors: string[] | null): string {
    if (!authors || authors.length === 0) return "";
    const first = shortName(authors[0]);
    if (authors.length === 1) return first;
    if (authors.length === 2) return `${first} & ${shortName(authors[1])}`;
    return `${first} et al.`;
  }

  const statusOrder = ["flagged", "needs-replacement", "human-added", "verified", null] as const;
  const statusLabels: Record<string, string> = {
    "verified": "Verified",
    "flagged": "Flagged",
    "needs-replacement": "Needs Replacement",
    "human-added": "Human Added",
  };

  const groupedSources = $derived(() => {
    if (sortBy !== "status") return null;
    const groups: { label: string; status: string | null; sources: typeof filteredSources }[] = [];
    let currentStatus: string | null | undefined = undefined;
    for (const s of filteredSources) {
      const st = s.status ?? null;
      if (st !== currentStatus) {
        currentStatus = st;
        groups.push({ label: statusLabels[st ?? ""] ?? "Unknown", status: st, sources: [] });
      }
      groups[groups.length - 1].sources.push(s);
    }
    return groups;
  });

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
      <div class="flex items-center gap-0.5 border-b border-border/30 px-2 py-1">
        {#each [{ id: "key", label: "Key" }, { id: "year", label: "Year" }, { id: "status", label: "Status" }, { id: "title", label: "Title" }] as opt}
          <button
            class="rounded px-1.5 py-0.5 text-xs transition-colors {sortBy === opt.id ? 'bg-accent/15 text-accent' : 'text-text-muted hover:text-text hover:bg-bg-tertiary/50'}"
            onclick={() => (sortBy = opt.id as typeof sortBy)}
          >{opt.label}</button>
        {/each}
      </div>
      {#snippet sourceCard(source: typeof filteredSources[0])}
        <button
          class="group flex w-full items-start gap-2 border-b border-border/30 px-2 py-2 text-left text-xs transition-all duration-150 hover:bg-bg-tertiary {$selectedSource === source.key ? 'bg-bg-tertiary ring-1 ring-accent/30' : ''}"
          onclick={() => selectSource(source.key)}
          ondblclick={() => openSourceInEditor(source.key)}
        >
          {#if sortBy !== "status"}
            <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full {source.status === 'verified' ? 'bg-success' : source.status === 'flagged' ? 'bg-warning' : source.status === 'needs-replacement' ? 'bg-danger' : source.status === 'human-added' ? 'bg-info' : 'bg-text-muted/50'}"></span>
          {/if}
          <div class="min-w-0 flex-1">
            {#if !source.title || source.title === source.key}
              {#if !formatAuthors(source.authors) && !source.year}
                <div class="flex items-center gap-2">
                  <span class="font-mono text-text-bright">{source.key}</span>
                  <span class="rounded bg-bg-tertiary px-1.5 py-px text-[10px] text-text-muted">unprocessed</span>
                </div>
              {:else}
                <div class="flex items-baseline gap-1">
                  {#if formatAuthors(source.authors)}
                    <span class="truncate font-semibold text-text-bright">{formatAuthors(source.authors)}</span>
                  {/if}
                  {#if source.year}
                    <span class="shrink-0 text-warning/80">{source.year}</span>
                  {/if}
                </div>
                <div class="mt-0.5 flex items-center gap-1.5">
                  <span class="font-mono text-success/50 group-hover:text-success/70">{source.key}</span>
                  <span class="rounded bg-bg-tertiary px-1 py-px text-[10px] text-text-muted">no title</span>
                </div>
              {/if}
            {:else}
              {#if formatAuthors(source.authors) || source.year}
                <div class="flex items-baseline gap-1">
                  {#if formatAuthors(source.authors)}
                    <span class="truncate font-semibold text-text-bright">{formatAuthors(source.authors)}</span>
                  {/if}
                  {#if source.year}
                    <span class="shrink-0 text-warning/80">{source.year}</span>
                  {/if}
                  {#if source.access_level === "abstract-only"}
                    <span class="ml-auto shrink-0 rounded bg-bg-tertiary px-1 py-px text-[10px] text-warning/60">abstract only</span>
                  {:else if source.access_level === "none"}
                    <span class="ml-auto shrink-0 rounded bg-bg-tertiary px-1 py-px text-[10px] text-danger/60">no access</span>
                  {/if}
                </div>
              {/if}
              <div class="line-clamp-2 font-serif leading-snug text-text-bright/80">{source.title}</div>
              <div class="mt-0.5 flex items-center gap-1.5">
                <span class="font-mono text-success/50 group-hover:text-success/70">{source.key}</span>
                {#if source.source_type}
                  <span class="text-border">&middot;</span>
                  <span class="italic text-text-muted/80">{source.source_type}</span>
                {/if}
                {#if source.evidence_for && source.evidence_for.length > 0}
                  <span class="text-border">&middot;</span>
                  <span class="text-info/70">{source.evidence_for.length} claim{source.evidence_for.length === 1 ? '' : 's'}</span>
                {/if}
              </div>
            {/if}
          </div>
        </button>
      {/snippet}

      {#if sortBy === "status"}
        {#each groupedSources() as group (group.label)}
          <div class="sticky top-0 z-10 flex items-center gap-2 border-b border-border/50 bg-bg-secondary px-2 py-1.5">
            <span class="h-2 w-2 rounded-full {group.status === 'verified' ? 'bg-success' : group.status === 'flagged' ? 'bg-warning' : group.status === 'needs-replacement' ? 'bg-danger' : group.status === 'human-added' ? 'bg-info' : 'bg-text-muted/50'}"></span>
            <span class="text-xs font-medium text-text">{group.label}</span>
            <span class="text-xs text-text-muted">({group.sources.length})</span>
          </div>
          {#each group.sources as source (source.key)}
            {@render sourceCard(source)}
          {/each}
        {:else}
          <div class="px-2 py-4 text-center text-xs text-text-muted">No sources found</div>
        {/each}
      {:else}
        {#each filteredSources as source (source.key)}
          {@render sourceCard(source)}
        {:else}
          <div class="px-2 py-4 text-center text-xs text-text-muted">No sources found</div>
        {/each}
      {/if}
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
