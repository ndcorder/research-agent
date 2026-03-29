<script lang="ts">
  import { sources, claims, wordCount, texContent } from "$lib/stores/project";
  import { parseCiteKeys } from "$lib/utils/latex";

  // --- Derived data ---

  let citationCount = $derived(parseCiteKeys($texContent).length);

  let statusCounts = $derived.by(() => {
    const counts: Record<string, number> = {
      verified: 0,
      flagged: 0,
      "needs-replacement": 0,
      "human-added": 0,
      unknown: 0,
    };
    for (const s of $sources) {
      const status = s.status || "unknown";
      if (status in counts) counts[status]++;
      else counts["unknown"]++;
    }
    return counts;
  });

  let yearDistribution = $derived.by(() => {
    const years: Record<number, number> = {};
    for (const s of $sources) {
      if (s.year) {
        years[s.year] = (years[s.year] || 0) + 1;
      }
    }
    return Object.entries(years)
      .map(([year, count]) => ({ year: Number(year), count }))
      .sort((a, b) => a.year - b.year);
  });

  let tagFrequencies = $derived.by(() => {
    const freq: Record<string, number> = {};
    for (const s of $sources) {
      if (s.tags) {
        for (const tag of s.tags) {
          freq[tag] = (freq[tag] || 0) + 1;
        }
      }
    }
    return Object.entries(freq)
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count);
  });

  let evidenceCoverage = $derived.by(() => {
    return $claims.map((claim) => {
      const supportCount = $sources.filter(
        (s) => s.evidence_for?.includes(claim.id)
      ).length;
      return { claim, supportCount };
    });
  });

  // --- Donut chart helpers ---

  const STATUS_COLORS: Record<string, string> = {
    verified: "#9ece6a",
    flagged: "#e0af68",
    "needs-replacement": "#f7768e",
    "human-added": "#7dcfff",
    unknown: "#565f89",
  };

  const STATUS_LABELS: Record<string, string> = {
    verified: "Verified",
    flagged: "Flagged",
    "needs-replacement": "Needs Replacement",
    "human-added": "Human Added",
    unknown: "Unknown",
  };

  function donutSegments(counts: Record<string, number>) {
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    if (total === 0) return [];

    const segments: Array<{
      key: string;
      color: string;
      offset: number;
      length: number;
      count: number;
    }> = [];
    let cumulative = 0;
    const circumference = 2 * Math.PI * 40; // r=40

    for (const [key, count] of Object.entries(counts)) {
      if (count === 0) continue;
      const length = (count / total) * circumference;
      segments.push({
        key,
        color: STATUS_COLORS[key] || "#565f89",
        offset: cumulative,
        length,
        count,
      });
      cumulative += length;
    }
    return segments;
  }

  // --- Bar chart helpers ---

  function barMaxCount(years: Array<{ year: number; count: number }>) {
    return Math.max(...years.map((y) => y.count), 1);
  }

  // --- Tag click dispatch ---

  function handleTagClick(tag: string) {
    // Dispatch a custom event that the sidebar can listen to
    window.dispatchEvent(
      new CustomEvent("research-dashboard:filter-tag", { detail: { tag } })
    );
  }

  // --- Evidence bar color ---

  function evidenceColor(count: number): string {
    if (count >= 3) return "#9ece6a";
    if (count === 2) return "#e0af68";
    return "#f7768e";
  }

  function evidenceBgClass(count: number): string {
    if (count >= 3) return "bg-success/20";
    if (count === 2) return "bg-warning/20";
    return "bg-danger/20";
  }
</script>

