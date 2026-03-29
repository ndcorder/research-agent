<script lang="ts">
  import "../app.css";
  import { activePage, projectDir, showCommandPalette, showSettings, sources, claims, paperState } from "$lib/stores/project";
  import { stopWatching } from "$lib/utils/ipc";
  import StatusBar from "$lib/components/layout/StatusBar.svelte";
  import ToastContainer from "$lib/components/ui/ToastContainer.svelte";
  import SettingsPanel from "$lib/components/ui/SettingsPanel.svelte";
  import CommandPalette from "$lib/components/ui/CommandPalette.svelte";
  import { setupShortcuts } from "$lib/utils/shortcuts";
  import { onMount } from "svelte";

  function closeProject() {
    stopWatching().catch(() => {});
    projectDir.set(null);
    sources.set([]);
    claims.set([]);
    paperState.set({ current_stage: 0, stages: {} });
  }

  let { children } = $props();

  onMount(() => {
    const cleanup = setupShortcuts();
    return cleanup;
  });
</script>

<div class="flex h-screen w-screen flex-col bg-bg">
  <!-- Top nav bar -->
  <nav class="flex h-10 items-center border-b border-border bg-bg-secondary px-4">
    <div class="flex gap-1">
      <button
        class="rounded px-3 py-1 text-xs transition-colors {$activePage === 'workspace'
          ? 'bg-bg-tertiary text-text-bright'
          : 'text-text-muted hover:text-text'}"
        onclick={() => activePage.set('workspace')}
      >
        Workspace
      </button>
      <button
        class="rounded px-3 py-1 text-xs transition-colors {$activePage === 'terminal'
          ? 'bg-bg-tertiary text-text-bright'
          : 'text-text-muted hover:text-text'}"
        onclick={() => activePage.set('terminal')}
      >
        Terminal
      </button>
    </div>
    <div class="mx-auto text-xs text-text-muted">
      {$projectDir ? `Research Agent \u2014 ${$projectDir.split('/').pop()}` : 'Research Agent'}
    </div>
    <div class="flex items-center gap-2">
      {#if $projectDir}
        <button
          class="rounded px-2 py-0.5 text-xs text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text"
          onclick={() => showCommandPalette.set(true)}
          title="Command Palette (Cmd+P)"
        >Cmd+P</button>
        <button
          class="rounded px-2 py-0.5 text-xs text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text"
          onclick={() => showSettings.set(true)}
          title="Settings (Cmd+,)"
        >&#x2699;</button>
        <button
          class="rounded px-2 py-0.5 text-xs text-text-muted transition-colors hover:bg-danger/20 hover:text-danger"
          onclick={closeProject}
          title="Close Project"
        >&times;</button>
      {/if}
    </div>
  </nav>

  <!-- Page content -->
  <div class="flex-1 overflow-hidden">
    {@render children()}
  </div>

  <StatusBar />
  <ToastContainer />
  <SettingsPanel />
  <CommandPalette />
</div>
