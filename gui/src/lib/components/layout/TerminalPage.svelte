<script lang="ts">
  import TerminalPanel from "../terminal/TerminalPanel.svelte";
  import PipelineSidebar from "../pipeline/PipelineSidebar.svelte";
</script>

<div class="flex h-full overflow-hidden">
  <!-- Terminal (main area) -->
  <div class="flex-1 overflow-hidden">
    <TerminalPanel fullscreen={true} />
  </div>

  <!-- Pipeline status sidebar -->
  <div class="w-72 flex-shrink-0 overflow-y-auto border-l border-border bg-bg-secondary">
    <PipelineSidebar />
  </div>
</div>
