<script lang="ts">
  import Sidebar from "./Sidebar.svelte";
  import EditorPanel from "../editor/EditorPanel.svelte";
  import RightPanel from "./RightPanel.svelte";

  function loadPanelSize(key: string, fallback: number): number {
    if (typeof localStorage === "undefined") return fallback;
    const saved = localStorage.getItem(`panel-${key}`);
    return saved ? parseInt(saved) || fallback : fallback;
  }

  let sidebarWidth = $state(loadPanelSize("sidebar", 250));
  let rightPanelWidth = $state(loadPanelSize("right", 350));
  let dragging = $state<"sidebar" | "right" | null>(null);

  function onMouseDown(panel: "sidebar" | "right") {
    dragging = panel;
  }

  function onMouseMove(e: MouseEvent) {
    if (!dragging) return;
    if (dragging === "sidebar") {
      sidebarWidth = Math.max(180, Math.min(400, e.clientX));
    } else if (dragging === "right") {
      rightPanelWidth = Math.max(250, Math.min(600, window.innerWidth - e.clientX));
    }
  }

  function onMouseUp() {
    if (dragging === "sidebar") {
      localStorage?.setItem("panel-sidebar", String(sidebarWidth));
    } else if (dragging === "right") {
      localStorage?.setItem("panel-right", String(rightPanelWidth));
    }
    dragging = null;
  }
</script>

<svelte:window onmousemove={onMouseMove} onmouseup={onMouseUp} />

<div class="flex h-full overflow-hidden {dragging ? 'select-none' : ''}" style:cursor={dragging ? 'col-resize' : undefined}>
  <!-- Sidebar -->
  <div style="width: {sidebarWidth}px" class="flex-shrink-0 overflow-hidden border-r border-border">
    <Sidebar />
  </div>

  <!-- Sidebar resize handle -->
  <div
    class="w-1 cursor-col-resize flex-shrink-0 transition-all duration-150 {dragging === 'sidebar' ? 'bg-accent w-0.5' : 'bg-border opacity-50 hover:opacity-100 hover:bg-accent'}"
    onmousedown={() => onMouseDown("sidebar")}
    role="separator"
  ></div>

  <!-- Main editor area -->
  <div class="flex-1 overflow-hidden">
    <EditorPanel />
  </div>

  <!-- Right panel resize handle -->
  <div
    class="w-1 cursor-col-resize flex-shrink-0 transition-all duration-150 {dragging === 'right' ? 'bg-accent w-0.5' : 'bg-border opacity-50 hover:opacity-100 hover:bg-accent'}"
    onmousedown={() => onMouseDown("right")}
    role="separator"
  ></div>

  <!-- Right panel -->
  <div style="width: {rightPanelWidth}px" class="flex-shrink-0 overflow-hidden border-l border-border">
    <RightPanel />
  </div>
</div>
