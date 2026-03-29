<script lang="ts">
  import { projectDir, sources } from "$lib/stores/project";
  import { writeFile, listSources } from "$lib/utils/ipc";
  import { serializeFrontmatter } from "$lib/utils/frontmatter";

  let {
    open,
    onclose,
  }: {
    open: boolean;
    onclose: () => void;
  } = $props();

  let title = $state("");
  let authors = $state("");
  let year = $state<number | null>(new Date().getFullYear());
  let doi = $state("");
  let url = $state("");
  let tags = $state("");
  let notes = $state("");
  let keyManual = $state("");
  let keyEdited = $state(false);
  let error = $state("");
  let submitting = $state(false);

  const autoKey = $derived.by(() => {
    const firstAuthor = authors
      .split(",")[0]
      ?.trim()
      .split(/\s+/)
      .pop()
      ?.toLowerCase()
      .replace(/[^a-z]/g, "");
    const y = year ?? "";
    return firstAuthor ? `${firstAuthor}${y}` : "";
  });

  const citationKey = $derived(keyEdited ? keyManual : autoKey);

  function onKeyInput(e: Event) {
    const target = e.target as HTMLInputElement;
    keyManual = target.value;
    keyEdited = true;
  }

  function resetForm() {
    title = "";
    authors = "";
    year = new Date().getFullYear();
    doi = "";
    url = "";
    tags = "";
    notes = "";
    keyManual = "";
    keyEdited = false;
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

    const key = citationKey.trim();
    if (!key) {
      error = "Citation key is required.";
      return;
    }
    if (!title.trim()) {
      error = "Title is required.";
      return;
    }

    const dir = $projectDir;
    if (!dir) {
      error = "No project directory loaded.";
      return;
    }

    // Check for duplicate key
    const existing = $sources.find((s) => s.key === key);
    if (existing) {
      error = `A source with key "${key}" already exists.`;
      return;
    }

    submitting = true;

    try {
      const authorsList = authors
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);
      const tagsList = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      const fm: Record<string, unknown> = {
        title: title.trim(),
        status: "human-added",
      };
      if (authorsList.length) fm.authors = authorsList;
      if (year) fm.year = year;
      if (doi.trim()) fm.doi = doi.trim();
      if (url.trim()) fm.url = url.trim();
      if (tagsList.length) fm.tags = tagsList;

      const body = notes.trim() || "";
      const content = serializeFrontmatter(fm, body);
      const filePath = `${dir}/research/sources/${key}.md`;

      await writeFile(filePath, content);

      // Reload sources store
      const updated = await listSources(dir);
      sources.set(updated);

      close();
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to create source.";
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
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
  >
    <div class="w-full max-w-lg rounded-lg border border-[#3b3f5c] bg-[#1a1b26] p-6 shadow-2xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-base font-semibold text-[#e0e6ff]">Add Source</h2>
        <button
          class="text-[#565f89] transition-colors hover:text-[#c0caf5]"
          onclick={close}
          aria-label="Close"
        >
          &#x2715;
        </button>
      </div>

      <form onsubmit={handleSubmit} class="space-y-3">
        <!-- Title -->
        <div>
          <label for="src-title" class="mb-1 block text-xs font-medium text-[#565f89]">Title *</label>
          <input
            id="src-title"
            type="text"
            bind:value={title}
            required
            class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="Paper title"
          />
        </div>

        <!-- Authors -->
        <div>
          <label for="src-authors" class="mb-1 block text-xs font-medium text-[#565f89]">Authors</label>
          <input
            id="src-authors"
            type="text"
            bind:value={authors}
            class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="Smith, J., Doe, A."
          />
        </div>

        <!-- Year + Citation key row -->
        <div class="flex gap-3">
          <div class="w-24">
            <label for="src-year" class="mb-1 block text-xs font-medium text-[#565f89]">Year</label>
            <input
              id="src-year"
              type="number"
              bind:value={year}
              min="1900"
              max="2099"
              class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            />
          </div>
          <div class="flex-1">
            <label for="src-key" class="mb-1 block text-xs font-medium text-[#565f89]">Citation Key *</label>
            <input
              id="src-key"
              type="text"
              value={citationKey}
              oninput={onKeyInput}
              required
              class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7] {keyEdited ? '' : 'italic text-[#565f89]'}"
              placeholder="smith2024"
            />
            {#if !keyEdited && citationKey}
              <p class="mt-0.5 text-xs text-[#565f89]">Auto-generated (edit to override)</p>
            {/if}
          </div>
        </div>

        <!-- DOI + URL row -->
        <div class="flex gap-3">
          <div class="flex-1">
            <label for="src-doi" class="mb-1 block text-xs font-medium text-[#565f89]">DOI</label>
            <input
              id="src-doi"
              type="text"
              bind:value={doi}
              class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
              placeholder="10.1234/example"
            />
          </div>
          <div class="flex-1">
            <label for="src-url" class="mb-1 block text-xs font-medium text-[#565f89]">URL</label>
            <input
              id="src-url"
              type="text"
              bind:value={url}
              class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
              placeholder="https://..."
            />
          </div>
        </div>

        <!-- Tags -->
        <div>
          <label for="src-tags" class="mb-1 block text-xs font-medium text-[#565f89]">Tags</label>
          <input
            id="src-tags"
            type="text"
            bind:value={tags}
            class="w-full rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="machine-learning, nlp, transformers"
          />
        </div>

        <!-- Notes -->
        <div>
          <label for="src-notes" class="mb-1 block text-xs font-medium text-[#565f89]">Initial Notes</label>
          <textarea
            id="src-notes"
            bind:value={notes}
            rows="3"
            class="w-full resize-none rounded border border-[#3b3f5c] bg-[#24283b] px-2.5 py-1.5 text-sm text-[#c0caf5] placeholder-[#565f89] outline-none focus:border-[#7aa2f7] focus:ring-1 focus:ring-[#7aa2f7]"
            placeholder="Key findings, relevance to your paper..."
          ></textarea>
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
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create Source"}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
