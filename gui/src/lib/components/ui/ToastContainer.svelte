<script lang="ts">
  import { toasts } from "$lib/stores/toast";

  function typeClasses(type: string): string {
    switch (type) {
      case "success":
        return "border-success/40 bg-success/10 text-success";
      case "error":
        return "border-danger/40 bg-danger/10 text-danger";
      case "warning":
        return "border-warning/40 bg-warning/10 text-warning";
      default:
        return "border-accent/40 bg-accent/10 text-accent";
    }
  }

  function typeIcon(type: string): string {
    switch (type) {
      case "success": return "\u2713";
      case "error": return "\u2717";
      case "warning": return "\u26A0";
      default: return "\u2139";
    }
  }
</script>

<div class="fixed bottom-10 right-4 z-50 flex flex-col gap-2" style="pointer-events: none;">
  {#each $toasts as toast (toast.id)}
    <div
      class="pointer-events-auto flex items-center gap-2 rounded-lg border px-4 py-2 text-xs shadow-lg backdrop-blur-sm transition-all duration-300 animate-in {typeClasses(toast.type)}"
      style="animation: slideIn 0.2s ease-out;"
    >
      <span class="text-sm">{typeIcon(toast.type)}</span>
      <span>{toast.message}</span>
      <button
        class="ml-2 opacity-50 hover:opacity-100"
        onclick={() => toasts.remove(toast.id)}
      >&times;</button>
    </div>
  {/each}
</div>

<style>
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
</style>
