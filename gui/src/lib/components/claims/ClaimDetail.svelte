<script lang="ts">
  import {
    claims,
    selectedClaim,
    sources,
    selectedSource,
    rightPanel,
    projectDir,
  } from "$lib/stores/project";
  import { readFile, listClaims, updateClaim } from "$lib/utils/ipc";
  import type { ClaimMeta, SourceMeta } from "$lib/types";
  import SourceLinker from "./SourceLinker.svelte";

  let claim = $derived<ClaimMeta | undefined>(
    $claims.find((c) => c.id === $selectedClaim)
  );

  // Parse source keys from the claim's evidence_sources string
  function extractSourceKeys(evidenceStr: string | undefined): string[] {
    if (!evidenceStr) return [];
    return evidenceStr
      .split(",")
      .map((entry) => entry.trim().split(/\s/)[0])
      .filter(Boolean);
  }

  let linkedSources = $derived<SourceMeta[]>(
    claim
      ? (() => {
          const keys = extractSourceKeys(claim.evidence_sources);
          const byEvidence = $sources.filter((s) => keys.includes(s.key));
          if (byEvidence.length > 0) return byEvidence;
          return $sources.filter(
            (s) =>
              s.evidence_for?.includes(claim!.id) ||
              s.tags?.includes(claim!.id)
          );
        })()
      : []
  );

  let loading = $state(false);
  let editing = $state(false);
  let saving = $state(false);
  let saveError = $state("");

  // Edit form state
  let editStatement = $state("");
  let editConfidence = $state("");
  let editWarrant = $state("");
  let editQualifier = $state("");
  let editRebuttal = $state("");
  let editStatus = $state("");
  let editEvidence = $state("");

  function startEdit() {
    if (!claim) return;
    editStatement = claim.statement;
    editConfidence = claim.confidence;
    editWarrant = claim.warrant ?? "";
    editQualifier = claim.qualifier ?? "";
    editRebuttal = claim.rebuttal ?? "";
    editStatus = claim.status ?? "Active";
    editEvidence = claim.evidence_sources ?? "";
    saveError = "";
    editing = true;
  }

  function discardEdit() {
    editing = false;
    saveError = "";
  }

  async function saveEdit() {
    if (!claim || !$projectDir) return;
    saving = true;
    saveError = "";

    try {
      const updates: Record<string, string> = {};

      if (editStatement !== claim.statement) updates.statement = editStatement;
      if (editConfidence !== claim.confidence) updates.confidence = editConfidence;
      if (editWarrant !== (claim.warrant ?? "")) updates.warrant = editWarrant;
      if (editQualifier !== (claim.qualifier ?? "")) updates.qualifier = editQualifier;
      if (editRebuttal !== (claim.rebuttal ?? "")) updates.rebuttal = editRebuttal;
      if (editStatus !== (claim.status ?? "")) updates.status = editStatus;
      if (editEvidence !== (claim.evidence_sources ?? "")) updates.evidence_sources = editEvidence;

      if (Object.keys(updates).length === 0) {
        editing = false;
        return;
      }

      await updateClaim($projectDir, claim.id, updates);

      // Refresh claims from disk
      const refreshed = await listClaims($projectDir);
      claims.set(refreshed as ClaimMeta[]);

      editing = false;
    } catch (e: unknown) {
      saveError = e instanceof Error ? e.message : "Save failed";
    } finally {
      saving = false;
    }
  }

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

  function goToSource(source: SourceMeta) {
    selectedSource.set(source.key);
    rightPanel.set("source");
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
        {#if editing}
          <textarea
            bind:value={editStatement}
            rows="2"
            class="flex-1 resize-none rounded bg-bg-tertiary p-2 text-sm font-semibold leading-tight text-text-bright outline-none focus:ring-1 focus:ring-accent"
          ></textarea>
        {:else}
          <h2 class="text-base font-semibold leading-tight text-text-bright">
            {claim.statement}
          </h2>
        {/if}

        {#if editing}
          <!-- Confidence toggle group -->
          <div class="flex flex-shrink-0 gap-0.5 rounded bg-bg-tertiary p-0.5">
            {#each [["high", "H"], ["medium", "M"], ["low", "L"]] as [val, label]}
              <button
                class="rounded px-2 py-0.5 text-xs font-medium transition-colors {editConfidence === val
                  ? confidenceColor(val)
                  : 'text-text-muted hover:text-text'}"
                onclick={() => (editConfidence = val)}
              >
                {label}
              </button>
            {/each}
          </div>
        {:else}
          <button
            class="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-medium {confidenceColor(claim.confidence)}"
            onclick={startEdit}
            title="Click to edit"
          >
            {claim.confidence}
          </button>
        {/if}
      </div>

      <div class="flex flex-wrap items-center gap-2 text-xs text-text-muted">
        {#if claim.type}
          <span class="rounded bg-bg-tertiary px-2 py-0.5">{claim.type}</span>
        {/if}
        {#if claim.section}
          <span>&middot; {claim.section}</span>
        {/if}
        {#if editing}
          <span>&middot;</span>
          <select
            bind:value={editStatus}
            class="rounded bg-bg-tertiary px-2 py-0.5 text-xs text-text outline-none"
          >
            <option value="Active">Active</option>
            <option value="Flagged">Flagged</option>
            <option value="Resolved">Resolved</option>
            <option value="Cut">Cut</option>
          </select>
        {:else if claim.status}
          <span>&middot; {claim.status}</span>
        {/if}
      </div>

      <!-- Evidence density bar (read-only, auto-updates when sources change) -->
      {#snippet densityBar()}
        {@const density = editing
          ? editEvidence.split(",").filter((e) => e.trim()).length
          : claim.evidence_density}
        <div class="mt-3">
          <div class="mb-1 flex items-center justify-between">
            <span class="text-xs font-medium text-text-muted">Evidence Density</span>
            <span class="text-xs text-text-muted"
              >{density} source{density !== 1 ? "s" : ""}</span
            >
          </div>
          <div class="h-1.5 w-full overflow-hidden rounded-full bg-bg-tertiary">
            <div
              class="h-full rounded-full transition-all {density >= 7
                ? 'bg-success'
                : density >= 4
                  ? 'bg-warning'
                  : 'bg-danger'}"
              style="width: {Math.min((density / 10) * 100, 100)}%"
            ></div>
          </div>
        </div>
      {/snippet}
      {@render densityBar()}
    </div>

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto p-4">
      {#if editing}
        <!-- Edit mode: Toulmin fields -->
        <section class="mb-5 space-y-3">
          <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Toulmin Structure
          </h3>

          <div>
            <label class="text-xs font-medium text-accent">Warrant</label>
            {#if claim.warrant && claim.warrant.startsWith("[AUTO")}
              <p class="mt-0.5 text-xs text-text-muted/60">Auto-resolved by pipeline</p>
            {/if}
            <textarea
              bind:value={editWarrant}
              rows="3"
              placeholder="The reasoning that connects evidence to the claim..."
              class="mt-1 w-full resize-none rounded bg-bg-tertiary p-2 text-sm text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
            ></textarea>
          </div>

          <div>
            <label class="text-xs font-medium text-accent">Qualifier</label>
            <input
              type="text"
              bind:value={editQualifier}
              placeholder="Hedging language (e.g. 'in most cases', 'for populations >100')"
              class="mt-1 w-full rounded bg-bg-tertiary px-2 py-1.5 text-sm text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
            />
          </div>

          <div>
            <label class="text-xs font-medium text-accent">Rebuttal</label>
            <textarea
              bind:value={editRebuttal}
              rows="2"
              placeholder="Known counterarguments or limitations..."
              class="mt-1 w-full resize-none rounded bg-bg-tertiary p-2 text-sm text-text placeholder-text-muted outline-none focus:ring-1 focus:ring-accent"
            ></textarea>
          </div>
        </section>

        <!-- Edit mode: Source linking -->
        <section class="mb-5">
          <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Evidence Sources
          </h3>
          <SourceLinker
            evidenceSources={editEvidence}
            onUpdate={(v) => (editEvidence = v)}
          />
        </section>
      {:else}
        <!-- Read mode: Toulmin structure -->
        <section class="mb-5">
          <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Toulmin Structure
          </h3>
          <div class="space-y-3">
            <div>
              <span class="text-xs font-medium text-accent">Statement</span>
              <p class="mt-0.5 text-sm text-text">{claim.statement}</p>
            </div>
            <div>
              <span class="text-xs font-medium text-accent">Grounds</span>
              {#if linkedSources.length > 0}
                <ul class="mt-0.5 space-y-0.5">
                  {#each linkedSources as ground}
                    <li class="text-sm text-text">&bull; {ground.title || ground.key}</li>
                  {/each}
                </ul>
              {:else}
                <p class="mt-0.5 text-sm text-text-muted italic">No linked sources</p>
              {/if}
            </div>
            <div>
              <span class="text-xs font-medium text-accent">Warrant</span>
              <p class="mt-0.5 text-sm text-text">
                {#if claim.warrant}
                  {claim.warrant}
                {:else}
                  {claim.type === "causal"
                    ? "Causal mechanism supported by evidence"
                    : claim.type === "comparative"
                      ? "Comparative analysis across sources"
                      : claim.type === "methodological"
                        ? "Methodological basis in literature"
                        : "Claim supported by cited evidence"}
                {/if}
              </p>
            </div>
            <div>
              <span class="text-xs font-medium text-accent">Qualifier</span>
              <p class="mt-0.5 text-sm text-text">
                {#if claim.qualifier}
                  {claim.qualifier}
                {:else}
                  {claim.confidence === "high"
                    ? "No significant qualifications"
                    : claim.confidence === "medium"
                      ? "Some limitations noted in evidence"
                      : "Substantial qualifications apply"}
                {/if}
              </p>
            </div>
            {#if claim.rebuttal}
              <div>
                <span class="text-xs font-medium text-accent">Rebuttal</span>
                <p class="mt-0.5 text-sm text-text">{claim.rebuttal}</p>
              </div>
            {/if}
          </div>
        </section>

        <!-- Read mode: Linked evidence -->
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
                      <p class="truncate text-xs text-text-muted">
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
      {/if}
    </div>

    <!-- Action bar -->
    <div class="flex-shrink-0 border-t border-border bg-bg-secondary p-4">
      {#if editing}
        {#if saveError}
          <p class="mb-2 text-xs text-danger">{saveError}</p>
        {/if}
        <div class="flex items-center justify-end gap-2">
          <button
            class="rounded px-3 py-1.5 text-xs text-text-muted transition-colors hover:bg-bg-tertiary"
            onclick={discardEdit}
            disabled={saving}
          >
            Discard
          </button>
          <button
            class="rounded bg-accent px-4 py-1.5 text-xs font-medium text-bg transition-colors hover:bg-accent/80 disabled:opacity-50"
            onclick={saveEdit}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      {:else}
        <button
          class="w-full rounded bg-bg-tertiary px-3 py-1.5 text-xs font-medium text-text transition-colors hover:bg-accent/10 hover:text-accent"
          onclick={startEdit}
        >
          Edit Claim
        </button>
      {/if}
    </div>
  </div>
{/if}
