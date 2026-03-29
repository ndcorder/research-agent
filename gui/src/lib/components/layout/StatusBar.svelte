<script lang="ts">
  import { get } from "svelte/store";
  import {
    projectDir,
    paperConfig,
    paperState,
    sources,
    stageList,
    wordCount,
    texContent,
  } from "$lib/stores/project";
  import { parseCiteKeys } from "$lib/utils/latex";
  import { compileLatex } from "$lib/utils/ipc";
  import { toasts } from "$lib/stores/toast";

  let compiling = $state(false);
  let compileStatus = $state<"idle" | "success" | "error">("idle");
  let compileOutput = $state("");
  let showOutput = $state(false);
  let statusTimeout: ReturnType<typeof setTimeout> | undefined;

  const folderName = $derived(
    $projectDir ? $projectDir.split("/").pop() ?? "" : ""
  );
  const venue = $derived($paperConfig?.venue ?? null);
  const depth = $derived($paperConfig?.depth ?? null);
  const sourceCount = $derived($sources.length);
  const stages = $derived($stageList);
  const totalStages = $derived(Math.max(stages.length, 15));
  const currentStage = $derived($paperState.current_stage);

  const pipelineLabel = $derived.by(() => {
    if (currentStage <= 0) return "Idle";
    const active = stages.find(
      (s) => s.status === "in_progress"
    );
    if (active) {
      const num = parseInt(active.key.split("-")[0]) || currentStage;
      const name = active.key
        .replace(/^\d+-/, "")
        .replace(/-/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      return `Stage ${num}/${totalStages} \u2013 ${name}`;
    }
    return `Stage ${currentStage}/${totalStages}`;
  });

  async function handleCompile() {
    const dir = get(projectDir);
    if (!dir || compiling) return;
    compiling = true;
    compileStatus = "idle";
    if (statusTimeout) clearTimeout(statusTimeout);
    try {
      const result = await compileLatex(dir);
      compileOutput = result.output;
      compileStatus = result.success ? "success" : "error";
      if (result.success) {
        toasts.success("LaTeX compiled successfully");
      } else {
        toasts.error("Compilation failed — check log");
      }
    } catch (e) {
      compileOutput = String(e);
      compileStatus = "error";
      toasts.error("Compilation error");
    } finally {
      compiling = false;
      statusTimeout = setTimeout(() => {
        compileStatus = "idle";
      }, 3000);
    }
  }
</script>

{#if showOutput && compileOutput}
  <div
    class="max-h-40 overflow-auto border-t border-border bg-bg px-3 py-2 font-mono text-xs text-text-muted"
  >
    <div class="mb-1 flex items-center justify-between">
      <span class="text-text text-xs font-semibold uppercase tracking-wider">Compile Output</span>
      <button
        class="text-text-muted hover:text-text text-xs"
        onclick={() => (showOutput = false)}
      >
        Close
      </button>
    </div>
    <pre class="whitespace-pre-wrap">{compileOutput}</pre>
  </div>
{/if}

<footer
  class="flex h-7 shrink-0 items-center justify-between border-t border-border bg-bg-secondary px-3 text-xs"
>
  <!-- Left: project info -->
  <div class="flex items-center gap-2 min-w-0">
    {#if folderName}
      <span class="truncate text-text" title={$projectDir ?? ""}>{folderName}</span>
    {:else}
      <span class="text-text-muted">No project</span>
    {/if}
    {#if venue}
      <span class="rounded bg-bg-tertiary px-1.5 py-px text-xs text-accent">{venue}</span>
    {/if}
    {#if depth}
      <span class="rounded bg-bg-tertiary px-1.5 py-px text-xs text-text-muted">{depth}</span>
    {/if}
  </div>

  <!-- Center: pipeline stage -->
  <div class="text-text-muted">
    {pipelineLabel}
  </div>

  <!-- Right: sources + compile -->
  <div class="flex items-center gap-3">
    <span class="text-text-muted">{$wordCount.toLocaleString()} words</span>
    <span class="text-text-muted">{parseCiteKeys($texContent).length} cites</span>
    <span class="text-text-muted">{sourceCount} source{sourceCount !== 1 ? "s" : ""}</span>

    <button
      class="flex items-center gap-1 rounded px-1.5 py-px text-xs transition-colors
        {compiling
          ? 'text-text-muted cursor-wait'
          : compileStatus === 'success'
            ? 'text-success'
            : compileStatus === 'error'
              ? 'text-danger'
              : 'text-text-muted hover:text-text'}"
      onclick={handleCompile}
      disabled={compiling}
      title="Compile LaTeX (Ctrl+Shift+B)"
    >
      {#if compiling}
        <svg class="h-3 w-3 animate-spin" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" opacity="0.3" />
          <path d="M14 8a6 6 0 0 0-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      {:else if compileStatus === "success"}
        <svg class="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
          <path d="M13.485 3.929a1 1 0 0 1 .086 1.413l-6 7a1 1 0 0 1-1.413.086l-3-2.5a1 1 0 1 1 1.282-1.536l2.244 1.87 5.388-6.247a1 1 0 0 1 1.413-.086Z" />
        </svg>
      {:else if compileStatus === "error"}
        <svg class="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708Z" />
        </svg>
      {:else}
        <svg class="h-3 w-3" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4.5 3a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-1 0v-9A.5.5 0 0 1 4.5 3Zm7.858 4.146-5-4A.5.5 0 0 0 6.5 3.5v8a.5.5 0 0 0 .858.354l5-4a.5.5 0 0 0 0-.708Z" />
        </svg>
      {/if}
      Compile
    </button>

    <button
      class="text-xs text-text-muted hover:text-text"
      onclick={() => (showOutput = !showOutput)}
      title="Toggle compile output"
    >
      {showOutput ? "\u25BC" : "\u25B2"} Log
    </button>
  </div>
</footer>
