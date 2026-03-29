<script lang="ts">
  import {
    claims,
    selectedClaim,
    sources,
    selectedSource,
    rightPanel,
    projectDir,
  } from "$lib/stores/project";
  import { readFile, writeFile } from "$lib/utils/ipc";
  import type { ClaimMeta, SourceMeta } from "$lib/types";

  let claim = $derived<ClaimMeta | undefined>(
    $claims.find((c) => c.id === $selectedClaim)
  );

  let linkedSources = $derived<SourceMeta[]>(
    claim
      ? $sources.filter(
          (s) =>
            s.evidence_for?.includes(claim!.id) ||
            s.tags?.includes(claim!.id)
        )
      : []
  );

  let noteText = $state("");
  let saving = $state(false);
  let claimFileContent = $state("");
  let loading = $state(false);

  // Toulmin structure extracted from claim
  let toulmin = $derived({
    statement: claim?.statement ?? "",
    grounds: linkedSources.map((s) => s.title || s.key),
    warrant: claim?.type === "causal" ? "Causal mechanism supported by evidence" :
             claim?.type === "comparative" ? "Comparative analysis across sources" :
             claim?.type === "methodological" ? "Methodological basis in literature" :
             "Claim supported by cited evidence",
    qualifications: claim?.confidence === "high" ? "No significant qualifications" :
                    claim?.confidence === "medium" ? "Some limitations noted in evidence" :
                    "Substantial qualifications apply",
  });

  $effect(() => {
    const id = $selectedClaim;
    const dir = $projectDir;
    if (!id || !dir) {
      claimFileContent = "";
      return;
    }

    loading = true;
    readFile(`${dir}/research/claims_matrix.md`)
      .then((raw) => {
        claimFileContent = raw;
      })
      .catch(() => {
        claimFileContent = "";
      })
      .finally(() => {
        loading = false;
      });
  });

  function confidenceColor(confidence: string): string {
    switch (confidence) {
      case "high":
        return "bg-success/20 text-success";
      case "medium":
        return "bg-warning/20 text-warning";
      default:
        return "bg-bg-tertiary text-text-muted";
    }
  }

  function densityPercent(density: number): number {
    return Math.min(Math.max(density * 100, 0), 100);
  }

  function goToSource(source: SourceMeta) {
    selectedSource.set(source.key);
    rightPanel.set("source");
  }

  async function addNote() {
    if (!claim || !noteText.trim() || !$projectDir) return;
    saving = true;
    try {
      const notePath = `${$projectDir}/research/claim-notes/${claim.id}.md`;
      const existing = await readFile(notePath).catch(() => "");
      const updated = existing
        ? `${existing}\n\n> **Human note:** ${noteText.trim()}`
        : `# Notes for ${claim.id}\n\n> **Human note:** ${noteText.trim()}`;
      await writeFile(notePath, updated);
      noteText = "";
    } catch {
      // Silently handle errors
    } finally {
      saving = false;
    }
  }
</script>

