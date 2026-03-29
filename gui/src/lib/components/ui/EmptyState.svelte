<script lang="ts">
  let {
    icon,
    title,
    description,
    action,
  }: {
    icon: string;
    title: string;
    description?: string;
    action?: { label: string; onclick: () => void };
  } = $props();
</script>

<div class="flex flex-col items-center justify-center px-4 py-8 text-center">
  <span class="mb-2 text-2xl opacity-40">{icon}</span>
  <p class="text-xs font-medium text-text-muted">{title}</p>
  {#if description}
    <p class="mt-1 max-w-48 text-xs leading-snug text-text-muted/70">{description}</p>
  {/if}
  {#if action}
    <button
      class="mt-3 rounded bg-accent/15 px-3 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/25"
      onclick={action.onclick}
    >
      {action.label}
    </button>
  {/if}
</div>
