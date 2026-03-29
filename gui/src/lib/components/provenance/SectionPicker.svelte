<script lang="ts">
  interface Props {
    sections: string[];
    selected: string | null;
    onselect: (section: string | null) => void;
  }

  let { sections, selected, onselect }: Props = $props();

  /** Capitalize section name for display */
  function displayName(section: string): string {
    return section
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
</script>

<div class="flex items-center gap-1 overflow-x-auto px-3 py-2">
  <button
    class="shrink-0 rounded px-2.5 py-1 text-xs font-medium transition-colors {selected === null
      ? 'bg-accent/20 text-accent'
      : 'text-text-muted hover:bg-bg-tertiary hover:text-text'}"
    onclick={() => onselect(null)}
  >
    All Sections
  </button>
  {#each sections as section}
    <button
      class="shrink-0 rounded px-2.5 py-1 text-xs font-medium transition-colors {selected === section
        ? 'bg-accent/20 text-accent'
        : 'text-text-muted hover:bg-bg-tertiary hover:text-text'}"
      onclick={() => onselect(section)}
    >
      {displayName(section)}
    </button>
  {/each}
</div>
