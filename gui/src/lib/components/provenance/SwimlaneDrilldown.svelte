<script lang="ts">
  import type { ProvenanceEntry } from "$lib/types";
  import { actionDotColor } from "$lib/utils/provenanceUtils";

  interface Props {
    target: string;
    events: ProvenanceEntry[];
    onsourceclick?: (key: string) => void;
    onfeedbackclick?: (ref: string) => void;
  }

  let { target, events, onsourceclick, onfeedbackclick }: Props = $props();

  let expandedCards = $state<Set<number>>(new Set());

  function toggleCard(index: number) {
    const next = new Set(expandedCards);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    expandedCards = next;
  }

  function formatTimestamp(ts?: string): string {
    if (!ts) return "";
    const date = new Date(ts);
    if (isNaN(date.getTime())) return ts;
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function actionBadgeClass(action: string): string {
    const a = action.toLowerCase();
    if (a === "write" || a === "add")
      return "bg-success/20 text-success border-success/30";
    if (a === "revise")
      return "bg-info/20 text-info border-info/30";
    if (a === "expand" || a === "reorder")
      return "bg-warning/20 text-warning border-warning/30";
    if (a === "cut" || a === "remove")
      return "bg-danger/20 text-danger border-danger/30";
    return "bg-bg-tertiary text-text-muted border-border";
  }

  function truncate(text: string, maxLen: number): string {
    if (text.length <= maxLen) return text;
    return text.slice(0, maxLen) + "\u2026";
  }
</script>

<div class="border-t border-border bg-bg-secondary/80 px-3 py-2">
  <div class="mb-2 flex items-center gap-2">
    <span class="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
      Lifecycle
    </span>
    <span class="text-xs font-medium text-accent">{target}</span>
    <span class="text-[10px] text-text-muted">
      {events.length} event{events.length !== 1 ? "s" : ""}
    </span>
  </div>

  <div class="space-y-1.5">
    {#each events as event, i}
      {@const isExpanded = expandedCards.has(i)}

      <button
        class="w-full rounded border border-border bg-bg p-2 text-left transition-colors hover:border-border/80"
        onclick={() => toggleCard(i)}
      >
        <!-- Header row -->
        <div class="flex items-center gap-2">
          <span
            class="inline-block h-2 w-2 shrink-0 rounded-full"
            style="background: {actionDotColor(event.action)}"
          ></span>
          <span
            class="rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider {actionBadgeClass(event.action)}"
          >
            {event.action}
          </span>
          {#if event.agent}
            <span class="text-xs text-text-bright">{event.agent}</span>
          {/if}
          {#if event.stage}
            <span class="rounded bg-bg-tertiary px-1.5 py-0.5 text-[10px] text-text-muted">
              Stage {event.stage}
            </span>
          {/if}
          <span class="ml-auto shrink-0 text-[10px] text-text-muted">
            {formatTimestamp(event.timestamp)}
          </span>
          <span class="text-[10px] text-text-muted transition-transform {isExpanded ? 'rotate-90' : ''}">
            &#9654;
          </span>
        </div>

        <!-- Expanded details -->
        {#if isExpanded}
          <div class="mt-2 space-y-1.5 border-t border-border/50 pt-2">
            {#if event.reasoning}
              <div>
                <span class="text-[10px] font-medium uppercase text-text-muted">Reasoning</span>
                <p class="mt-0.5 text-xs leading-relaxed text-text">
                  {event.reasoning}
                </p>
              </div>
            {/if}

            {#if event.diff_summary}
              <div>
                <span class="text-[10px] font-medium uppercase text-text-muted">Changes</span>
                <p class="mt-0.5 font-mono text-[11px] leading-relaxed text-text-muted">
                  {event.diff_summary}
                </p>
              </div>
            {/if}

            {#if event.details}
              <div>
                <span class="text-[10px] font-medium uppercase text-text-muted">Details</span>
                <p class="mt-0.5 text-xs leading-relaxed text-text-muted">
                  {event.details}
                </p>
              </div>
            {/if}

            <!-- Source badges -->
            {#if event.sources && event.sources.length > 0}
              <div>
                <span class="text-[10px] font-medium uppercase text-text-muted">Sources</span>
                <div class="mt-1 flex flex-wrap gap-1">
                  {#each event.sources as src}
                    <button
                      class="rounded bg-accent/10 px-1.5 py-0.5 text-[10px] font-medium text-accent transition-colors hover:bg-accent/20"
                      onclick={(e: MouseEvent) => { e.stopPropagation(); onsourceclick?.(src); }}
                    >
                      {src}
                    </button>
                  {/each}
                </div>
              </div>
            {/if}

            <!-- Feedback ref link -->
            {#if event.feedback_ref}
              <div>
                <button
                  class="text-[10px] text-info underline decoration-info/30 transition-colors hover:text-info/80"
                  onclick={(e: MouseEvent) => { e.stopPropagation(); onfeedbackclick?.(event.feedback_ref!); }}
                >
                  View QA feedback &rarr;
                </button>
              </div>
            {/if}
          </div>
        {/if}
      </button>
    {/each}
  </div>
</div>