{#if !$selectedClaim || !claim}
  <div class="flex h-full items-center justify-center bg-bg p-8">
    <div class="text-center">
      <div class="mb-2 text-3xl text-text-muted">&#9878;</div>
      <p class="text-sm text-text-muted">Select a claim to view details</p>
    </div>
  </div>
{:else if loading}
  <div class="flex h-full items-center justify-center bg-bg">
    <div class="text-sm text-text-muted">Loading claim...</div>
  </div>
{:else}
  <div class="flex h-full flex-col overflow-hidden bg-bg">
    <!-- Claim header -->
    <div class="flex-shrink-0 border-b border-border bg-bg-secondary p-4">
      <div class="mb-2 flex items-start justify-between gap-3">
        <h2 class="text-base font-semibold leading-tight text-text-bright">
          {claim.statement}
        </h2>
        <span
          class="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-medium {confidenceColor(claim.confidence)}"
        >
          {claim.confidence}
        </span>
      </div>

      <div class="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        {#if claim.type}
          <span class="rounded bg-bg-tertiary px-2 py-0.5">{claim.type}</span>
        {/if}
        {#if claim.section}
          <span>&middot; {claim.section}</span>
        {/if}
      </div>

      <!-- Evidence density -->
      <div class="mt-3">
        <div class="mb-1 flex items-center justify-between">
          <span class="text-xs font-medium text-text-muted">Evidence Density</span>
          <span class="text-xs text-text-muted">{(claim.evidence_density * 100).toFixed(0)}%</span>
        </div>
        <div class="h-1.5 w-full overflow-hidden rounded-full bg-bg-tertiary">
          <div
            class="h-full rounded-full transition-all {claim.evidence_density >= 0.7
              ? 'bg-success'
              : claim.evidence_density >= 0.4
                ? 'bg-warning'
                : 'bg-danger'}"
            style="width: {densityPercent(claim.evidence_density)}%"
          ></div>
        </div>
      </div>
    </div>

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- Toulmin structure -->
      <section class="mb-5">
        <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
          Toulmin Structure
        </h3>
        <div class="space-y-3">
          <div>
            <span class="text-xs font-medium text-accent">Statement</span>
            <p class="mt-0.5 text-sm text-text">{toulmin.statement}</p>
          </div>
          <div>
            <span class="text-xs font-medium text-accent">Grounds</span>
            {#if toulmin.grounds.length > 0}
              <ul class="mt-0.5 space-y-0.5">
                {#each toulmin.grounds as ground}
                  <li class="text-sm text-text">&bull; {ground}</li>
                {/each}
              </ul>
            {:else}
              <p class="mt-0.5 text-sm text-text-muted italic">No linked sources</p>
            {/if}
          </div>
          <div>
            <span class="text-xs font-medium text-accent">Warrant</span>
            <p class="mt-0.5 text-sm text-text">{toulmin.warrant}</p>
          </div>
          <div>
            <span class="text-xs font-medium text-accent">Qualifications</span>
            <p class="mt-0.5 text-sm text-text">{toulmin.qualifications}</p>
          </div>
        </div>
      </section>

      <!-- Linked evidence / sources -->
      <section class="mb-5">
        <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
          Evidence ({linkedSources.length} source{linkedSources.length !== 1 ? "s" : ""})
        </h3>
        {#if linkedSources.length === 0}
          <p class="text-xs text-text-muted italic">No sources linked to this claim</p>
        {:else}
          <div class="space-y-1.5">
            {#each linkedSources as src}
              <button
                class="flex w-full items-center gap-2 rounded bg-bg-secondary px-3 py-2 text-left transition-colors hover:bg-bg-tertiary"
                onclick={() => goToSource(src)}
              >
                <div class="min-w-0 flex-1">
                  <p class="truncate text-xs font-medium text-text-bright">
                    {src.title || src.key}
                  </p>
                  {#if src.authors?.length}
                    <p class="truncate text-[10px] text-text-muted">
                      {src.authors.join(", ")}{src.year ? ` (${src.year})` : ""}
                    </p>
                  {/if}
                </div>
                <svg
                  class="h-3 w-3 flex-shrink-0 text-text-muted"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            {/each}
          </div>
        {/if}
      </section>
    </div>

    <!-- Human notes section -->
    <div class="flex-shrink-0 border-t border-border bg-bg-secondary p-4">
      <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
        Human Notes
      </h3>
      <textarea
        bind:value={noteText}
        placeholder="Add a note about this claim..."
        rows="3"
        class="w-full resize-none rounded bg-bg-tertiary p-2 text-xs text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
      ></textarea>
      <div class="mt-2 flex justify-end">
        <button
          class="rounded bg-accent px-3 py-1 text-xs font-medium text-bg transition-colors hover:bg-accent/80 disabled:opacity-50"
          onclick={addNote}
          disabled={saving || !noteText.trim()}
        >
          Add Note
        </button>
      </div>
    </div>
  </div>
{/if}
