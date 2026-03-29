<script lang="ts">
  import { projectDir } from "$lib/stores/project";
  import { listFigures, type FigureInfo } from "$lib/utils/ipc";

  let figures = $state<FigureInfo[]>([]);
  let loading = $state(true);
  let filter = $state<"all" | "used" | "unused">("all");

  const filtered = $derived(
    figures.filter((f) => {
      if (filter === "used") return f.referenced;
      if (filter === "unused") return !f.referenced;
      return true;
    })
  );

  const usedCount = $derived(figures.filter((f) => f.referenced).length);
  const unusedCount = $derived(figures.filter((f) => !f.referenced).length);

  $effect(() => {
    const dir = $projectDir;
    if (!dir) return;
    loading = true;
    listFigures(dir)
      .then((f) => { figures = f; })
      .catch(() => { figures = []; })
      .finally(() => { loading = false; });
  });

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  }

  function getExtIcon(name: string): string {
    const ext = name.split(".").pop()?.toLowerCase() ?? "";
    switch (ext) {
      case "pdf": return "P";
      case "svg": return "S";
      case "tikz": return "T";
      default: return "I";
    }
  }
</script>

<div class="flex h-full flex-col bg-bg">
  <!-- Header -->
  <div class="border-b border-border bg-bg-secondary p-3">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-text-bright">Figures</h3>
      <span class="text-[10px] text-text-muted">
        {figures.length} total ({usedCount} used, {unusedCount} unused)
      </span>
    </div>
    <div class="mt-2 flex gap-1">
      {#each [{ id: "all", label: "All" }, { id: "used", label: "Used" }, { id: "unused", label: "Unused" }] as opt}
        <button
          class="rounded px-2 py-0.5 text-[10px] transition-colors {filter === opt.id ? 'bg-accent/20 text-accent' : 'text-text-muted hover:text-text'}"
          onclick={() => (filter = opt.id as typeof filter)}
        >{opt.label}</button>
      {/each}
    </div>
  </div>

  <!-- Figure grid -->
  <div class="flex-1 overflow-y-auto p-2">
    {#if loading}
      <div class="p-4 text-center text-xs text-text-muted">Loading figures...</div>
    {:else if filtered.length === 0}
      <div class="p-4 text-center text-xs text-text-muted">
        {figures.length === 0 ? "No figures found. Add images to a figures/ directory." : "No figures match this filter."}
      </div>
    {:else}
      <div class="grid grid-cols-2 gap-2">
        {#each filtered as fig (fig.path)}
          <div
            class="group rounded-lg border border-border bg-bg-secondary p-2 transition-colors hover:border-accent/50
              {fig.referenced ? '' : 'opacity-50'}"
          >
            <!-- Thumbnail area -->
            <div class="mb-2 flex h-16 items-center justify-center rounded bg-bg-tertiary text-2xl text-text-muted">
              {getExtIcon(fig.name)}
            </div>
            <!-- Info -->
            <div class="truncate text-[10px] font-medium text-text-bright" title={fig.name}>
              {fig.name}
            </div>
            <div class="flex items-center justify-between text-[10px] text-text-muted">
              <span>{formatSize(fig.size)}</span>
              <span class={fig.referenced ? "text-success" : "text-warning"}>
                {fig.referenced ? "used" : "unused"}
              </span>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
