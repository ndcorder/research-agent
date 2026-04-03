<script lang="ts">
  import Sidebar from "./Sidebar.svelte";
  import EditorPanel from "../editor/EditorPanel.svelte";
  import RightPanel from "./RightPanel.svelte";
  import TerminalPanel from "../terminal/TerminalPanel.svelte";
  import { bottomTerminalVisible, bottomTerminalHeight } from "$lib/stores/project";

  function loadPanelSize(key: string, fallback: number): number {
    if (typeof localStorage === "undefined") return fallback;
    const saved = localStorage.getItem(`panel-${key}`);
    return saved ? parseInt(saved) || fallback : fallback;
  }

  let sidebarWidth = $state(loadPanelSize("sidebar", 250));
  let rightPanelWidth = $state(loadPanelSize("right", 350));
  let terminalHeight = $state(loadPanelSize("bottom", 250));
  let dragging = $state<"sidebar" | "right" | "bottom" | null>(null);

  // Sync initial localStorage value into the store
  $effect(() => {
    bottomTerminalHeight.set(terminalHeight);
  });

  function onMouseDown(panel: "sidebar" | "right" | "bottom") {
    dragging = panel;
  }

  function onMouseMove(e: MouseEvent) {
    if (!dragging) return;
    if (dragging === "sidebar") {
      sidebarWidth = Math.max(180, Math.min(400, e.clientX));
    } else if (dragging === "right") {
      rightPanelWidth = Math.max(250, Math.min(600, window.innerWidth - e.clientX));
    } else if (dragging === "bottom") {
      const maxHeight = Math.floor(window.innerHeight * 0.6);
      terminalHeight = Math.max(100, Math.min(maxHeight, window.innerHeight - e.clientY));
      bottomTerminalHeight.set(terminalHeight);
    }
  }

  function onMouseUp() {
    if (dragging === "sidebar") {
      localStorage?.setItem("panel-sidebar", String(sidebarWidth));
    } else if (dragging === "right") {
      localStorage?.setItem("panel-right", String(rightPanelWidth));
    } else if (dragging === "bottom") {
      localStorage?.setItem("panel-bottom", String(terminalHeight));
    }
    dragging = null;
  }

  function toggleTerminal() {
    bottomTerminalVisible.update((v) => !v);
  }
</script>

<svelte:window onmousemove={onMouseMove} onmouseup={onMouseUp} />

<div class="flex h-full flex-col {dragging ? 'select-none' : ''}" style:cursor={dragging === 'bottom' ? 'row-resize' : dragging ? 'col-resize' : undefined}>
  <!-- Top: existing 3-panel horizontal layout -->
  <div class="flex flex-1 overflow-hidden min-h-0">
    <!-- Sidebar -->
    <div style="width: {sidebarWidth}px" class="flex-shrink-0 overflow-hidden border-r border-border">
      <Sidebar />
    </div>

    <!-- Sidebar resize handle -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="w-1 cursor-col-resize flex-shrink-0 transition-all duration-150 {dragging === 'sidebar' ? 'bg-accent w-0.5' : 'bg-border opacity-50 hover:opacity-100 hover:bg-accent'}"
      onmousedown={() => onMouseDown("sidebar")}
      role="separator"
      tabindex="0"
      aria-label="Resize sidebar"
    ></div>

    <!-- Main editor area -->
    <div class="flex-1 overflow-hidden">
      <EditorPanel />
    </div>

    <!-- Right panel resize handle -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="w-1 cursor-col-resize flex-shrink-0 transition-all duration-150 {dragging === 'right' ? 'bg-accent w-0.5' : 'bg-border opacity-50 hover:opacity-100 hover:bg-accent'}"
      onmousedown={() => onMouseDown("right")}
      role="separator"
      tabindex="0"
      aria-label="Resize right panel"
    ></div>

    <!-- Right panel -->
    <div style="width: {rightPanelWidth}px" class="flex-shrink-0 overflow-hidden border-l border-border">
      <RightPanel />
    </div>
  </div>

  <!-- Bottom terminal area -->
  <div class="border-t border-border flex-shrink-0">
    <!-- Always-visible toolbar -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions a11y_no_static_element_interactions a11y_click_events_have_key_events -->
    <div
      class="flex h-7 items-center gap-2 px-2 text-xs cursor-pointer select-none hover:bg-bg-secondary"
      onclick={toggleTerminal}
      onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleTerminal(); } }}
      role="button"
      tabindex="0"
    >
      <button
        class="flex items-center justify-center w-4 h-4 text-text-muted hover:text-text transition-colors"
        aria-label="Toggle terminal"
      >
        {#if $bottomTerminalVisible}
          <svg class="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 5l3 3 3-3" />
          </svg>
        {:else}
          <svg class="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7l3-3 3 3" />
          </svg>
        {/if}
      </button>
      <span class="text-text-muted font-medium">Terminal</span>
      <span class="ml-auto text-text-muted/50 text-[10px]">{'\u2318'}`</span>
    </div>

    {#if $bottomTerminalVisible}
      <!-- Vertical resize handle -->
      <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
      <div
        class="h-1 cursor-row-resize transition-all duration-150 {dragging === 'bottom' ? 'bg-accent h-0.5' : 'bg-border opacity-50 hover:opacity-100 hover:bg-accent'}"
        onmousedown={() => onMouseDown("bottom")}
        role="separator"
        tabindex="0"
        aria-label="Resize terminal"
      ></div>

      <!-- Terminal panel -->
      <div style="height: {terminalHeight}px" class="overflow-hidden">
        <TerminalPanel fullscreen={false} />
      </div>
    {/if}
  </div>
</div>
