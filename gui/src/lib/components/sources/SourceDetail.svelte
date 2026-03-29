<script lang="ts">
  import { sources, selectedSource, projectDir } from "$lib/stores/project";
  import { readFile, updateSourceStatus, appendHumanNotes } from "$lib/utils/ipc";
  import { parseFrontmatter } from "$lib/utils/frontmatter";
  import type { SourceMeta } from "$lib/types";

  let source = $derived<SourceMeta | undefined>(
    $sources.find((s) => s.key === $selectedSource)
  );

  let frontmatter = $state<Record<string, unknown>>({});
  let bodyContent = $state("");
  let loading = $state(false);
  let noteText = $state("");
  let saving = $state(false);

  $effect(() => {
    const key = $selectedSource;
    if (!key || !source) {
      frontmatter = {};
      bodyContent = "";
      return;
    }

    loading = true;
    readFile(source.path)
      .then((raw) => {
        const parsed = parseFrontmatter(raw);
        frontmatter = parsed.frontmatter;
        bodyContent = parsed.content;
      })
      .catch(() => {
        frontmatter = {};
        bodyContent = "(Failed to load source file)";
      })
      .finally(() => {
        loading = false;
      });
  });

  async function setStatus(status: string) {
    if (!source) return;
    saving = true;
    try {
      await updateSourceStatus(source.path, status);
      // Update local store
      sources.update((all) =>
        all.map((s) => (s.key === source!.key ? { ...s, status } : s))
      );
    } finally {
      saving = false;
    }
  }

  async function addNote() {
    if (!source || !noteText.trim()) return;
    saving = true;
    try {
      await appendHumanNotes(source.path, noteText.trim());
      bodyContent += `\n\n> **Human note:** ${noteText.trim()}`;
      noteText = "";
    } finally {
      saving = false;
    }
  }

  function statusColor(status: string | null): string {
    switch (status) {
      case "verified":
        return "bg-success/20 text-success";
      case "flagged":
        return "bg-warning/20 text-warning";
      case "needs-replacement":
        return "bg-danger/20 text-danger";
      case "human-added":
        return "bg-info/20 text-info";
      default:
        return "bg-bg-tertiary text-text-muted";
    }
  }

  function renderMarkdown(text: string): string {
    return text
      .split("\n\n")
      .map((block) => {
        const trimmed = block.trim();
        if (!trimmed) return "";

        // Headers
        if (trimmed.startsWith("#### "))
          return `<h4 class="text-sm font-semibold text-text-bright mt-4 mb-1">${trimmed.slice(5)}</h4>`;
        if (trimmed.startsWith("### "))
          return `<h3 class="text-sm font-bold text-text-bright mt-4 mb-1">${trimmed.slice(4)}</h3>`;
        if (trimmed.startsWith("## "))
          return `<h2 class="text-base font-bold text-text-bright mt-5 mb-2">${trimmed.slice(3)}</h2>`;
        if (trimmed.startsWith("# "))
          return `<h1 class="text-lg font-bold text-text-bright mt-5 mb-2">${trimmed.slice(2)}</h1>`;

        // Blockquotes
        if (trimmed.startsWith("> ")) {
          const quoteContent = trimmed
            .split("\n")
            .map((l) => l.replace(/^>\s?/, ""))
            .join("<br/>");
          return `<blockquote class="border-l-2 border-accent pl-3 my-2 text-text-muted italic">${inlineFormat(quoteContent)}</blockquote>`;
        }

        // Paragraph
        return `<p class="my-1.5 leading-relaxed">${inlineFormat(trimmed)}</p>`;
      })
      .join("\n");
  }

  function inlineFormat(text: string): string {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong class="text-text-bright">$1</strong>')
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, '<code class="rounded bg-bg-tertiary px-1 py-0.5 text-xs text-accent">$1</code>');
  }
</script>

