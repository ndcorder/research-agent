import { writable } from "svelte/store";

export interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration: number;
}

let nextId = 0;

function createToastStore() {
  const { subscribe, update } = writable<Toast[]>([]);

  function add(
    message: string,
    type: Toast["type"] = "info",
    duration = 3000
  ) {
    const id = nextId++;
    update((toasts) => [...toasts, { id, message, type, duration }]);
    if (duration > 0) {
      setTimeout(() => remove(id), duration);
    }
  }

  function remove(id: number) {
    update((toasts) => toasts.filter((t) => t.id !== id));
  }

  return {
    subscribe,
    success: (msg: string) => add(msg, "success"),
    error: (msg: string, duration = 5000) => add(msg, "error", duration),
    info: (msg: string) => add(msg, "info"),
    warning: (msg: string) => add(msg, "warning"),
    remove,
  };
}

export const toasts = createToastStore();
