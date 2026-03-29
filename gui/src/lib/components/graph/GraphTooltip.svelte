<script lang="ts">
  interface Props {
    visible: boolean;
    x: number;
    y: number;
    text: string;
  }

  let { visible, x, y, text }: Props = $props();
</script>

{#if visible}
  <div
    class="pointer-events-none fixed z-50 max-w-64 rounded border border-border bg-bg-secondary px-2 py-1 text-xs text-text shadow-lg"
    style="left: {x + 12}px; top: {y - 8}px;"
  >
    {text}
  </div>
{/if}
