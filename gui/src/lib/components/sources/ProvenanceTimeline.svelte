<script lang="ts">
  import { projectDir } from "$lib/stores/project";
  import { readProvenance } from "$lib/utils/ipc";

  type ProvenanceEntry = Record<string, unknown>;
  type FilterType = "all" | "writes" | "revisions" | "cuts";

  let entries = $state<ProvenanceEntry[]>([]);
  let loading = $state(false);
  let error = $state("");
  let activeFilter = $state<FilterType>("all");
  let timelineEl = $state<HTMLDivElement | null>(null);

  const MAX_ENTRIES = 200;

  const filterConfig: { id: FilterType; label: string }[] = [
    { id: "all", label: "All" },
    { id: "writes", label: "Writes" },
    { id: "revisions", label: "Revisions" },
    { id: "cuts", label: "Cuts" },
  ];

  const actionMatches: Record<FilterType, string[]> = {
    all: [],
    writes: ["write", "add"],
    revisions: ["revise"],
    cuts: ["cut", "remove"],
  };

  let filtered = $derived<ProvenanceEntry[]>(() => {
    if (activeFilter === "all") return entries.slice(-MAX_ENTRIES);
    const allowed = actionMatches[activeFilter];
    return entries
      .filter((e) => {
        const action = String(e.action ?? "").toLowerCase();
        return allowed.some((a) => action.includes(a));
      })
      .slice(-MAX_ENTRIES);
  });

  function actionColor(action: string): string {
    const a = action.toLowerCase();
    if (a === "write" || a === "add") return "bg-success/20 text-success border-success/30";
    if (a === "revise") return "bg-info/20 text-info border-info/30";
    if (a === "cut") return "bg-warning/20 text-warning border-warning/30";
    if (a === "remove") return "bg-danger/20 text-danger border-danger/30";
    return "bg-bg-tertiary text-text-muted border-border";
  }

  function timelineColor(action: string): string {
    const a = action.toLowerCase();
    if (a === "write" || a === "add") return "bg-success";
    if (a === "revise") return "bg-info";
    if (a === "cut") return "bg-warning";
    if (a === "remove") return "bg-danger";
    return "bg-text-muted";
  }

  function formatTime(timestamp: unknown): string {
    if (!timestamp) return "";
    const date = new Date(String(timestamp));
    if (isNaN(date.getTime())) return String(timestamp);

    const now = Date.now();
    const diff = now - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  async function loadEntries() {
    const dir = $projectDir;
    if (!dir) return;
    loading = true;
    error = "";
    try {
      entries = await readProvenance(dir);
    } catch (e) {
      entries = [];
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  function scrollToBottom() {
    if (timelineEl) {
      timelineEl.scrollTop = timelineEl.scrollHeight;
    }
  }

  // Load on mount and when project changes
  $effect(() => {
    const dir = $projectDir;
    if (dir) {
      loadEntries();
    } else {
      entries = [];
    }
  });

  // Auto-refresh every 10 seconds
  $effect(() => {
    const interval = setInterval(() => {
      if ($projectDir) loadEntries();
    }, 10000);
    return () => clearInterval(interval);
  });

  // Scroll to bottom when entries change
  $effect(() => {
    const _trigger = filtered();
    // Use microtask to wait for DOM update
    queueMicrotask(scrollToBottom);
  });
</script>

<div class="flex h-full flex-col bg-bg">
  <!-- Filter bar -->
  <div class="flex flex-shrink-0 items-center gap-1 border-b border-border bg-bg-secondary px-3 py-2">
    {#each filterConfig as f}
      <button
        class="rounded px-2.5 py-1 text-xs font-medium transition-colors {activeFilter === f.id
          ? 'bg-accent/20 text-accent'
          : 'text-text-muted hover:bg-bg-tertiary hover:text-text'}"
        onclick={() => (activeFilter = f.id)}
      >
        {f.label}
      </button>
    {/each}
    <div class="flex-1"></div>
    <span class="text-xs text-text-muted">{filtered().length} entries</span>
  </div>

  <!-- Timeline content -->
  {#if loading && entries.length === 0}
    <div class="flex flex-1 items-center justify-center">
      <span class="text-sm text-text-muted">Loading provenance...</span>
    </div>
  {:else if error && entries.length === 0}
    <div class="flex flex-1 items-center justify-center p-6">
      <div class="text-center">
        <p class="mb-1 text-sm text-text-muted">No provenance entries yet.</p>
        <p class="text-xs text-text-muted">Run the pipeline to generate activity logs.</p>
      </div>
    </div>
  {:else if filtered().length === 0}
    <div class="flex flex-1 items-center justify-center p-6">
      <div class="text-center">
        <p class="mb-1 text-sm text-text-muted">
          {#if entries.length === 0}
            No provenance entries yet.
          {:else}
            No entries match this filter.
          {/if}
        </p>
        {#if entries.length === 0}
          <p class="text-xs text-text-muted">Run the pipeline to generate activity logs.</p>
        {/if}
      </div>
    </div>
  {:else}
    <div class="flex-1 overflow-y-auto" bind:this={timelineEl}>
      <div class="relative py-3 pl-10 pr-4">
        <!-- Vertical line -->
        <div class="absolute left-5 top-0 bottom-0 w-px bg-border"></div>

        {#each filtered() as entry, i}
          {@const action = String(entry.action ?? "unknown")}
          {@const target = String(entry.target ?? "")}
          {@const details = String(entry.details ?? "")}
          {@const timestamp = entry.timestamp}

          <div class="relative mb-3 last:mb-0">
            <!-- Dot on the timeline -->
            <div class="absolute -left-5 top-1.5 flex h-3 w-3 items-center justify-center">
              <div class="h-2.5 w-2.5 rounded-full {timelineColor(action)} ring-2 ring-bg"></div>
            </div>

            <!-- Entry card -->
            <div class="rounded border border-border bg-bg-secondary p-2.5">
              <div class="mb-1 flex items-center gap-2">
                <span class="rounded border px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wider {actionColor(action)}">
                  {action}
                </span>
                {#if target}
                  <span class="truncate text-xs font-medium text-text-bright">{target}</span>
                {/if}
                <span class="ml-auto flex-shrink-0 text-xs text-text-muted">{formatTime(timestamp)}</span>
              </div>
              {#if details}
                <p class="text-xs leading-relaxed text-text-muted">{details}</p>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
