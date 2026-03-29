<script lang="ts">
  import { onMount } from "svelte";
  import { projectDir } from "$lib/stores/project";
  import { compileLatex } from "$lib/utils/ipc";

  type PDFDocumentProxy = {
    numPages: number;
    getPage(num: number): Promise<PDFPageProxy>;
    destroy(): void;
  };

  type PDFPageProxy = {
    getViewport(params: { scale: number }): { width: number; height: number };
    render(params: {
      canvasContext: CanvasRenderingContext2D;
      viewport: { width: number; height: number };
    }): { promise: Promise<void> };
  };

  let currentPage = $state(1);
  let totalPages = $state(0);
  let scale = $state(1.0);
  let fitWidth = $state(true);
  let status = $state<"loading" | "ready" | "no-pdf" | "error">("loading");
  let errorMsg = $state("");
  let compiling = $state(false);
  let canvasContainer: HTMLDivElement | undefined = $state();
  let scrollContainer: HTMLDivElement | undefined = $state();

  let pdfDoc: PDFDocumentProxy | null = null;
  let pdfjsLib: typeof import("pdfjs-dist") | null = null;
  let renderGeneration = 0;

  async function loadPdfjs() {
    const mod = await import("pdfjs-dist");
    mod.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url
    ).href;
    pdfjsLib = mod;
    return mod;
  }

  async function readPdfBinary(path: string): Promise<Uint8Array> {
    const { readFile } = await import("@tauri-apps/plugin-fs");
    return await readFile(path, { baseDir: undefined } as any);
  }

  async function loadPdf() {
    const dir = $projectDir;
    if (!dir) {
      status = "no-pdf";
      return;
    }

    const pdfPath = `${dir}/main.pdf`;

    // Check if file exists
    try {
      const { exists } = await import("@tauri-apps/plugin-fs");
      const fileExists = await exists(pdfPath, { baseDir: undefined } as any);
      if (!fileExists) {
        status = "no-pdf";
        return;
      }
    } catch {
      status = "no-pdf";
      return;
    }

    status = "loading";

    try {
      const lib = pdfjsLib ?? (await loadPdfjs());
      const data = await readPdfBinary(pdfPath);

      if (pdfDoc) {
        pdfDoc.destroy();
        pdfDoc = null;
      }

      const doc = await lib.getDocument({ data }).promise;
      pdfDoc = doc as unknown as PDFDocumentProxy;
      totalPages = doc.numPages;
      currentPage = Math.min(currentPage, totalPages);
      if (currentPage < 1) currentPage = 1;
      status = "ready";
      await renderAllPages();
    } catch (e: any) {
      status = "error";
      errorMsg = e?.message ?? "Failed to load PDF";
    }
  }

  async function renderAllPages() {
    if (!pdfDoc || !canvasContainer) return;

    const gen = ++renderGeneration;
    canvasContainer.innerHTML = "";

    for (let i = 1; i <= totalPages; i++) {
      if (gen !== renderGeneration) return;

      const page = await pdfDoc.getPage(i);
      const containerWidth = canvasContainer.clientWidth - 32;

      let displayScale = scale;
      if (fitWidth && containerWidth > 0) {
        const baseViewport = page.getViewport({ scale: 1.0 });
        displayScale = containerWidth / baseViewport.width;
      }

      const viewport = page.getViewport({ scale: displayScale });

      const wrapper = document.createElement("div");
      wrapper.className = "pdf-page-wrapper";
      wrapper.dataset.page = String(i);
      wrapper.style.marginBottom = "12px";
      wrapper.style.display = "flex";
      wrapper.style.justifyContent = "center";

      const canvas = document.createElement("canvas");
      canvas.width = viewport.width * window.devicePixelRatio;
      canvas.height = viewport.height * window.devicePixelRatio;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      canvas.style.borderRadius = "2px";
      canvas.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";

      const ctx = canvas.getContext("2d")!;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

      wrapper.appendChild(canvas);
      canvasContainer.appendChild(wrapper);

      await page.render({ canvasContext: ctx, viewport }).promise;
    }
  }

  function scrollToPage(page: number) {
    if (!canvasContainer) return;
    const wrapper = canvasContainer.querySelector(
      `[data-page="${page}"]`
    ) as HTMLElement | null;
    if (wrapper) {
      wrapper.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function handleScroll() {
    if (!canvasContainer || !scrollContainer) return;
    const scrollTop = scrollContainer.scrollTop;
    const wrappers = canvasContainer.querySelectorAll(".pdf-page-wrapper");
    let closestPage = 1;
    let closestDist = Infinity;

    for (const el of wrappers) {
      const htmlEl = el as HTMLElement;
      const dist = Math.abs(htmlEl.offsetTop - scrollTop);
      if (dist < closestDist) {
        closestDist = dist;
        closestPage = parseInt(htmlEl.dataset.page ?? "1");
      }
    }

    currentPage = closestPage;
  }

  function prevPage() {
    if (currentPage > 1) {
      currentPage--;
      scrollToPage(currentPage);
    }
  }

  function nextPage() {
    if (currentPage < totalPages) {
      currentPage++;
      scrollToPage(currentPage);
    }
  }

  function zoomIn() {
    fitWidth = false;
    scale = Math.min(scale + 0.25, 4.0);
    renderAllPages();
  }

  function zoomOut() {
    fitWidth = false;
    scale = Math.max(scale - 0.25, 0.25);
    renderAllPages();
  }

  function toggleFitWidth() {
    fitWidth = !fitWidth;
    if (fitWidth) {
      renderAllPages();
    }
  }

  async function handleCompile() {
    const dir = $projectDir;
    if (!dir || compiling) return;
    compiling = true;
    try {
      await compileLatex(dir);
      await loadPdf();
    } catch (e: any) {
      status = "error";
      errorMsg = e?.message ?? "Compilation failed";
    } finally {
      compiling = false;
    }
  }

  // Re-render on resize
  let resizeObserver: ResizeObserver | undefined;

  onMount(() => {
    loadPdf();

    // Watch for file changes via Tauri event
    let unlisten: (() => void) | undefined;
    import("@tauri-apps/api/event").then(({ listen }) => {
      listen<{ path: string; kind: string }>("file-change", (event) => {
        if (event.payload.path.endsWith("main.pdf")) {
          loadPdf();
        }
      }).then((u) => {
        unlisten = u;
      });
    });

    // Resize observer to re-render on panel resize
    if (canvasContainer) {
      resizeObserver = new ResizeObserver(() => {
        if (status === "ready" && fitWidth) {
          renderAllPages();
        }
      });
      resizeObserver.observe(canvasContainer);
    }

    // Re-check on window focus
    const onFocus = () => {
      if ($projectDir) loadPdf();
    };
    window.addEventListener("focus", onFocus);

    return () => {
      unlisten?.();
      resizeObserver?.disconnect();
      window.removeEventListener("focus", onFocus);
      if (pdfDoc) {
        pdfDoc.destroy();
        pdfDoc = null;
      }
    };
  });

  // React to projectDir changes
  $effect(() => {
    const _dir = $projectDir;
    if (_dir) {
      loadPdf();
    } else {
      status = "no-pdf";
    }
  });
</script>

<div class="flex h-full flex-col bg-bg">
  {#if status === "loading"}
    <div class="flex flex-1 items-center justify-center text-text-muted">
      <div class="flex flex-col items-center gap-2">
        <svg
          class="animate-spin"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
        <span class="text-xs">Loading PDF...</span>
      </div>
    </div>
  {:else if status === "no-pdf"}
    <div class="flex flex-1 flex-col items-center justify-center gap-3 text-text-muted">
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
      <span class="text-xs">No PDF found</span>
      <span class="text-xs text-text-muted/60">Compile to generate main.pdf</span>
      <button
        class="mt-2 rounded border border-border bg-bg-secondary px-3 py-1.5 text-xs text-text transition-colors hover:border-accent hover:text-text-bright disabled:opacity-50"
        onclick={handleCompile}
        disabled={compiling || !$projectDir}
      >
        {compiling ? "Compiling..." : "Compile LaTeX"}
      </button>
    </div>
  {:else if status === "error"}
    <div class="flex flex-1 flex-col items-center justify-center gap-2 text-danger">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="15" y1="9" x2="9" y2="15" />
        <line x1="9" y1="9" x2="15" y2="15" />
      </svg>
      <span class="text-xs">{errorMsg}</span>
      <button
        class="mt-1 text-xs text-accent hover:text-accent-hover"
        onclick={() => loadPdf()}
      >
        Retry
      </button>
    </div>
  {:else}
    <!-- Toolbar -->
    <div class="flex items-center justify-between border-b border-border bg-bg-secondary px-2 py-1">
      <div class="flex items-center gap-1">
        <button
          class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text disabled:opacity-30"
          onclick={prevPage}
          disabled={currentPage <= 1}
          title="Previous page"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <span class="min-w-[72px] text-center text-xs text-text-muted">
          {currentPage} / {totalPages}
        </span>
        <button
          class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text disabled:opacity-30"
          onclick={nextPage}
          disabled={currentPage >= totalPages}
          title="Next page"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      <div class="flex items-center gap-1">
        <button
          class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text"
          onclick={zoomOut}
          title="Zoom out"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
        <button
          class="rounded px-1.5 py-0.5 text-xs transition-colors {fitWidth
            ? 'bg-bg-tertiary text-accent'
            : 'text-text-muted hover:bg-bg-tertiary hover:text-text'}"
          onclick={toggleFitWidth}
          title="Fit to width"
        >
          W
        </button>
        <button
          class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text"
          onclick={zoomIn}
          title="Zoom in"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="11" y1="8" x2="11" y2="14" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
      </div>

      <button
        class="rounded p-1 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-text disabled:opacity-50"
        onclick={handleCompile}
        disabled={compiling}
        title="Recompile"
      >
        {#if compiling}
          <svg class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
        {:else}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
        {/if}
      </button>
    </div>

    <!-- PDF canvas area -->
    <div
      class="flex-1 overflow-auto bg-bg"
      bind:this={scrollContainer}
      onscroll={handleScroll}
    >
      <div class="p-4" bind:this={canvasContainer}></div>
    </div>
  {/if}
</div>
