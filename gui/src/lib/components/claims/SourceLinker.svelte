<script lang="ts">
  import { sources } from "$lib/stores/project";
  import type { SourceMeta } from "$lib/types";

  interface Props {
    evidenceSources: string;
    onUpdate: (newEvidence: string) => void;
  }

  let { evidenceSources, onUpdate }: Props = $props();

  let query = $state("");
  let showResults = $state(false);

  // Source being linked — shows the relationship picker
  let linking = $state<SourceMeta | null>(null);
  let linkAccess = $state<"FT" | "AO" | "MO">("FT");
  let linkType = $state<"direct" | "indirect">("direct");

  // Parse existing linked source keys from evidence string
  let linkedKeys = $derived<Set<string>>(
    new Set(
      evidenceSources
        .split(",")
        .map((e) => e.trim().split(/\s/)[0])
        .filter(Boolean)
    )
  );

  // Filter sources by query, exclude already linked
  let results = $derived<SourceMeta[]>(
    query.length < 1
      ? []
      : $sources
          .filter((s) => !linkedKeys.has(s.key))
          .filter((s) => {
            const q = query.toLowerCase();
            return (
              s.key.toLowerCase().includes(q) ||
              (s.title?.toLowerCase().includes(q) ?? false) ||
              (s.authors?.some((a) => a.toLowerCase().includes(q)) ?? false)
            );
          })
          .slice(0, 8)
  );

  // Parse evidence entries for display
  interface EvidenceEntry {
    key: string;
    access: string;
    type: string;
    score: string;
    raw: string;
  }

  let entries = $derived<EvidenceEntry[]>(
    evidenceSources
      .split(",")
      .map((e) => e.trim())
      .filter(Boolean)
      .map((raw) => {
        const m = raw.match(/^(\S+)\s*\((\w+),(\w+)\)=(.+)$/);
        if (!m) return { key: raw.split(/\s/)[0], access: "?", type: "?", score: "?", raw };
        return { key: m[1], access: m[2], type: m[3], score: m[4], raw };
      })
  );

  function computeScore(access: string, type: string): number {
    const base = access === "FT" ? 3 : access === "AO" ? 1 : 0;
    const mod = type === "direct" ? 1 : 0;
    return base + mod;
  }

  function accessFromSource(src: SourceMeta): "FT" | "AO" | "MO" {
    const al = (src.access_level ?? "").toUpperCase();
    if (al.includes("FULL")) return "FT";
    if (al.includes("ABSTRACT")) return "AO";
    if (al.includes("METADATA")) return "MO";
    return "FT";
  }

  function startLink(src: SourceMeta) {
    linking = src;
    linkAccess = accessFromSource(src);
    linkType = "direct";
    showResults = false;
    query = "";
  }

  function confirmLink() {
    if (!linking) return;
    const score = computeScore(linkAccess, linkType);
    const notation = `${linking.key} (${linkAccess},${linkType})=${score}`;
    const updated = evidenceSources ? `${evidenceSources}, ${notation}` : notation;
    onUpdate(updated);
    linking = null;
  }

  function unlinkSource(key: string) {
    const updated = entries
      .filter((e) => e.key !== key)
      .map((e) => e.raw)
      .join(", ");
    onUpdate(updated);
  }
</script>

<div class="space-y-3">
  <!-- Existing linked sources -->
  {#if entries.length > 0}
    <div class="space-y-1">
      {#each entries as entry}
        <div
          class="flex items-center justify-between rounded bg-bg-secondary px-2.5 py-1.5"
        >
          <div class="min-w-0 flex-1">
            <span class="text-xs font-medium text-text-bright">{entry.key}</span>
            <span class="ml-1.5 text-xs text-text-muted">
              {entry.access}/{entry.type} = {entry.score}
            </span>
          </div>
          <button
            class="ml-2 flex-shrink-0 rounded px-1.5 py-0.5 text-xs text-danger hover:bg-danger/10"
            onclick={() => unlinkSource(entry.key)}
          >
            Unlink
          </button>
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-xs text-text-muted italic">No sources linked</p>
  {/if}

  <!-- Link relationship picker (shown when a source is selected) -->
  {#if linking}
    <div class="rounded border border-accent/30 bg-bg-secondary p-3">
      <p class="mb-2 text-xs font-medium text-text-bright">
        Link: {linking.title || linking.key}
      </p>
      <div class="flex items-center gap-3">
        <label class="text-xs text-text-muted">
          Access
          <select
            bind:value={linkAccess}
            class="ml-1 rounded bg-bg-tertiary px-2 py-1 text-xs text-text outline-none"
          >
            <option value="FT">Full-text</option>
            <option value="AO">Abstract-only</option>
            <option value="MO">Metadata-only</option>
          </select>
        </label>
        <label class="text-xs text-text-muted">
          Relationship
          <select
            bind:value={linkType}
            class="ml-1 rounded bg-bg-tertiary px-2 py-1 text-xs text-text outline-none"
          >
            <option value="direct">Direct</option>
            <option value="indirect">Indirect</option>
          </select>
        </label>
      </div>
      <div class="mt-2 flex items-center justify-between">
        <span class="text-xs text-text-muted">
          Score: {computeScore(linkAccess, linkType)}
        </span>
        <div class="flex gap-2">
          <button
            class="rounded px-2 py-1 text-xs text-text-muted hover:bg-bg-tertiary"
            onclick={() => (linking = null)}
          >
            Cancel
          </button>
          <button
            class="rounded bg-accent px-2 py-1 text-xs font-medium text-bg hover:bg-accent/80"
            onclick={confirmLink}
          >
            Link
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Search input -->
  <div class="relative">
    <input
      type="text"
      bind:value={query}
      onfocus={() => (showResults = true)}
      onblur={() => setTimeout(() => (showResults = false), 200)}
      placeholder="Search sources to link..."
      class="w-full rounded bg-bg-tertiary px-3 py-1.5 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
    />
    {#if showResults && results.length > 0}
      <div
        class="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-y-auto rounded border border-border bg-bg-secondary shadow-lg"
      >
        {#each results as src}
          <button
            class="flex w-full flex-col px-3 py-2 text-left hover:bg-bg-tertiary"
            onmousedown={() => startLink(src)}
          >
            <span class="text-xs font-medium text-text-bright">
              {src.key}
              {#if src.title}
                <span class="font-normal text-text-muted"> — {src.title}</span>
              {/if}
            </span>
            {#if src.authors?.length}
              <span class="text-xs text-text-muted">
                {src.authors.join(", ")}{src.year ? ` (${src.year})` : ""}
              </span>
            {/if}
            {#if src.access_level}
              <span class="mt-0.5 text-xs text-text-muted/60">{src.access_level}</span>
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>
