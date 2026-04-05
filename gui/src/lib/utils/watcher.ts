import { writable } from "svelte/store";
import { sources, claims, paperState } from "$lib/stores/project";
import { pipelineState } from "$lib/stores/pipeline";
import { listSources, listClaims, readPaperState, startWatching, stopWatching } from "$lib/utils/ipc";
import type { FileChangeEvent } from "$lib/types";

const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

/** Fires when main.tex changes so editor components can react. */
export const texChanged = writable<number>(0);

type RefreshTarget = "sources" | "claims" | "paperState" | "tex";

function classify(path: string): RefreshTarget | null {
  if (path.includes("/research/sources/") || path.includes("\\research\\sources\\")) return "sources";
  if (path.includes("/research/claims/") || path.includes("\\research\\claims\\") || path.endsWith("claims_matrix.md")) return "claims";
  if (path.endsWith(".paper-state.json")) return "paperState";
  if (path.endsWith("/main.tex") || path.endsWith("\\main.tex")) return "tex";
  return null;
}

function debounce<T extends (...args: unknown[]) => void>(fn: T, ms: number): T {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return ((...args: unknown[]) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  }) as unknown as T;
}

/**
 * Start listening for file-change events and sync into Svelte stores.
 * In Tauri mode, uses the Rust backend's FS watcher.
 * In browser mode, file watching is a no-op (no live reload).
 */
export async function setupWatcher(projectDir: string): Promise<() => void> {
  const pending = new Set<RefreshTarget>();

  async function flush() {
    const targets = [...pending];
    pending.clear();

    const tasks: Promise<void>[] = [];

    for (const t of targets) {
      switch (t) {
        case "sources":
          tasks.push(
            listSources(projectDir).then((s) => sources.set(s))
          );
          break;
        case "claims":
          tasks.push(
            listClaims(projectDir).then((c) => claims.set(c as never))
          );
          break;
        case "paperState":
          tasks.push(
            readPaperState(projectDir).then((s) => paperState.set(s))
          );
          break;
        case "tex":
          texChanged.update((n) => n + 1);
          break;
      }
    }

    await Promise.allSettled(tasks);
  }

  const debouncedFlush = debounce(flush, 300);

  // Tell backend to start watching (no-op in browser mode)
  await startWatching(projectDir);

  if (isTauri) {
    // Use Tauri event listener for file changes
    const { listen } = await import("@tauri-apps/api/event");
    const unlisten = await listen<FileChangeEvent>(
      "file-change",
      (event) => {
        const target = classify(event.payload.path);
        if (target) {
          pending.add(target);
          debouncedFlush();
        }
      }
    );

    const unlistenPipeline = await listen<{ currentStage: string; stages: Record<string, any> }>(
      "pipeline-progress",
      (event) => {
        pipelineState.update((s) => ({
          ...s,
          currentStage: event.payload.currentStage,
          stages: event.payload.stages,
        }));
      }
    );

    return async function cleanup() {
      unlisten();
      unlistenPipeline();
      await stopWatching();
    } as unknown as () => void;
  } else {
    // Browser mode: no live file watching
    return async function cleanup() {
      await stopWatching();
    } as unknown as () => void;
  }
}