{#if !$selectedSource || !source}
  <div class="flex h-full items-center justify-center bg-bg p-8">
    <div class="text-center">
      <div class="mb-2 text-3xl text-text-muted">&#9723;</div>
      <p class="text-sm text-text-muted">Select a source from the sidebar to view details</p>
    </div>
  </div>
{:else if loading}
  <div class="flex h-full items-center justify-center bg-bg">
    <div class="text-sm text-text-muted">Loading source...</div>
  </div>
{:else}
  <div class="flex h-full flex-col overflow-hidden bg-bg">
    <!-- Metadata header -->
    <div class="flex-shrink-0 border-b border-border bg-bg-secondary p-4">
      <div class="mb-2 flex items-start justify-between gap-3">
        <h2 class="text-base font-semibold leading-tight text-text-bright">
          {source.title || source.key}
        </h2>
        <span class="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-medium {statusColor(source.status)}">
          {source.status || "unknown"}
        </span>
      </div>

      {#if source.authors?.length}
        <p class="mb-1 text-xs text-text-muted">
          {source.authors.join(", ")}
          {#if source.year}&middot; {source.year}{/if}
        </p>
      {/if}

      <!-- Links and access info -->
      <div class="mb-2 flex flex-wrap items-center gap-2">
        {#if source.access_level}
          <span class="rounded-full px-2 py-0.5 text-[10px] font-medium {source.access_level === 'FULL-TEXT' ? 'bg-success/20 text-success' : source.access_level === 'ABSTRACT-ONLY' ? 'bg-warning/20 text-warning' : 'bg-bg-tertiary text-text-muted'}">
            {source.access_level}
          </span>
        {/if}
        {#if source.source_type}
          <span class="rounded-full bg-bg-tertiary px-2 py-0.5 text-[10px] text-text-muted">{source.source_type}</span>
        {/if}
        {#if source.url}
          <a href={source.url} target="_blank" rel="noopener" class="text-[10px] text-accent hover:underline">Open URL &#x2197;</a>
        {/if}
        {#if source.doi}
          <a href="https://doi.org/{source.doi}" target="_blank" rel="noopener" class="text-[10px] text-accent hover:underline">DOI &#x2197;</a>
        {/if}
        {#if frontmatter.doi && !source.doi}
          <a href="https://doi.org/{frontmatter.doi}" target="_blank" rel="noopener" class="text-[10px] text-accent hover:underline">DOI &#x2197;</a>
        {/if}
      </div>

      {#if source.tags?.length}
        <div class="flex flex-wrap gap-1">
          {#each source.tags as tag}
            <span class="rounded-full bg-bg-tertiary px-2 py-0.5 text-xs text-text-muted">{tag}</span>
          {/each}
        </div>
      {/if}

      <!-- Action buttons -->
      <div class="mt-3 flex gap-2">
        <button
          class="rounded bg-warning/15 px-2.5 py-1 text-xs font-medium text-warning transition-colors hover:bg-warning/25 disabled:opacity-50"
          onclick={() => setStatus("flagged")}
          disabled={saving}
        >
          Flag
        </button>
        <button
          class="rounded bg-danger/15 px-2.5 py-1 text-xs font-medium text-danger transition-colors hover:bg-danger/25 disabled:opacity-50"
          onclick={() => setStatus("needs-replacement")}
          disabled={saving}
        >
          Needs Replacement
        </button>
        <button
          class="rounded bg-success/15 px-2.5 py-1 text-xs font-medium text-success transition-colors hover:bg-success/25 disabled:opacity-50"
          onclick={() => setStatus("verified")}
          disabled={saving}
        >
          Verify
        </button>
      </div>
    </div>

    <!-- Body content -->
    <div class="flex-1 overflow-y-auto p-4 text-sm text-text">
      {@html renderMarkdown(bodyContent)}
    </div>

    <!-- Human notes section -->
    <div class="flex-shrink-0 border-t border-border bg-bg-secondary p-4">
      <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">Human Notes</h3>
      <textarea
        bind:value={noteText}
        placeholder="Add a note about this source..."
        rows="3"
        class="w-full resize-none rounded bg-bg-tertiary p-2 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
      ></textarea>
      <div class="mt-2 flex justify-end">
        <button
          class="rounded bg-accent px-3 py-1 text-xs font-medium text-bg transition-colors hover:bg-accent/80 disabled:opacity-50"
          onclick={addNote}
          disabled={saving || !noteText.trim()}
        >
          Add Note
        </button>
      </div>
    </div>
  </div>
{/if}
