<script lang="ts">
  import { pipelineState, pipelineStageList } from "$lib/stores/pipeline";
  import { runPipelineAction } from "$lib/utils/ipc";
  import { projectDir, bottomTerminalVisible } from "$lib/stores/project";

  let autoIterations = $state(3);

  async function startWritePaper() {
    if (!$projectDir) return;
    const terminalId = await runPipelineAction($projectDir, "writePaper", {
      claim_ids: [],
    });
    pipelineState.update((s) => ({ ...s, running: true, terminalId }));
    bottomTerminalVisible.set(true);
  }

  async function startAuto() {
    if (!$projectDir) return;
    const terminalId = await runPipelineAction($projectDir, "auto", {
      claim_ids: [],
      auto_iterations: autoIterations,
    });
    pipelineState.update((s) => ({ ...s, running: true, terminalId }));
    bottomTerminalVisible.set(true);
  }

  function stageStatus(key: string): "done" | "active" | "pending" {
    const stage = $pipelineState.stages[key];
    if (stage?.done) return "done";
    if ($pipelineState.currentStage === key) return "active";
    return "pending";
  }
</script>

<div class="flex flex-col gap-3 p-3">
  <div class="flex items-center gap-2">
    <button
      class="rounded bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-40"
      onclick={startWritePaper}
      disabled={$pipelineState.running}
    >
      Write Paper
    </button>
    <div class="flex items-center gap-1">
      <button
        class="rounded bg-surface px-3 py-1.5 text-sm font-medium text-text hover:bg-surface-hover disabled:opacity-40"
        onclick={startAuto}
        disabled={$pipelineState.running}
      >
        /auto
      </button>
      <input
        type="number"
        min="1"
        max="10"
        bind:value={autoIterations}
        class="w-12 rounded bg-surface px-1.5 py-1 text-center text-sm text-text"
      />
      <span class="text-xs text-text-muted">iterations</span>
    </div>
  </div>

  <div class="flex flex-col gap-0.5">
    {#each pipelineStageList as stage}
      {@const status = stageStatus(stage.key)}
      <div
        class="flex items-center gap-2 rounded px-2 py-1 text-sm {status === 'pending' ? 'opacity-40' : ''} {status === 'done' ? 'text-success' : ''} {status === 'active' ? 'font-semibold bg-accent/10' : ''}"
      >
        <span class="w-8 font-mono text-xs">{stage.number}</span>
        <span class="flex-1">{stage.label}</span>
        {#if status === "done"}
          <span class="text-success">&#10003;</span>
        {:else if status === "active"}
          <span class="animate-spin">&#9881;</span>
        {:else}
          <span class="text-text-muted">&#9675;</span>
        {/if}
      </div>
    {/each}
  </div>
</div>
