import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { writable } from "svelte/store";
import { sources, claims, paperState } from "$lib/stores/project";
import { listSources, listClaims, readPaperState, startWatching, stopWatching } from "$lib/utils/ipc";
import type { FileChangeEvent } from "$lib/types";

/** Fires when main.tex changes so editor components can react. */
export const texChanged = writable<number>(0);

type RefreshTarget = "sources" | "claims" | "paperState" | "tex";

function classify(path: string): RefreshTarget | null {
  if (path.includes("/research/sources/") || path.includes("\\research\\sources\\")) return "sources";
  if (path.includes("/research/claims/") || path.includes("\\research\\claims\\")) return "claims";
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
 * Start listening for file-change events from the Rust backend
 * and sync relevant changes into Svelte stores.
 *
 * Returns a cleanup function that stops the watcher and removes the event listener.
 */
export async function setupWatcher(projectDir: string): Promise<() => void> {
  // Track which targets need refreshing so we can coalesce rapid bursts.
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

  // Tell the Rust backend to start the FS watcher for this project.
  await startWatching(projectDir);

  // Listen for events emitted by the Rust backend.
  const unlisten: UnlistenFn = await listen<FileChangeEvent>(
    "file-change",
    (event) => {
      const target = classify(event.payload.path);
      if (target) {
        pending.add(target);
        debouncedFlush();
      }
    }
  );

  return async function cleanup() {
    unlisten();
    await stopWatching();
  } as unknown as () => void;
}
