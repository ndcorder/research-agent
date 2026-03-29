<script lang="ts">
  import { onDestroy } from "svelte";
  import type { SourceMeta, ClaimMeta } from "$lib/types";
  import { selectedSource, selectedClaim, rightPanel } from "$lib/stores/project";
  import Badge from "$lib/components/ui/Badge.svelte";

  let {
    sources,
    claims,
  }: {
    sources: SourceMeta[];
    claims: ClaimMeta[];
  } = $props();

  let activeTab = $state<"sources" | "claims">("sources");
  let filterText = $state("");
  let filterDebounced = $state("");
  let filterTimeout: ReturnType<typeof setTimeout> | null = null;

  type SortDir = "asc" | "desc";
  let sourceSortCol = $state<string>("key");
  let sourceSortDir = $state<SortDir>("asc");
  let claimSortCol = $state<string>("statement");
  let claimSortDir = $state<SortDir>("asc");

  onDestroy(() => {
    if (filterTimeout) clearTimeout(filterTimeout);
  });

  function onFilterInput() {
    if (filterTimeout) clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => {
      filterDebounced = filterText;
    }, 200);
  }

  function toggleSourceSort(col: string) {
    if (sourceSortCol === col) {
      sourceSortDir = sourceSortDir === "asc" ? "desc" : "asc";
    } else {
      sourceSortCol = col;
      sourceSortDir = "asc";
    }
  }

  function toggleClaimSort(col: string) {
    if (claimSortCol === col) {
      claimSortDir = claimSortDir === "asc" ? "desc" : "asc";
    } else {
      claimSortCol = col;
      claimSortDir = "asc";
    }
  }

  function sourceClaimCount(s: SourceMeta): number {
    return s.evidence_for?.length ?? 0;
  }

  function claimSourceCount(c: ClaimMeta): number {
    if (!c.evidence_sources) return 0;
    return c.evidence_sources.split(",").filter((s) => s.trim()).length;
  }

  function statusVariant(status: string | null): "success" | "warning" | "danger" | "info" | "muted" {
    switch (status) {
      case "verified": return "success";
      case "flagged": return "warning";
      case "needs-replacement": return "danger";
      case "human-added": return "info";
      default: return "muted";
    }
  }

  function confidenceVariant(confidence: string): "success" | "warning" | "danger" | "info" | "muted" {
    switch (confidence.toUpperCase()) {
      case "HIGH": return "success";
      case "MODERATE": return "warning";
      case "LOW": return "danger";
      default: return "muted";
    }
  }

  const filteredSources = $derived.by(() => {
    const q = filterDebounced.toLowerCase();
    let items = sources;
    if (q) {
      items = items.filter((s) => {
        return (
          s.key.toLowerCase().includes(q) ||
          (s.title && s.title.toLowerCase().includes(q)) ||
          (s.year !== null && String(s.year).includes(q)) ||
          (s.status && s.status.toLowerCase().includes(q)) ||
          (s.access_level && s.access_level.toLowerCase().includes(q)) ||
          (s.tags && s.tags.some((t) => t.toLowerCase().includes(q)))
        );
      });
    }
    const col = sourceSortCol;
    const dir = sourceSortDir === "asc" ? 1 : -1;
    return [...items].sort((a, b) => {
      let cmp = 0;
      switch (col) {
        case "key":
          cmp = a.key.localeCompare(b.key);
          break;
        case "title":
          cmp = (a.title ?? "").localeCompare(b.title ?? "");
          break;
        case "year":
          cmp = (a.year ?? 0) - (b.year ?? 0);
          break;
        case "status":
          cmp = (a.status ?? "").localeCompare(b.status ?? "");
          break;
        case "access":
          cmp = (a.access_level ?? "").localeCompare(b.access_level ?? "");
          break;
        case "claims":
          cmp = sourceClaimCount(a) - sourceClaimCount(b);
          break;
        case "tags":
          cmp = (a.tags?.join(",") ?? "").localeCompare(b.tags?.join(",") ?? "");
          break;
      }
      return cmp * dir;
    });
  });

  const filteredClaims = $derived.by(() => {
    const q = filterDebounced.toLowerCase();
    let items = claims;
    if (q) {
      items = items.filter((c) => {
        return (
          c.statement.toLowerCase().includes(q) ||
          c.section.toLowerCase().includes(q) ||
          c.confidence.toLowerCase().includes(q) ||
          String(c.evidence_density).includes(q) ||
          (c.strength?.toLowerCase().includes(q) ?? false) ||
          (c.evidence_sources?.toLowerCase().includes(q) ?? false)
        );
      });
    }
    const col = claimSortCol;
    const dir = claimSortDir === "asc" ? 1 : -1;
    return [...items].sort((a, b) => {
      let cmp = 0;
      switch (col) {
        case "statement":
          cmp = a.statement.localeCompare(b.statement);
          break;
        case "section":
          cmp = a.section.localeCompare(b.section);
          break;
        case "confidence":
          cmp = a.confidence.localeCompare(b.confidence);
          break;
        case "density":
          cmp = a.evidence_density - b.evidence_density;
          break;
        case "sources":
          cmp = claimSourceCount(a) - claimSourceCount(b);
          break;
        case "strength":
          cmp = (a.strength ?? "").localeCompare(b.strength ?? "");
          break;
      }
      return cmp * dir;
    });
  });

  function selectSource(key: string) {
    selectedSource.set(key);
    rightPanel.set("source");
  }

  function selectClaim(id: string) {
    selectedClaim.set(id);
    rightPanel.set("claim");
  }

  function sortArrow(active: boolean, dir: SortDir): string {
    if (!active) return "";
    return dir === "asc" ? " \u25B2" : " \u25BC";
  }

  const sourceColumns = [
    { id: "key", label: "Key" },
    { id: "title", label: "Title" },
    { id: "year", label: "Year" },
    { id: "status", label: "Status" },
    { id: "access", label: "Access" },
    { id: "claims", label: "Claims" },
    { id: "tags", label: "Tags" },
  ] as const;

  const claimColumns = [
    { id: "statement", label: "Statement" },
    { id: "section", label: "Section" },
    { id: "confidence", label: "Confidence" },
    { id: "density", label: "Density" },
    { id: "sources", label: "Sources" },
    { id: "strength", label: "Strength" },
  ] as const;