<div class="flex h-full flex-col overflow-y-auto bg-bg p-4">
  <!-- Row 1: Key Metrics -->
  <div class="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
    <!-- Total Sources -->
    <div class="rounded-lg border border-border bg-bg-secondary p-4">
      <div class="text-xs uppercase tracking-wide text-text-muted">Sources</div>
      <div class="mt-1 text-2xl font-bold text-text-bright">{$sources.length}</div>
    </div>

    <!-- Total Claims -->
    <div class="rounded-lg border border-border bg-bg-secondary p-4">
      <div class="text-xs uppercase tracking-wide text-text-muted">Claims</div>
      <div class="mt-1 text-2xl font-bold text-text-bright">{$claims.length}</div>
    </div>

    <!-- Word Count -->
    <div class="rounded-lg border border-border bg-bg-secondary p-4">
      <div class="text-xs uppercase tracking-wide text-text-muted">Words</div>
      <div class="mt-1 text-2xl font-bold text-text-bright">
        {$wordCount.toLocaleString()}
      </div>
    </div>

    <!-- Citations -->
    <div class="rounded-lg border border-border bg-bg-secondary p-4">
      <div class="text-xs uppercase tracking-wide text-text-muted">Citations</div>
      <div class="mt-1 text-2xl font-bold text-text-bright">{citationCount}</div>
    </div>
  </div>

  <!-- Row 2: Source Status Donut -->
  <div class="mb-4 rounded-lg border border-border bg-bg-secondary p-4">
    <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
      Source Status Breakdown
    </h3>
    <div class="flex flex-col items-center gap-4 sm:flex-row">
      <!-- Donut SVG -->
      <div class="relative flex-shrink-0">
        <svg width="120" height="120" viewBox="0 0 100 100">
          {#if $sources.length === 0}
            <circle
              cx="50" cy="50" r="40"
              fill="none"
              stroke="#3b3f5c"
              stroke-width="12"
            />
          {:else}
            {#each donutSegments(statusCounts) as seg}
              <circle
                cx="50" cy="50" r="40"
                fill="none"
                stroke={seg.color}
                stroke-width="12"
                stroke-dasharray="{seg.length} {2 * Math.PI * 40 - seg.length}"
                stroke-dashoffset={-seg.offset}
                transform="rotate(-90 50 50)"
                class="transition-all duration-300"
              />
            {/each}
          {/if}
          <text x="50" y="48" text-anchor="middle" fill="#e0e6ff" font-size="16" font-weight="bold">
            {$sources.length}
          </text>
          <text x="50" y="60" text-anchor="middle" fill="#565f89" font-size="7">
            total
          </text>
        </svg>
      </div>

      <!-- Legend -->
      <div class="flex flex-wrap gap-x-4 gap-y-2">
        {#each Object.entries(STATUS_COLORS) as [key, color]}
          {@const count = statusCounts[key] || 0}
          {#if count > 0}
            <div class="flex items-center gap-1.5">
              <span
                class="inline-block h-2.5 w-2.5 rounded-full"
                style="background-color: {color}"
              ></span>
              <span class="text-xs text-text">{STATUS_LABELS[key]}</span>
              <span class="text-xs font-medium text-text-bright">{count}</span>
            </div>
          {/if}
        {/each}
      </div>
    </div>
  </div>

  <!-- Row 3: Source Year Distribution -->
  <div class="mb-4 rounded-lg border border-border bg-bg-secondary p-4">
    <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
      Source Year Distribution
    </h3>
    {#if yearDistribution.length === 0}
      <div class="py-4 text-center text-xs text-text-muted">No year data available</div>
    {:else}
      <div class="space-y-1.5">
        {#each yearDistribution as { year, count }}
          {@const maxCount = barMaxCount(yearDistribution)}
          {@const pct = (count / maxCount) * 100}
          <div class="flex items-center gap-2">
            <span class="w-10 text-right text-xs text-text-muted">{year}</span>
            <div class="flex-1">
              <svg width="100%" height="18" viewBox="0 0 200 18" preserveAspectRatio="none">
                <rect
                  x="0" y="2" width={pct * 2} height="14"
                  rx="3" ry="3"
                  fill="#7aa2f7"
                  opacity="0.7"
                  class="transition-all duration-300"
                />
              </svg>
            </div>
            <span class="w-6 text-right text-xs font-medium text-text-bright">{count}</span>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Row 4: Tag Cloud -->
  <div class="mb-4 rounded-lg border border-border bg-bg-secondary p-4">
    <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
      Tag Cloud
    </h3>
    {#if tagFrequencies.length === 0}
      <div class="py-4 text-center text-xs text-text-muted">No tags found</div>
    {:else}
      {@const maxFreq = Math.max(...tagFrequencies.map((t) => t.count))}
      <div class="flex flex-wrap gap-2">
        {#each tagFrequencies as { tag, count }}
          {@const minSize = 11}
          {@const maxSize = 20}
          {@const size = maxFreq > 1
            ? minSize + ((count - 1) / (maxFreq - 1)) * (maxSize - minSize)
            : 14}
          <button
            class="rounded-full bg-bg-tertiary px-2 py-0.5 text-text transition-colors hover:bg-accent/20 hover:text-accent"
            style="font-size: {size}px"
            onclick={() => handleTagClick(tag)}
            title="{count} source{count !== 1 ? 's' : ''}"
          >
            {tag}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Row 5: Evidence Coverage -->
  <div class="rounded-lg border border-border bg-bg-secondary p-4">
    <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
      Evidence Coverage
    </h3>
    {#if evidenceCoverage.length === 0}
      <div class="py-4 text-center text-xs text-text-muted">No claims to evaluate</div>
    {:else}
      <div class="space-y-2">
        {#each evidenceCoverage as { claim, supportCount }}
          <div class="rounded px-2 py-1.5 {evidenceBgClass(supportCount)}">
            <div class="mb-1 flex items-center justify-between gap-2">
              <span class="min-w-0 truncate text-xs text-text">{claim.statement}</span>
              <span
                class="flex-shrink-0 text-xs font-bold"
                style="color: {evidenceColor(supportCount)}"
              >
                {supportCount}
              </span>
            </div>
            <div class="h-1.5 overflow-hidden rounded-full bg-bg-tertiary">
              <div
                class="h-full rounded-full transition-all duration-300"
                style="width: {Math.min(supportCount / 5 * 100, 100)}%; background-color: {evidenceColor(supportCount)}"
              ></div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
