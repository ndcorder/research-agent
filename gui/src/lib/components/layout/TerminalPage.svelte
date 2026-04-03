<script lang="ts">
  import TerminalPanel from "../terminal/TerminalPanel.svelte";
  import PipelineSidebar from "../pipeline/PipelineSidebar.svelte";
  import { activePage } from "$lib/stores/project";
</script>

<div class="flex h-full overflow-hidden">
  <!-- Terminal (main area) -->
  <div class="flex-1 overflow-hidden">
    <TerminalPanel fullscreen={true} />
  </div>

  <!-- Pipeline status sidebar -->
  <div class="w-72 flex-shrink-0 flex flex-col overflow-hidden border-l border-border bg-bg-secondary">
    <div class="flex items-center justify-between border-b border-border px-3 py-2">
      <span class="text-xs font-semibold text-text-bright">Pipeline</span>
      <button
        class="rounded px-1.5 py-0.5 text-xs text-text-muted hover:bg-bg-tertiary hover:text-text"
        onclick={() => activePage.set('workspace')}
      >
        Workspace
      </button>
    </div>
    <div class="flex-1 overflow-y-auto">
      <PipelineSidebar />
    </div>
  </div>
</div>
