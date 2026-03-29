<script lang="ts" module>
  export interface ContextMenuItem {
    label: string;
    icon?: string;
    action: () => void;
    separator?: boolean;
    disabled?: boolean;
    children?: ContextMenuItem[];
  }
</script>

<script lang="ts">
  interface Props {
    items: ContextMenuItem[];
    x: number;
    y: number;
    visible: boolean;
    onclose: () => void;
  }

  let { items, x, y, visible, onclose }: Props = $props();

  let backdropEl: HTMLDivElement | undefined = $state();
  let menuEl: HTMLDivElement | undefined = $state();
  let selectedIndex = $state(-1);
  let openSubmenuIndex = $state(-1);
  let submenuSelectedIndex = $state(-1);
  let adjustedX = $state(0);
  let adjustedY = $state(0);

  // Adjust position to stay within viewport
  $effect(() => {
    if (visible && menuEl) {
      const rect = menuEl.getBoundingClientRect();
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      adjustedX = x + rect.width > vw ? vw - rect.width - 4 : x;
      adjustedY = y + rect.height > vh ? vh - rect.height - 4 : y;
    } else {
      adjustedX = x;
      adjustedY = y;
    }
  });

  // Reset state and focus backdrop when menu opens
  $effect(() => {
    if (visible) {
      selectedIndex = -1;
      openSubmenuIndex = -1;
      submenuSelectedIndex = -1;
      // Focus backdrop so keyboard events are captured
      backdropEl?.focus();
    }
  });

  // Close on click outside
  function onBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      onclose();
    }
  }

  // Keyboard navigation
  function onKeydown(e: KeyboardEvent) {
    if (!visible) return;

    if (e.key === "Escape") {
      e.preventDefault();
      if (openSubmenuIndex !== -1) {
        openSubmenuIndex = -1;
        submenuSelectedIndex = -1;
      } else {
        onclose();
      }
      return;
    }

    // If a submenu is open and focused
    if (openSubmenuIndex !== -1 && submenuSelectedIndex !== -1) {
      const sub = items[openSubmenuIndex]?.children;
      if (!sub) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        submenuSelectedIndex = findNextEnabled(sub, submenuSelectedIndex, 1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        submenuSelectedIndex = findNextEnabled(sub, submenuSelectedIndex, -1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        openSubmenuIndex = -1;
        submenuSelectedIndex = -1;
      } else if (e.key === "Enter") {
        e.preventDefault();
        const item = sub[submenuSelectedIndex];
        if (item && !item.disabled) {
          item.action();
          onclose();
        }
      }
      return;
    }

    // Main menu navigation
    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = findNextEnabled(items, selectedIndex, 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = findNextEnabled(items, selectedIndex, -1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      const item = items[selectedIndex];
      if (item?.children?.length) {
        openSubmenuIndex = selectedIndex;
        submenuSelectedIndex = findNextEnabled(item.children, -1, 1);
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = items[selectedIndex];
      if (item && !item.disabled) {
        if (item.children?.length) {
          openSubmenuIndex = selectedIndex;
          submenuSelectedIndex = findNextEnabled(item.children, -1, 1);
        } else {
          item.action();
          onclose();
        }
      }
    }
  }

  function findNextEnabled(list: ContextMenuItem[], current: number, direction: 1 | -1): number {
    const len = list.length;
    let next = current + direction;
    for (let i = 0; i < len; i++) {
      if (next < 0) next = len - 1;
      if (next >= len) next = 0;
      if (!list[next].disabled && !list[next].separator) return next;
      next += direction;
    }
    return current;
  }

  function handleItemClick(item: ContextMenuItem, index: number) {
    if (item.disabled) return;
    if (item.children?.length) {
      openSubmenuIndex = index;
      submenuSelectedIndex = -1;
      return;
    }
    item.action();
    onclose();
  }

  function handleSubmenuClick(item: ContextMenuItem) {
    if (item.disabled) return;
    item.action();
    onclose();
  }
</script>

{#if visible}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    bind:this={backdropEl}
    class="fixed inset-0 z-50"
    onclick={onBackdropClick}
    onkeydown={onKeydown}
    tabindex="-1"
    role="presentation"
  >
    <div
      bind:this={menuEl}
      class="fixed z-50 min-w-40 max-w-56 overflow-hidden rounded border border-border bg-bg-secondary py-1 shadow-lg"
      style="left: {adjustedX}px; top: {adjustedY}px;"
      role="menu"
    >
      {#each items as item, i}
        {#if item.separator}
          <div class="mx-2 my-1 border-t border-border" role="separator"></div>
        {:else}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div
          class="relative flex cursor-default items-center gap-2 px-3 py-1.5 text-xs
            {item.disabled ? 'text-text-muted opacity-50' : 'text-text'}
            {!item.disabled && (selectedIndex === i || openSubmenuIndex === i) ? 'bg-bg-tertiary' : ''}
            {!item.disabled ? 'hover:bg-bg-tertiary' : ''}"
          role="menuitem"
          tabindex="-1"
          aria-disabled={item.disabled}
          data-index={i}
          onclick={() => handleItemClick(item, i)}
          onmouseenter={() => {
            if (!item.disabled) {
              selectedIndex = i;
              if (item.children?.length) {
                openSubmenuIndex = i;
                submenuSelectedIndex = -1;
              } else {
                openSubmenuIndex = -1;
                submenuSelectedIndex = -1;
              }
            }
          }}
        >
          {#if item.icon}
            <span class="w-4 shrink-0 text-center text-xs">{item.icon}</span>
          {/if}
          <span class="flex-1 truncate">{item.label}</span>
          {#if item.children?.length}
            <span class="shrink-0 text-text-muted">{@html '&#9656;'}</span>
          {/if}
        </div>

        <!-- Submenu -->
        {#if item.children?.length && openSubmenuIndex === i}
          {@const itemEl = menuEl?.querySelector(`[data-index="${i}"]`) as HTMLElement | null}
          <div
            class="fixed min-w-40 max-w-56 overflow-hidden rounded border border-border bg-bg-secondary py-1 shadow-lg"
            style="left: {adjustedX + (menuEl?.offsetWidth ?? 160)}px; top: {itemEl ? itemEl.getBoundingClientRect().top : adjustedY}px;"
          >
            {#each item.children as child, ci}
              {#if child.separator}
                <div class="mx-2 my-1 border-t border-border"></div>
              {/if}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <div
                class="flex cursor-default items-center gap-2 px-3 py-1.5 text-xs
                  {child.disabled ? 'text-text-muted opacity-50' : 'text-text'}
                  {!child.disabled && submenuSelectedIndex === ci ? 'bg-bg-tertiary' : ''}
                  {!child.disabled ? 'hover:bg-bg-tertiary' : ''}"
                role="menuitem"
                tabindex="-1"
                aria-disabled={child.disabled}
                onclick={() => handleSubmenuClick(child)}
                onmouseenter={() => {
                  if (!child.disabled) submenuSelectedIndex = ci;
                }}
              >
                {#if child.icon}
                  <span class="w-4 shrink-0 text-center text-xs">{child.icon}</span>
                {/if}
                <span class="flex-1 truncate">{child.label}</span>
              </div>
            {/each}
          </div>
        {/if}
        {/if}
      {/each}
    </div>
  </div>
{/if}
