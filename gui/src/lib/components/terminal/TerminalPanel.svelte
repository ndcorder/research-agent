<script lang="ts">
  import { get } from "svelte/store";
  import { projectDir } from "$lib/stores/project";
  import {
    spawnTerminal,
    writeTerminal,
    resizeTerminal,
    killTerminal,
  } from "$lib/utils/ipc";

  type Terminal = import("@xterm/xterm").Terminal;
  type FitAddon = import("@xterm/addon-fit").FitAddon;

  let { fullscreen = false }: { fullscreen?: boolean } = $props();

  let containerEl: HTMLDivElement | undefined = $state();
  let terminal: Terminal | undefined = $state();
  let fitAddon: FitAddon | undefined = $state();
  let terminalId: number | undefined = $state();
  let unlisten: (() => void) | undefined;

  const theme = {
    background: "#1a1b26",
    foreground: "#c0caf5",
    cursor: "#7aa2f7",
    cursorAccent: "#1a1b26",
    selectionBackground: "#33467c",
    selectionForeground: "#c0caf5",
    black: "#15161e",
    red: "#f7768e",
    green: "#9ece6a",
    yellow: "#e0af68",
    blue: "#7aa2f7",
    magenta: "#bb9af7",
    cyan: "#7dcfff",
    white: "#a9b1d6",
    brightBlack: "#414868",
    brightRed: "#f7768e",
    brightGreen: "#9ece6a",
    brightYellow: "#e0af68",
    brightBlue: "#7aa2f7",
    brightMagenta: "#bb9af7",
    brightCyan: "#7dcfff",
    brightWhite: "#c0caf5",
  };

  async function init() {
    if (!containerEl) return;

    const [{ Terminal }, { FitAddon: FitAddonCtor }, { listen }] =
      await Promise.all([
        import("@xterm/xterm"),
        import("@xterm/addon-fit"),
        import("@tauri-apps/api/event"),
      ]);

    // CSS import for side effects
    await import("@xterm/xterm/css/xterm.css");

    const term = new Terminal({
      theme,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      fontSize: 14,
      lineHeight: 1.2,
      cursorBlink: true,
      cursorStyle: "bar",
      allowProposedApi: true,
    });

    const fit = new FitAddonCtor();
    term.loadAddon(fit);
    term.open(containerEl);
    fit.fit();

    terminal = term;
    fitAddon = fit;

    // Spawn PTY
    const cwd = get(projectDir) ?? (globalThis as any).__TAURI__?.env?.HOME ?? "/";
    const id = await spawnTerminal(cwd);
    terminalId = id;

    // Listen for PTY output
    unlisten = await listen<{ id: number; data: string }>(
      "terminal-data",
      (event) => {
        if (event.payload.id === id) {
          term.write(event.payload.data);
        }
      }
    );

    // Forward user input to PTY
    term.onData((data) => {
      writeTerminal(id, data);
    });

    // Sync initial size
    const dims = fit.proposeDimensions();
    if (dims) {
      resizeTerminal(id, dims.rows, dims.cols);
    }

    // Re-fit on resize
    term.onResize(({ rows, cols }) => {
      resizeTerminal(id, rows, cols);
    });
  }

  function handleResize() {
    if (fitAddon && terminal) {
      fitAddon.fit();
    }
  }

  async function cleanup() {
    unlisten?.();
    if (terminalId !== undefined) {
      await killTerminal(terminalId).catch(() => {});
    }
    terminal?.dispose();
    terminal = undefined;
    fitAddon = undefined;
    terminalId = undefined;
    unlisten = undefined;
  }

  // Mount/unmount lifecycle
  $effect(() => {
    if (containerEl) {
      init();
      return () => {
        cleanup();
      };
    }
  });
</script>

<svelte:window onresize={handleResize} />

<div
  class="h-full w-full overflow-hidden {fullscreen
    ? 'p-0'
    : 'rounded-md border border-border'}"
  style="background-color: #1a1b26;"
>
  <div class="h-full w-full" bind:this={containerEl}></div>
</div>
