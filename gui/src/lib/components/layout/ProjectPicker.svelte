<script lang="ts">
  import {
    projectDir,
    paperConfig,
    sources,
    claims,
    paperState,
  } from "$lib/stores/project";
  import {
    validatePaperProject,
    addRecentProject,
    getRecentProjects,
    listSources,
    listClaims,
    readPaperState,
    startWatching,
  } from "$lib/utils/ipc";
  import type { ProjectInfo } from "$lib/utils/ipc";

  const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

  let recentPaths = $state<string[]>([]);
  let recentProjects = $state<(ProjectInfo & { name: string })[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(false);
  let loadingPath = $state<string | null>(null);

  $effect(() => {
    loadRecents();

    // Auto-open project from URL ?project=/path/to/paper
    const params = new URLSearchParams(window.location.search);
    const projectPath = params.get("project");
    if (projectPath) {
      openProject(projectPath);
    }
  });

  async function loadRecents() {
    try {
      recentPaths = await getRecentProjects();
      const resolved: (ProjectInfo & { name: string })[] = [];
      for (const p of recentPaths) {
        try {
          const info = await validatePaperProject(p);
          resolved.push({
            ...info,
            name: p.split("/").filter(Boolean).pop() || p,
          });
        } catch {
          // Skip invalid/removed projects
        }
      }
      recentProjects = resolved;
    } catch {
      recentProjects = [];
    }
  }

  async function openProject(path: string) {
    error = null;
    loading = true;
    loadingPath = path;
    try {
      const info = await validatePaperProject(path);
      await addRecentProject(path);

      projectDir.set(path);
      paperConfig.set({
        topic: info.config.topic ?? "",
        venue: info.config.venue ?? "",
        depth: info.config.depth ?? "standard",
      });

      const [srcList, claimList, state] = await Promise.all([
        listSources(path),
        listClaims(path),
        readPaperState(path),
      ]);

      sources.set(srcList);
      claims.set(claimList as any);
      paperState.set(state);

      await startWatching(path);
    } catch (e: any) {
      error = e?.message || e?.toString() || "Not a valid paper project";
    } finally {
      loading = false;
      loadingPath = null;
    }
  }

  async function pickFolder() {
    error = null;
    try {
      if (isTauri) {
        const { open } = await import("@tauri-apps/plugin-dialog");
        const selected = await open({
          directory: true,
          multiple: false,
          title: "Open Paper Project",
        });
        if (selected) {
          await openProject(selected as string);
        }
      } else {
        // Browser dev mode: prompt for path
        const path = window.prompt("Enter paper project path:");
        if (path) {
          await openProject(path);
        }
      }
    } catch (e: any) {
      error = e?.message || e?.toString() || "Failed to open folder";
    }
  }
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-bg">
  <div class="flex w-full max-w-xl flex-col gap-8 px-6">
    <!-- Header -->
    <div class="flex flex-col items-center gap-3">
      <div
        class="flex h-14 w-14 items-center justify-center rounded-2xl bg-bg-secondary ring-1 ring-border"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="h-7 w-7 text-accent"
        >
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      </div>
      <h1 class="text-2xl font-semibold text-text-bright">Research Agent</h1>
      <p class="text-sm text-text-muted">Open a paper project to get started</p>
    </div>

    <!-- Error -->
    {#if error}
      <div
        class="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400"
      >
        {error}
      </div>
    {/if}

    <!-- Recent Projects -->
    {#if recentProjects.length > 0}
      <div class="flex flex-col gap-2">
        <h2 class="px-1 text-xs font-medium uppercase tracking-wider text-text-muted">
          Recent Projects
        </h2>
        <div class="flex flex-col gap-1">
          {#each recentProjects as project (project.path)}
            <button
              class="group flex w-full items-start gap-3 rounded-lg border border-transparent px-3 py-3 text-left transition-colors hover:border-border hover:bg-bg-secondary disabled:opacity-50"
              onclick={() => openProject(project.path)}
              disabled={loading}
            >
              <div
                class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-bg-tertiary text-xs text-accent"
              >
                {project.name.charAt(0).toUpperCase()}
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="truncate text-sm font-medium text-text-bright">
                    {project.name}
                  </span>
                  {#if loadingPath === project.path}
                    <span class="text-xs text-text-muted">Loading...</span>
                  {/if}
                </div>
                {#if project.config.topic}
                  <div class="mt-0.5 truncate text-xs text-text-muted">
                    {project.config.topic}
                  </div>
                {/if}
                <div class="mt-1 flex items-center gap-3 text-xs text-text-muted">
                  {#if project.config.venue}
                    <span
                      class="rounded bg-bg-tertiary px-1.5 py-0.5 text-text-muted"
                    >
                      {project.config.venue}
                    </span>
                  {/if}
                  <span>{project.source_count} sources</span>
                  {#if project.has_tex}
                    <span class="text-green-400">TeX</span>
                  {/if}
                </div>
              </div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                class="mt-1 h-4 w-4 shrink-0 text-text-muted opacity-0 transition-opacity group-hover:opacity-100"
              >
                <path
                  fill-rule="evenodd"
                  d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Open Folder -->
    <div class="flex flex-col gap-2">
      {#if recentProjects.length > 0}
        <div class="flex items-center gap-3">
          <div class="h-px flex-1 bg-border"></div>
          <span class="text-xs text-text-muted">or</span>
          <div class="h-px flex-1 bg-border"></div>
        </div>
      {/if}
      <button
        class="flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-bg-secondary px-4 py-3 text-sm font-medium text-text transition-colors hover:border-accent hover:bg-bg-tertiary hover:text-text-bright disabled:opacity-50"
        onclick={pickFolder}
        disabled={loading}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="h-4 w-4"
        >
          <path
            d="M3.75 3A1.75 1.75 0 002 4.75v3.26a3.235 3.235 0 011.75-.51h12.5c.644 0 1.245.188 1.75.51V6.75A1.75 1.75 0 0016.25 5h-4.836a.25.25 0 01-.177-.073L9.823 3.513A1.75 1.75 0 008.586 3H3.75z"
          />
          <path
            d="M3.75 9A1.75 1.75 0 002 10.75v4.5c0 .966.784 1.75 1.75 1.75h12.5A1.75 1.75 0 0018 15.25v-4.5A1.75 1.75 0 0016.25 9H3.75z"
          />
        </svg>
        Open Folder
      </button>
    </div>

    <!-- Hint -->
    <p class="text-center text-xs text-text-muted">
      Select a paper project directory created with <code
        class="rounded bg-bg-tertiary px-1 py-0.5 text-text-muted">create-paper</code
      >
    </p>
  </div>
</div>
