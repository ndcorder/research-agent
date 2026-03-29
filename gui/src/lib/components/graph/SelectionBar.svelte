<script lang="ts">
  import type { SourceMeta } from "$lib/types";
  import { collectTags } from "./graphUtils";

  interface Props {
    selectedNodes: Set<string>;
    sources: SourceMeta[];
    onaction: (action: string, nodeIds: string[]) => void;
    onresearch: (nodeIds: string[]) => void;
    onclear: () => void;
  }

  let { selectedNodes, sources, onaction, onresearch, onclear }: Props = $props();

  let tagDropdownOpen = $state(false);

  let existingTags = $derived.by(() => {
    return Array.from(collectTags(sources).keys()).sort();
  });

  function nodeIds(): string[] {
    return [...selectedNodes];
  }

  function handleTag(tag: string) {
    onaction(`tag:${tag}`, nodeIds());
    tagDropdownOpen = false;
  }

  function handleNewTag() {
    const tag = prompt("Enter new tag:");
    if (tag && tag.trim()) {
      onaction(`tag:${tag.trim()}`, nodeIds());
    }
    tagDropdownOpen = false;
  }

  function handleFlag() {
    onaction("flag", nodeIds());
  }

  function handleHide() {
    onaction("hide", nodeIds());
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && selectedNodes.size > 0) {
      e.stopPropagation();
      if (tagDropdownOpen) {
        tagDropdownOpen = false;
      } else {
        onclear();
      }
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if selectedNodes.size > 0}
  <div
    class="absolute bottom-14 left-1/2 -translate-x-1/2 z-40 bg-bg-secondary border border-border rounded-lg shadow-xl px-4 py-2 flex items-center gap-3 text-xs"
  >
    <span class="text-text-bright font-semibold">
      {selectedNodes.size} selected
    </span>

    <span class="text-border">&mdash;</span>

    <!-- Tag All dropdown -->
    <div class="relative">
      <button
        class="px-2 py-1 rounded bg-bg-tertiary border border-border text-text hover:text-text-bright hover:border-text-muted transition-colors cursor-pointer"
        onclick={(e: MouseEvent) => { e.stopPropagation(); tagDropdownOpen = !tagDropdownOpen; }}
      >
        Tag All &#9662;
      </button>

      {#if tagDropdownOpen}
        <!-- Invisible backdrop to close dropdown on outside click -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div class="fixed inset-0 z-30" onclick={() => (tagDropdownOpen = false)}></div>
        <div
          class="absolute bottom-full mb-1 left-0 z-40 bg-bg-secondary border border-border rounded-lg shadow-xl py-1 min-w-32 max-h-48 overflow-y-auto"
        >
          {#each existingTags as tag}
            <button
              class="block w-full text-left px-3 py-1 text-text hover:bg-bg-tertiary transition-colors cursor-pointer"
              onclick={() => handleTag(tag)}
            >
              {tag}
            </button>
          {/each}
          {#if existingTags.length > 0}
            <div class="border-t border-border my-1"></div>
          {/if}
          <button
            class="block w-full text-left px-3 py-1 text-accent hover:bg-bg-tertiary transition-colors cursor-pointer"
            onclick={handleNewTag}
          >
            New tag...
          </button>
        </div>
      {/if}
    </div>

    <button
      class="px-2 py-1 rounded bg-bg-tertiary border border-border text-text hover:text-warning hover:border-warning transition-colors cursor-pointer"
      onclick={handleFlag}
      aria-label="Flag all selected sources"
    >
      Flag All
    </button>

    <button
      class="px-2 py-1 rounded bg-accent border border-accent text-bg font-medium hover:bg-accent/80 transition-colors cursor-pointer"
      onclick={() => onresearch(nodeIds())}
      aria-label="Research selected claims"
    >
      Research
    </button>

    <button
      class="px-2 py-1 rounded bg-bg-tertiary border border-border text-text hover:text-text-muted hover:border-text-muted transition-colors cursor-pointer"
      onclick={handleHide}
      aria-label="Hide selected sources"
    >
      Hide
    </button>

    <button
      class="px-2 py-1 rounded bg-bg-tertiary border border-border text-text-muted hover:text-text hover:border-text-muted transition-colors cursor-pointer"
      onclick={onclear}
      aria-label="Clear selection"
    >
      Clear
    </button>
  </div>
{/if}
