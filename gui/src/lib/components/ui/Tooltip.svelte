<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    text,
    position = "top",
    children,
  }: {
    text: string;
    position?: "top" | "bottom" | "left" | "right";
    children: Snippet;
  } = $props();

  let visible = $state(false);
  let timeout: ReturnType<typeof setTimeout> | null = null;

  function show() {
    timeout = setTimeout(() => (visible = true), 200);
  }

  function hide() {
    if (timeout) clearTimeout(timeout);
    timeout = null;
    visible = false;
  }

  const positionClasses: Record<string, string> = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  const arrowClasses: Record<string, string> = {
    top: "top-full left-1/2 -translate-x-1/2 border-t-[#2f3350] border-x-transparent border-b-transparent",
    bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-[#2f3350] border-x-transparent border-t-transparent",
    left: "left-full top-1/2 -translate-y-1/2 border-l-[#2f3350] border-y-transparent border-r-transparent",
    right: "right-full top-1/2 -translate-y-1/2 border-r-[#2f3350] border-y-transparent border-l-transparent",
  };
</script>

<div
  class="relative inline-flex"
  onmouseenter={show}
  onmouseleave={hide}
  onfocusin={show}
  onfocusout={hide}
  role="tooltip"
>
  {@render children()}

  {#if visible}
    <div
      class="absolute z-50 whitespace-nowrap rounded px-2 py-1 text-xs font-normal shadow-lg
        bg-bg-tertiary text-text-bright pointer-events-none
        animate-fade-in {positionClasses[position]}"
    >
      {text}
      <span
        class="absolute border-[5px] {arrowClasses[position]}"
      ></span>
    </div>
  {/if}
</div>

<style>
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  :global(.animate-fade-in) {
    animation: fadeIn 150ms ease-out;
  }
</style>