</script>

<div class="flex h-full flex-col">
  <!-- Tab toggle + filter -->
  <div class="flex items-center gap-2 border-b border-border px-3 py-2">
    <button
      class="rounded px-2 py-1 text-xs transition-colors {activeTab === 'sources'
        ? 'bg-accent/20 text-accent'
        : 'text-text-muted hover:text-text'}"
      onclick={() => (activeTab = "sources")}
    >
      Sources ({sources.length})
    </button>
    <button
      class="rounded px-2 py-1 text-xs transition-colors {activeTab === 'claims'
        ? 'bg-accent/20 text-accent'
        : 'text-text-muted hover:text-text'}"
      onclick={() => (activeTab = "claims")}
    >
      Claims ({claims.length})
    </button>
    <input
      type="text"
      placeholder="Filter..."
      bind:value={filterText}
      oninput={onFilterInput}
      class="ml-auto bg-bg-tertiary border border-border rounded px-2 py-1 text-xs text-text placeholder:text-text-muted outline-none focus:ring-1 focus:ring-accent"
    />
  </div>

  <!-- Table -->
  <div class="flex-1 overflow-auto">
    {#if activeTab === "sources"}
      <table class="w-full text-xs">
        <thead>
          <tr>
            {#each sourceColumns as col}
              <th
                class="bg-bg-secondary text-text-muted font-medium uppercase tracking-wider sticky top-0 cursor-pointer select-none px-3 py-2 text-left"
                onclick={() => toggleSourceSort(col.id)}
              >
                {col.label}{sortArrow(sourceSortCol === col.id, sourceSortDir)}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each filteredSources as source (source.key)}
            <tr
              class="cursor-pointer border-b border-border/50 hover:bg-bg-tertiary transition-colors {$selectedSource === source.key ? 'bg-accent/10' : ''}"
              onclick={() => selectSource(source.key)}
            >
              <td class="px-3 py-1.5 text-text-bright whitespace-nowrap">{source.key}</td>
              <td class="px-3 py-1.5 max-w-48 truncate" title={source.title ?? ""}>{source.title ?? ""}</td>
              <td class="px-3 py-1.5 whitespace-nowrap">{source.year ?? ""}</td>
              <td class="px-3 py-1.5">
                {#if source.status}
                  <Badge variant={statusVariant(source.status)}>{source.status}</Badge>
                {/if}
              </td>
              <td class="px-3 py-1.5 whitespace-nowrap">{source.access_level ?? ""}</td>
              <td class="px-3 py-1.5 text-center">{sourceClaimCount(source)}</td>
              <td class="px-3 py-1.5 max-w-32 truncate text-text-muted">{source.tags?.join(", ") ?? ""}</td>
            </tr>
          {:else}
            <tr>
              <td colspan="7" class="px-3 py-6 text-center text-text-muted">No sources match filter</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <table class="w-full text-xs">
        <thead>
          <tr>
            {#each claimColumns as col}
              <th
                class="bg-bg-secondary text-text-muted font-medium uppercase tracking-wider sticky top-0 cursor-pointer select-none px-3 py-2 text-left"
                onclick={() => toggleClaimSort(col.id)}
              >
                {col.label}{sortArrow(claimSortCol === col.id, claimSortDir)}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each filteredClaims as claim (claim.id)}
            <tr
              class="cursor-pointer border-b border-border/50 hover:bg-bg-tertiary transition-colors {$selectedClaim === claim.id ? 'bg-accent/10' : ''}"
              onclick={() => selectClaim(claim.id)}
            >
              <td class="px-3 py-1.5 max-w-64 truncate" title={claim.statement}>
                {claim.statement.length > 60 ? claim.statement.slice(0, 60) + "\u2026" : claim.statement}
              </td>
              <td class="px-3 py-1.5 whitespace-nowrap">{claim.section}</td>
              <td class="px-3 py-1.5">
                <Badge variant={confidenceVariant(claim.confidence)}>{claim.confidence}</Badge>
              </td>
              <td class="px-3 py-1.5 text-center">{claim.evidence_density}</td>
              <td class="px-3 py-1.5 text-center">{claimSourceCount(claim)}</td>
              <td class="px-3 py-1.5 whitespace-nowrap">{claim.strength ?? ""}</td>
            </tr>
          {:else}
            <tr>
              <td colspan="6" class="px-3 py-6 text-center text-text-muted">No claims match filter</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
