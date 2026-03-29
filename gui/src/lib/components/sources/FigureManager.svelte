<script lang="ts">
  import { projectDir, texContent, editorGoToLine } from "$lib/stores/project";
  import { listFigures, type FigureInfo } from "$lib/utils/ipc";
  import {
    parseFigureEnvironments,
    parseFigureRefs,
    parseTexSections,
  } from "$lib/utils/latex";

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

  let figureEnvs = $derived(parseFigureEnvironments($texContent));
  let figureRefs = $derived(parseFigureRefs($texContent));
  let sections = $derived(parseTexSections($texContent));

  interface EnrichedFigure extends FigureInfo {
    caption: string;
    label: string | null;
    envLine: number | null;
    referencedInSections: { title: string; line: number }[];
  }

  let enriched = $derived<EnrichedFigure[]>(
    filtered.map((fig) => {
      const stem = fig.name.replace(/\.\w+$/, "");
      const env = figureEnvs.find((e) => e.stem === stem);
      const label = env?.label ?? null;

      // Find sections that reference this figure's label
      let referencedInSections: { title: string; line: number }[] = [];
      if (label) {
        const refs = figureRefs.filter((r) => r.label === label);
        for (const ref of refs) {
          // Find the section containing this reference line
          let containingSection: (typeof sections)[0] | undefined = undefined;
          for (const sec of sections) {
            if (sec.line <= ref.line) containingSection = sec;
            else break;
          }
          if (containingSection && !referencedInSections.some((s) => s.line === containingSection!.line)) {
            referencedInSections.push({ title: containingSection.title, line: containingSection.line });
          }
        }
      }

      return {
        ...fig,
        caption: env?.caption ?? "",
        label,
        envLine: env?.line ?? null,
        referencedInSections,
      };
    })
  );

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
      <span class="text-xs text-text-muted">
        {figures.length} total ({usedCount} used, {unusedCount} unused)
      </span>
    </div>
    <div class="mt-2 flex gap-1">
      {#each [{ id: "all", label: "All" }, { id: "used", label: "Used" }, { id: "unused", label: "Unused" }] as opt}
        <button
          class="rounded px-2 py-0.5 text-xs transition-colors {filter === opt.id ? 'bg-accent/20 text-accent' : 'text-text-muted hover:text-text'}"
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
        {#each enriched as fig (fig.path)}
          <div
            class="group rounded-lg border border-border bg-bg-secondary p-2 transition-colors hover:border-accent/50
              {fig.referenced ? '' : 'opacity-50'}"
          >
            <!-- Thumbnail area -->
            <div class="mb-2 flex h-16 items-center justify-center rounded bg-bg-tertiary text-2xl text-text-muted">
              {getExtIcon(fig.name)}
            </div>
            <!-- Filename -->
            <div class="truncate text-xs font-medium text-text-bright" title={fig.name}>
              {fig.name}
            </div>
            <!-- Caption -->
            {#if fig.caption}
              <p class="mt-0.5 line-clamp-2 text-xs text-text-muted" title={fig.caption}>
                {fig.caption}
              </p>
            {/if}
            <!-- Meta row -->
            <div class="mt-1 flex items-center justify-between text-xs text-text-muted">
              <span>{formatSize(fig.size)}</span>
              <span class={fig.referenced ? "text-success" : "text-warning"}>
                {fig.referenced ? "used" : "unused"}
              </span>
            </div>
            <!-- Section references -->
            {#if fig.referencedInSections.length > 0}
              <div class="mt-1 flex flex-wrap gap-1">
                {#each fig.referencedInSections as sec}
                  <button
                    class="rounded bg-accent/10 px-1 py-0.5 text-[9px] text-accent hover:bg-accent/20"
                    title="Go to {sec.title}"
                    onclick={() => editorGoToLine.set(sec.line)}
                  >
                    {sec.title}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
