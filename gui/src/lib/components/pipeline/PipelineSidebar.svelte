<script lang="ts">
  import { paperState, stageList } from "$lib/stores/project";

  let now = $state(Date.now());

  $effect(() => {
    const interval = setInterval(() => {
      now = Date.now();
    }, 1000);
    return () => clearInterval(interval);
  });

  let elapsed = $derived(() => {
    if (!$paperState.started_at) return null;
    const start = new Date($paperState.started_at).getTime();
    const diff = Math.max(0, now - start);
    const seconds = Math.floor(diff / 1000);
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m.toString().padStart(2, "0")}m ${s.toString().padStart(2, "0")}s`;
    if (m > 0) return `${m}m ${s.toString().padStart(2, "0")}s`;
    return `${s}s`;
  });

  let completedCount = $derived($stageList.filter((s) => s.status === "completed").length);
  let totalCount = $derived($stageList.length);
  let activeAgents = $derived($paperState.active_agents ?? []);

  function statusIcon(status: string): string {
    switch (status) {
      case "completed":
        return "\u2713";
      case "in_progress":
        return "\u25CF";
      case "failed":
        return "\u2717";
      default:
        return "\u25CB";
    }
  }

  function statusColorClass(status: string): string {
    switch (status) {
      case "completed":
        return "text-success";
      case "in_progress":
        return "text-accent";
      case "failed":
        return "text-danger";
      default:
        return "text-text-muted";
    }
  }

  function labelColor(status: string): string {
    switch (status) {
      case "completed":
        return "text-text";
      case "in_progress":
        return "text-text-bright font-medium";
      case "failed":
        return "text-danger";
      default:
        return "text-text-muted";
    }
  }

  function formatStageName(key: string): string {
    // "01-research" -> "Research"
    const parts = key.split("-");
    parts.shift(); // remove number prefix
    return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
  }
</script>

<div class="flex h-full flex-col p-4">
  <!-- Header: progress summary -->
  <div class="mb-4 flex-shrink-0">
    <h2 class="text-sm font-semibold text-text-bright">Pipeline Progress</h2>
    <div class="mt-1 flex items-baseline justify-between">
      <span class="text-xs text-text-muted">
        Stage {$paperState.current_stage} / {totalCount || "..."}
      </span>
      {#if elapsed()}
        <span class="text-xs tabular-nums text-text-muted">{elapsed()}</span>
      {/if}
    </div>

    <!-- Progress bar -->
    {#if totalCount > 0}
      <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-bg-tertiary">
        <div
          class="h-full rounded-full bg-success transition-all duration-500"
          style="width: {(completedCount / totalCount) * 100}%"
        ></div>
      </div>
      <p class="mt-1 text-xs text-text-muted">{completedCount} of {totalCount} completed</p>
    {/if}
  </div>

  <!-- Stage checklist -->
  <div class="flex-1 overflow-y-auto">
    <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">Stages</h3>
    <ul class="space-y-0.5">
      {#each $stageList as stage (stage.key)}
        <li class="flex items-center gap-2 rounded px-2 py-1 text-xs {stage.status === 'in_progress' ? 'bg-bg-tertiary' : ''}">
          <span class="w-4 text-center {statusColorClass(stage.status)}">
            {#if stage.status === "in_progress"}
              <span class="inline-block animate-pulse">{statusIcon(stage.status)}</span>
            {:else}
              {statusIcon(stage.status)}
            {/if}
          </span>
          <span class="truncate {labelColor(stage.status)}">
            {formatStageName(stage.key)}
          </span>
        </li>
      {:else}
        <li class="px-2 py-2 text-xs text-text-muted">No stages loaded</li>
      {/each}
    </ul>
  </div>

  <!-- Active agents -->
  {#if activeAgents.length > 0}
    <div class="mt-4 flex-shrink-0 border-t border-border pt-3">
      <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
        Active Agents
        <span class="ml-1 rounded-full bg-accent/20 px-1.5 py-0.5 text-xs tabular-nums text-accent">
          {activeAgents.length}
        </span>
      </h3>
      <ul class="space-y-1.5">
        {#each activeAgents as agent}
          <li class="rounded bg-bg-tertiary px-2 py-1.5">
            <div class="flex items-center gap-1.5">
              <span class="h-1.5 w-1.5 flex-shrink-0 animate-pulse rounded-full bg-accent"></span>
              <span class="truncate text-xs font-medium text-text-bright">{agent.name}</span>
            </div>
            <p class="mt-0.5 truncate pl-3 text-xs text-text-muted">{agent.task}</p>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
