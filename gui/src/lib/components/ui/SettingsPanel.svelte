<script lang="ts">
  import { showSettings } from "$lib/stores/project";
  import { settings } from "$lib/stores/settings";

  let panel: HTMLDivElement | undefined = $state();

  function close() {
    showSettings.set(false);
  }

  function onBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") close();
  }

  function updateSetting<K extends keyof typeof $settings>(
    key: K,
    value: (typeof $settings)[K],
  ) {
    settings.update((s) => ({ ...s, [key]: value }));
  }

  const shortcuts: [string, string][] = [
    ["Cmd+W", "Close tab"],
    ["Cmd+S", "Save"],
    ["Cmd+P", "Command palette"],
    ["Cmd+,", "Settings"],
    ["Cmd+Shift+B", "Compile"],
    ["Cmd+1 / 2", "Switch page"],
    ["Cmd+Shift+G", "Toggle graph"],
    ["Cmd+Shift+P", "Toggle PDF"],
    ["Cmd+Shift+T", "Toggle timeline"],
    ["Cmd+= / \u2212 / 0", "Zoom in / out / reset"],
    ["Cmd+[ / ]", "Cycle panels"],
    ["Ctrl+Tab", "Cycle tabs"],
    ["Cmd+Shift+F", "Search"],
  ];
</script>

{#if $showSettings}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
    onclick={onBackdropClick}
    onkeydown={onKeydown}
  >
    <div
      bind:this={panel}
      class="flex max-h-[80vh] w-full max-w-lg flex-col overflow-hidden rounded-lg border border-border bg-bg-secondary shadow-2xl"
    >
      <!-- Header -->
      <div
        class="flex items-center justify-between border-b border-border px-5 py-3"
      >
        <h2 class="text-sm font-semibold text-text-bright">Settings</h2>
        <button
          class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text"
          onclick={close}
          aria-label="Close settings"
        >
          <svg
            class="h-4 w-4"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>

      <!-- Scrollable body -->
      <div class="flex-1 space-y-5 overflow-y-auto px-5 py-4">
        <!-- Editor section -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Editor
          </h3>
          <div class="space-y-3">
            <!-- Font size -->
            <div class="flex items-center justify-between gap-4">
              <label class="text-xs text-text" for="font-size">Font size</label>
              <div class="flex items-center gap-2">
                <input
                  id="font-size"
                  type="range"
                  min="9"
                  max="24"
                  value={$settings.editorFontSize}
                  oninput={(e) =>
                    updateSetting(
                      "editorFontSize",
                      Number((e.target as HTMLInputElement).value),
                    )}
                  class="h-1 w-24 cursor-pointer appearance-none rounded-full bg-border accent-accent"
                />
                <input
                  type="number"
                  min="9"
                  max="24"
                  value={$settings.editorFontSize}
                  oninput={(e) => {
                    const v = Number((e.target as HTMLInputElement).value);
                    if (v >= 9 && v <= 24) updateSetting("editorFontSize", v);
                  }}
                  class="w-12 rounded border border-border bg-bg px-2 py-0.5 text-center text-xs text-text outline-none focus:border-accent"
                />
              </div>
            </div>

            <!-- Minimap -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="minimap">Minimap</label>
              <button
                id="minimap"
                role="switch"
                aria-checked={$settings.editorMinimap}
                aria-label="Toggle minimap"
                onclick={() =>
                  updateSetting("editorMinimap", !$settings.editorMinimap)}
                class="relative h-5 w-9 rounded-full transition-colors {$settings.editorMinimap
                  ? 'bg-accent'
                  : 'bg-border'}"
              >
                <span
                  class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.editorMinimap
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></span>
              </button>
            </div>

            <!-- Line numbers -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="line-numbers"
                >Line numbers</label
              >
              <button
                id="line-numbers"
                role="switch"
                aria-checked={$settings.showLineNumbers}
                aria-label="Toggle line numbers"
                onclick={() =>
                  updateSetting(
                    "showLineNumbers",
                    !$settings.showLineNumbers,
                  )}
                class="relative h-5 w-9 rounded-full transition-colors {$settings.showLineNumbers
                  ? 'bg-accent'
                  : 'bg-border'}"
              >
                <span
                  class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.showLineNumbers
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></span>
              </button>
            </div>

            <!-- Word wrap -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="word-wrap">Word wrap</label>
              <button
                id="word-wrap"
                role="switch"
                aria-checked={$settings.wordWrap}
                aria-label="Toggle word wrap"
                onclick={() =>
                  updateSetting("wordWrap", !$settings.wordWrap)}
                class="relative h-5 w-9 rounded-full transition-colors {$settings.wordWrap
                  ? 'bg-accent'
                  : 'bg-border'}"
              >
                <span
                  class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.wordWrap
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></span>
              </button>
            </div>
          </div>
        </section>

        <!-- Pipeline section -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Pipeline
          </h3>
          <div class="flex items-center justify-between">
            <div>
              <label class="text-xs text-text" for="auto-compile"
                >Auto-compile on save</label
              >
              <p class="mt-0.5 text-xs leading-tight text-text-muted">
                Automatically run latexmk after saving a .tex file
              </p>
            </div>
            <button
              id="auto-compile"
              role="switch"
              aria-checked={$settings.autoCompileOnSave}
              aria-label="Toggle auto-compile on save"
              onclick={() =>
                updateSetting(
                  "autoCompileOnSave",
                  !$settings.autoCompileOnSave,
                )}
              class="relative h-5 w-9 shrink-0 rounded-full transition-colors {$settings.autoCompileOnSave
                ? 'bg-accent'
                : 'bg-border'}"
            >
              <span
                class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.autoCompileOnSave
                  ? 'translate-x-4'
                  : 'translate-x-0'}"
              ></span>
            </button>
          </div>
        </section>

        <!-- Keyboard Shortcuts section -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Keyboard Shortcuts
          </h3>
          <div
            class="rounded border border-border bg-bg text-xs"
          >
            {#each shortcuts as [key, desc], i}
              <div
                class="flex items-center justify-between px-3 py-1.5 {i !== shortcuts.length - 1
                  ? 'border-b border-border'
                  : ''}"
              >
                <span class="text-text-muted">{desc}</span>
                <kbd
                  class="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-xs text-text-bright"
                  >{key}</kbd
                >
              </div>
            {/each}
          </div>
        </section>

        <!-- About section -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            About
          </h3>
          <div class="space-y-1 text-xs">
            <div class="flex justify-between">
              <span class="text-text-muted">Version</span>
              <span class="text-text">0.1.0</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-muted">Stack</span>
              <span class="text-text">Tauri v2 + SvelteKit</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
{/if}
