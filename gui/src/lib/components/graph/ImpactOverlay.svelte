<script lang="ts">
  import type { SourceMeta, ClaimMeta } from "$lib/types";
  import { extractSourceKeys } from "./graphUtils";

  interface Props {
    sourceKey: string;
    sources: SourceMeta[];
    claims: ClaimMeta[];
    visible: boolean;
    onclose: () => void;
  }

  let { sourceKey, sources, claims, visible, onclose }: Props = $props();

  type ImpactLevel = "critical" | "degraded" | "safe";

  interface ClaimImpact {
    claim: ClaimMeta;
    originalDensity: number;
    newDensity: number;
    level: ImpactLevel;
  }



  function densityTier(density: number): string {
    if (density < 1) return "critical";
    if (density < 2) return "weak";
    if (density < 3) return "moderate";
    return "strong";
  }

  function computeImpact(
    sourceKey: string,
    claimList: ClaimMeta[],
  ): ClaimImpact[] {
    const results: ClaimImpact[] = [];

    for (const claim of claimList) {
      const keys = extractSourceKeys(claim.evidence_sources);
      if (!keys.includes(sourceKey)) continue;

      const originalDensity = claim.evidence_density;
      // Each source contributes roughly 1 to evidence_density.
      // Approximate new density by subtracting the proportion this source represents.
      const sourceCount = keys.length;
      const newDensity = sourceCount > 1
        ? originalDensity * ((sourceCount - 1) / sourceCount)
        : 0;

      const originalTier = densityTier(originalDensity);
      const newTier = densityTier(newDensity);

      let level: ImpactLevel;
      if (newDensity < 1) {
        level = "critical";
      } else if (newTier !== originalTier) {
        level = "degraded";
      } else {
        level = "safe";
      }

      results.push({ claim, originalDensity, newDensity, level });
    }

    // Sort: critical first, then degraded, then safe
    const order: Record<ImpactLevel, number> = { critical: 0, degraded: 1, safe: 2 };
    results.sort((a, b) => order[a.level] - order[b.level]);

    return results;
  }

  let impactData = $derived(computeImpact(sourceKey, claims));

  let criticalCount = $derived(impactData.filter((d) => d.level === "critical").length);
  let degradedCount = $derived(impactData.filter((d) => d.level === "degraded").length);

  function levelLabel(level: ImpactLevel): string {
    switch (level) {
      case "critical":
        return "CRIT";
      case "degraded":
        return "WEAK";
      case "safe":
        return "OK";
    }
  }

  function levelColorClass(level: ImpactLevel): string {
    switch (level) {
      case "critical":
        return "text-danger";
      case "degraded":
        return "text-warning";
      case "safe":
        return "text-text-muted";
    }
  }

  function truncate(text: string, max: number): string {
    if (text.length <= max) return text;
    return text.slice(0, max - 1) + "\u2026";
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && visible) {
      e.stopPropagation();
      onclose();
    }
  }

</script>

<svelte:window onkeydown={handleKeydown} />

{#if visible}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="absolute bottom-4 left-1/2 -translate-x-1/2 z-50 bg-bg-secondary border border-border rounded-lg shadow-xl p-3 text-xs min-w-80 max-w-lg"
    onclick={(e) => e.stopPropagation()}
    role="dialog"
    tabindex="-1"
    aria-label="Source removal impact analysis"
  >
    <div class="font-semibold text-text-bright mb-1">
      Impact: Removing "{sourceKey}"
    </div>

    {#if impactData.length === 0}
      <div class="text-text-muted mb-2">
        <span class="text-success">This source is not cited by any claims.</span>
      </div>
    {:else}
      <div class="text-text-muted mb-2">
        {#if criticalCount > 0}
          <span class="text-danger">{criticalCount} claim{criticalCount !== 1 ? "s" : ""} become CRITICAL</span>
        {/if}
        {#if criticalCount > 0 && degradedCount > 0}
          <span> &middot; </span>
        {/if}
        {#if degradedCount > 0}
          <span class="text-warning">{degradedCount} drop{degradedCount !== 1 ? "" : "s"} to WEAK</span>
        {/if}
        {#if criticalCount === 0 && degradedCount === 0}
          <span class="text-success">No critical impact</span>
        {/if}
      </div>

      <div class="border border-border rounded p-2 max-h-40 overflow-y-auto space-y-1">
        {#each impactData as item}
          <div class="flex items-start gap-2">
            <span class={levelColorClass(item.level)}>&bull;</span>
            <span class="flex-1 text-text">
              {item.claim.id}: "{truncate(item.claim.statement, 40)}"
            </span>
            <span class={`font-semibold shrink-0 ${levelColorClass(item.level)}`}>
              &rarr; {levelLabel(item.level)}
            </span>
          </div>
        {/each}
      </div>
    {/if}

    <div class="flex justify-end mt-2">
      <button
        class="px-3 py-1 rounded bg-bg-tertiary border border-border text-text-muted hover:text-text hover:border-text-muted transition-colors cursor-pointer"
        onclick={onclose}
        aria-label="Close impact overlay"
      >
        Close
      </button>
    </div>
  </div>
{/if}
