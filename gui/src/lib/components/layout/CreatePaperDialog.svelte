<script lang="ts">
  import {
    listVenues,
    createPaper,
    getResearchAgentDir,
    type VenueInfo,
  } from "$lib/utils/ipc";

  let {
    open,
    onclose,
    oncreated,
  }: {
    open: boolean;
    onclose: () => void;
    oncreated: (path: string) => void;
  } = $props();

  let directory = $state("");
  let topic = $state("");
  let venue = $state("generic");
  let deep = $state(false);
  let runtime = $state("claude");
  let venues = $state<VenueInfo[]>([]);
  let error = $state("");
  let submitting = $state(false);
  let researchAgentDir = $state("");
  let loadingVenues = $state(false);

  const canSubmit = $derived(
    directory.trim().length > 0 && topic.trim().length > 0 && !submitting
  );

  function toKebabCase(input: string): string {
    return input
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");
  }

  function handleDirectoryInput(e: Event) {
    const target = e.target as HTMLInputElement;
    directory = toKebabCase(target.value);
  }

  $effect(() => {
    if (open) {
      loadVenues();
    }
  });

  async function loadVenues() {
    loadingVenues = true;
    try {
      researchAgentDir = await getResearchAgentDir();
      venues = await listVenues(researchAgentDir);
    } catch (err) {
      // Fallback: use hardcoded list if we can't discover the dir
      venues = [
        { id: "generic", name: "Generic" },
        { id: "ieee", name: "Ieee" },
        { id: "acm", name: "Acm" },
        { id: "neurips", name: "Neurips" },
        { id: "nature", name: "Nature" },
        { id: "arxiv", name: "Arxiv" },
        { id: "apa", name: "Apa" },
      ];
    } finally {
      loadingVenues = false;
    }
  }

  function resetForm() {
    directory = "";
    topic = "";
    venue = "generic";
    deep = false;
    runtime = "claude";
    error = "";
    submitting = false;
  }

  function close() {
    resetForm();
    onclose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") close();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = "";

    if (!directory.trim()) {
      error = "Directory name is required.";
      return;
    }
    if (!topic.trim()) {
      error = "Topic is required.";
      return;
    }

    submitting = true;

    try {
      const path = await createPaper(
        researchAgentDir,
        directory.trim(),
        topic.trim(),
        venue,
        deep,
        runtime
      );
      resetForm();
      oncreated(path);
    } catch (err) {
      error =
        err instanceof Error ? err.message : String(err) || "Failed to create paper.";
    } finally {
      submitting = false;
    }
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
  >
    <div class="w-full max-w-lg rounded-lg border border-[#3b3f5c] bg-[#1a1b26] p-6 shadow-2xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-base font-semibold text-[#e0e6ff]">Create New Paper</h2>
        <button
          class="text-[#565f89] transition-colors hover:text-[#c0caf5]"
          onclick={close}
          aria-label="Close"
        >
          &#x2715;
        </button>
      </div>

      <form onsubmit={handleSubmit} class="space-y-3">
        <!-- Directory name -->
        <div>
          <label for="paper-dir" class="mb-1 block text-xs font-medium text-[#565f89]"
            >Directory Name *</label
          >
          <input
            id="paper-dir"
            type="text"
            value={directory}
            oninput={handleDirectoryInput}
            required
            class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="my-paper-name"
          />
          {#if directory}
            <p class="mt-0.5 text-xs text-[#565f89]">{directory}</p>
          {/if}
        </div>

        <!-- Topic -->
        <div>
          <label for="paper-topic" class="mb-1 block text-xs font-medium text-[#565f89]"
            >Topic *</label
          >
          <textarea
            id="paper-topic"
            bind:value={topic}
            required
            rows="3"
            class="w-full resize-none rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="A survey on large language model reasoning capabilities..."
          ></textarea>
        </div>

        <!-- Venue + Runtime + Depth row -->
        <div class="flex gap-3">
          <div class="flex-1">
            <label for="paper-venue" class="mb-1 block text-xs font-medium text-[#565f89]"
              >Venue</label
            >
            <select
              id="paper-venue"
              bind:value={venue}
              class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            >
              {#each venues as v (v.id)}
                <option value={v.id}>{v.name}</option>
              {/each}
            </select>
          </div>

          <div class="w-36">
            <span class="mb-1 block text-xs font-medium text-[#565f89]">Runtime</span>
            <div class="flex rounded border border-[#3b3f5c] bg-[#24283b]">
              <button
                type="button"
                class="flex-1 rounded-l px-2.5 py-1.5 text-xs font-medium transition-colors {runtime ===
                'claude'
                  ? 'bg-[#7aa2f7] text-[#1a1b26]'
                  : 'text-[#565f89] hover:text-[#c0caf5]'}"
                onclick={() => (runtime = "claude")}
              >
                Claude
              </button>
              <button
                type="button"
                class="flex-1 rounded-r px-2.5 py-1.5 text-xs font-medium transition-colors {runtime ===
                'codex'
                  ? 'bg-[#7aa2f7] text-[#1a1b26]'
                  : 'text-[#565f89] hover:text-[#c0caf5]'}"
                onclick={() => (runtime = "codex")}
              >
                Codex
              </button>
            </div>
          </div>

          <div class="w-36">
            <span class="mb-1 block text-xs font-medium text-[#565f89]">Depth</span>
            <div class="flex rounded border border-[#3b3f5c] bg-[#24283b]">
              <button
                type="button"
                class="flex-1 rounded-l px-2.5 py-1.5 text-xs font-medium transition-colors {!deep
                  ? 'bg-[#7aa2f7] text-[#1a1b26]'
                  : 'text-[#565f89] hover:text-[#c0caf5]'}"
                onclick={() => (deep = false)}
              >
                Standard
              </button>
              <button
                type="button"
                class="flex-1 rounded-r px-2.5 py-1.5 text-xs font-medium transition-colors {deep
                  ? 'bg-[#7aa2f7] text-[#1a1b26]'
                  : 'text-[#565f89] hover:text-[#c0caf5]'}"
                onclick={() => (deep = true)}
              >
                Deep
              </button>
            </div>
          </div>
        </div>

        <!-- Error -->
        {#if error}
          <p class="text-xs text-[#f7768e]">{error}</p>
        {/if}

        <!-- Buttons -->
        <div class="flex justify-end gap-2 pt-1">
          <button
            type="button"
            class="rounded border border-[#3b3f5c] px-3 py-1.5 text-xs font-medium text-[#c0caf5] transition-colors hover:bg-[#2f3350]"
            onclick={close}
          >
            Cancel
          </button>
          <button
            type="submit"
            class="rounded bg-[#7aa2f7] px-3 py-1.5 text-xs font-medium text-[#1a1b26] transition-colors hover:bg-[#7aa2f7]/80 disabled:opacity-50"
            disabled={!canSubmit}
          >
            {#if submitting}
              <span class="inline-flex items-center gap-1.5">
                <svg
                  class="h-3 w-3 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  ></path>
                </svg>
                Creating...
              </span>
            {:else}
              Create Paper
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
