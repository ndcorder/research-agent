<script lang="ts">
  import { showSettings } from "$lib/stores/project";
  import {
    settings,
    DEFAULTS,
    ACCENT_COLORS,
    type FontFamily,
    type AccentColor,
    type CursorStyle,
    type LineHighlight,
  } from "$lib/stores/settings";

  const fontOptions: { value: FontFamily; label: string; sample: string }[] = [
    { value: "mono", label: "SF Mono", sample: "font-mono" },
    { value: "sans", label: "SF Pro", sample: "font-sans" },
    { value: "serif", label: "New York", sample: "font-serif" },
  ];

  const accentOptions: { value: AccentColor; label: string }[] = [
    { value: "blue", label: "Blue" },
    { value: "purple", label: "Purple" },
    { value: "green", label: "Green" },
    { value: "orange", label: "Orange" },
    { value: "pink", label: "Pink" },
    { value: "teal", label: "Teal" },
  ];

  const cursorOptions: { value: CursorStyle; label: string }[] = [
    { value: "line", label: "Line" },
    { value: "line-thin", label: "Thin line" },
    { value: "block", label: "Block" },
    { value: "block-outline", label: "Block outline" },
    { value: "underline", label: "Underline" },
  ];

  const lineHighlightOptions: { value: LineHighlight; label: string }[] = [
    { value: "none", label: "None" },
    { value: "gutter", label: "Gutter" },
    { value: "line", label: "Line" },
    { value: "all", label: "All" },
  ];

  const autoSaveOptions: { value: number; label: string }[] = [
    { value: 0, label: "Off" },
    { value: 500, label: "0.5s" },
    { value: 1000, label: "1s" },
    { value: 2000, label: "2s" },
    { value: 5000, label: "5s" },
  ];

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

  function resetAll() {
    settings.set({ ...DEFAULTS });
    localStorage.removeItem("panel-sidebar");
    localStorage.removeItem("panel-right");
  }

  const shortcuts: [string, string][] = [
    ["Cmd+`", "Toggle terminal"],
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

        <!-- ── Appearance ── -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Appearance
          </h3>
          <div class="space-y-4">
            <!-- Font family -->
            <div>
              <span class="mb-2 block text-xs text-text">Font family</span>
              <div class="grid grid-cols-3 gap-2">
                {#each fontOptions as opt}
                  <button
                    onclick={() => updateSetting("fontFamily", opt.value)}
                    class="flex flex-col items-center gap-1.5 rounded-lg border px-3 py-2.5 text-center transition-colors {$settings.fontFamily === opt.value
                      ? 'border-accent bg-accent/10 text-text-bright'
                      : 'border-border bg-bg text-text-muted hover:border-text-muted hover:text-text'}"
                  >
                    <span class="{opt.sample} text-lg leading-tight">Aa</span>
                    <span class="text-[10px]">{opt.label}</span>
                  </button>
                {/each}
              </div>
            </div>

            <!-- UI font size -->
            <div class="flex items-center justify-between gap-4">
              <label class="text-xs text-text" for="ui-font-size">Interface size</label>
              <div class="flex items-center gap-2">
                <input
                  id="ui-font-size"
                  type="range"
                  min="12"
                  max="20"
                  value={$settings.uiFontSize}
                  oninput={(e) =>
                    updateSetting("uiFontSize", Number((e.target as HTMLInputElement).value))}
                  class="h-1 w-24 cursor-pointer appearance-none rounded-full bg-border accent-accent"
                />
                <span class="w-8 text-center text-xs text-text-muted">{$settings.uiFontSize}px</span>
              </div>
            </div>

            <!-- Accent color -->
            <div>
              <span class="mb-2 block text-xs text-text">Accent color</span>
              <div class="flex gap-2">
                {#each accentOptions as opt}
                  <button
                    onclick={() => updateSetting("accentColor", opt.value)}
                    title={opt.label}
                    aria-label="Accent color {opt.label}"
                    class="h-6 w-6 rounded-full border-2 transition-transform hover:scale-110 {$settings.accentColor === opt.value
                      ? 'border-text-bright scale-110'
                      : 'border-transparent'}"
                    style="background-color: {ACCENT_COLORS[opt.value].accent}"
                  ></button>
                {/each}
              </div>
            </div>
          </div>
        </section>

        <!-- ── Editor ── -->
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
                    updateSetting("editorFontSize", Number((e.target as HTMLInputElement).value))}
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

            <!-- Tab size -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="tab-size">Tab size</label>
              <div class="flex gap-1">
                {#each [2, 4] as size}
                  <button
                    onclick={() => updateSetting("editorTabSize", size)}
                    class="rounded px-2.5 py-0.5 text-xs transition-colors {$settings.editorTabSize === size
                      ? 'bg-accent text-bg'
                      : 'bg-bg text-text-muted hover:text-text'}"
                  >{size}</button>
                {/each}
              </div>
            </div>

            <!-- Cursor style -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="cursor-style">Cursor style</label>
              <select
                id="cursor-style"
                value={$settings.cursorStyle}
                onchange={(e) =>
                  updateSetting("cursorStyle", (e.target as HTMLSelectElement).value as CursorStyle)}
                class="rounded border border-border bg-bg px-2 py-0.5 text-xs text-text outline-none focus:border-accent"
              >
                {#each cursorOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>

            <!-- Line highlight -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="line-highlight">Line highlight</label>
              <select
                id="line-highlight"
                value={$settings.lineHighlight}
                onchange={(e) =>
                  updateSetting("lineHighlight", (e.target as HTMLSelectElement).value as LineHighlight)}
                class="rounded border border-border bg-bg px-2 py-0.5 text-xs text-text outline-none focus:border-accent"
              >
                {#each lineHighlightOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>

            <!-- Minimap -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="minimap">Minimap</label>
              <button
                id="minimap"
                role="switch"
                aria-checked={$settings.editorMinimap}
                aria-label="Toggle minimap"
                onclick={() => updateSetting("editorMinimap", !$settings.editorMinimap)}
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
              <label class="text-xs text-text" for="line-numbers">Line numbers</label>
              <button
                id="line-numbers"
                role="switch"
                aria-checked={$settings.showLineNumbers}
                aria-label="Toggle line numbers"
                onclick={() => updateSetting("showLineNumbers", !$settings.showLineNumbers)}
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
                onclick={() => updateSetting("wordWrap", !$settings.wordWrap)}
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

            <!-- Bracket pair colorization -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="bracket-color">Bracket colorization</label>
              <button
                id="bracket-color"
                role="switch"
                aria-checked={$settings.bracketPairColorization}
                aria-label="Toggle bracket pair colorization"
                onclick={() => updateSetting("bracketPairColorization", !$settings.bracketPairColorization)}
                class="relative h-5 w-9 rounded-full transition-colors {$settings.bracketPairColorization
                  ? 'bg-accent'
                  : 'bg-border'}"
              >
                <span
                  class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.bracketPairColorization
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></span>
              </button>
            </div>

            <!-- Smooth scrolling -->
            <div class="flex items-center justify-between">
              <label class="text-xs text-text" for="smooth-scroll">Smooth scrolling</label>
              <button
                id="smooth-scroll"
                role="switch"
                aria-checked={$settings.smoothScrolling}
                aria-label="Toggle smooth scrolling"
                onclick={() => updateSetting("smoothScrolling", !$settings.smoothScrolling)}
                class="relative h-5 w-9 rounded-full transition-colors {$settings.smoothScrolling
                  ? 'bg-accent'
                  : 'bg-border'}"
              >
                <span
                  class="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform {$settings.smoothScrolling
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></span>
              </button>
            </div>
          </div>
        </section>

        <!-- ── Pipeline ── -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Pipeline
          </h3>
          <div class="space-y-3">
            <!-- Auto-compile on save -->
            <div class="flex items-center justify-between">
              <div>
                <label class="text-xs text-text" for="auto-compile">Auto-compile on save</label>
                <p class="mt-0.5 text-xs leading-tight text-text-muted">
                  Run latexmk after saving .tex files
                </p>
              </div>
              <button
                id="auto-compile"
                role="switch"
                aria-checked={$settings.autoCompileOnSave}
                aria-label="Toggle auto-compile on save"
                onclick={() => updateSetting("autoCompileOnSave", !$settings.autoCompileOnSave)}
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

            <!-- Auto-save delay -->
            <div class="flex items-center justify-between">
              <div>
                <label class="text-xs text-text" for="auto-save-delay">Auto-save delay</label>
                <p class="mt-0.5 text-xs leading-tight text-text-muted">
                  Delay after typing before saving
                </p>
              </div>
              <div class="flex gap-1">
                {#each autoSaveOptions as opt}
                  <button
                    onclick={() => updateSetting("autoSaveDelay", opt.value)}
                    class="rounded px-2 py-0.5 text-xs transition-colors {$settings.autoSaveDelay === opt.value
                      ? 'bg-accent text-bg'
                      : 'bg-bg text-text-muted hover:text-text'}"
                  >{opt.label}</button>
                {/each}
              </div>
            </div>
          </div>
        </section>

        <!-- ── Keyboard Shortcuts ── -->
        <section>
          <h3 class="mb-3 text-xs font-semibold tracking-wide text-text-muted uppercase">
            Keyboard Shortcuts
          </h3>
          <div class="rounded border border-border bg-bg text-xs">
            {#each shortcuts as [key, desc], i}
              <div
                class="flex items-center justify-between px-3 py-1.5 {i !== shortcuts.length - 1
                  ? 'border-b border-border'
                  : ''}"
              >
                <span class="text-text-muted">{desc}</span>
                <kbd class="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-xs text-text-bright">{key}</kbd>
              </div>
            {/each}
          </div>
        </section>

        <!-- ── About ── -->
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

          <button
            onclick={resetAll}
            class="mt-4 w-full rounded border border-border bg-bg px-3 py-1.5 text-xs text-text-muted transition-colors hover:border-danger hover:text-danger"
          >
            Reset all settings to defaults
          </button>
        </section>
      </div>
    </div>
  </div>
{/if}
