<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    variant,
    children,
  }: {
    variant: "success" | "warning" | "danger" | "info" | "muted";
    children: Snippet;
  } = $props();

  const variantClasses: Record<string, string> = {
    success: "bg-success/15 text-success",
    warning: "bg-warning/15 text-warning",
    danger: "bg-danger/15 text-danger",
    info: "bg-info/15 text-info",
    muted: "bg-text-muted/15 text-text-muted",
  };
</script>

<span
  class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium leading-tight {variantClasses[variant]}"
>
  {@render children()}
</span>
