<script lang="ts">
  import { projectDir, openFileRequest, selectedSource } from "$lib/stores/project";
  import { listDirectory } from "$lib/utils/ipc";
  import type { FileEntry } from "$lib/types";

  const EXCLUDED = new Set([".git", "node_modules", ".claude", ".svelte-kit", "target", "__pycache__"]);

  interface TreeNode {
    entry: FileEntry;
    children: TreeNode[];
    loaded: boolean;
    loading: boolean;
  }

  let roots = $state<TreeNode[]>([]);
  let expanded = $state(new Set<string>());
  let selectedPath = $state<string | null>(null);

  async function loadChildren(path: string): Promise<TreeNode[]> {
    try {
      const entries = await listDirectory(path);
      return entries
        .filter((e) => !EXCLUDED.has(e.name))
        .sort((a, b) => {
          if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
          return a.name.localeCompare(b.name);
        })
        .map((e) => ({ entry: e, children: [], loaded: false, loading: false }));
    } catch {
      return [];
    }
  }

  $effect(() => {
    const dir = $projectDir;
    if (dir) {
      loadChildren(dir).then((nodes) => {
        roots = nodes;
      });
    } else {
      roots = [];
    }
  });

  async function toggleFolder(node: TreeNode) {
    const path = node.entry.path;
    if (expanded.has(path)) {
      expanded.delete(path);
      expanded = new Set(expanded);
    } else {
      if (!node.loaded) {
        node.loading = true;
        node.children = await loadChildren(path);
        node.loaded = true;
        node.loading = false;
      }
      expanded.add(path);
      expanded = new Set(expanded);
    }
  }

  function fileIcon(name: string): { label: string; color: string } {
    const ext = name.includes(".") ? name.slice(name.lastIndexOf(".")) : "";
    switch (ext) {
      case ".tex":
        return { label: "T", color: "text-accent" };
      case ".md":
        return { label: "M", color: "text-info" };
      case ".json":
        return { label: "{}", color: "text-warning" };
      case ".bib":
        return { label: "B", color: "text-success" };
      case ".py":
        return { label: "Py", color: "text-text" };
      case ".pdf":
        return { label: "P", color: "text-danger" };
      default:
        return { label: "~", color: "text-text-muted" };
    }
  }

  function formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function handleFileClick(entry: FileEntry) {
    selectedPath = entry.path;
    if (entry.name.endsWith(".md") && entry.path.includes("research/sources/")) {
      const key = entry.name.replace(/\.md$/, "");
      selectedSource.set(key);
    }
  }

  function handleFileDblClick(entry: FileEntry) {
    openFileRequest.set({ name: entry.name, path: entry.path });
  }
</script>

{#snippet renderNode(node: TreeNode, depth: number)}
  {#if node.entry.is_dir}
    <button
      class="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-xs transition-colors hover:bg-bg-tertiary"
      style="padding-left: {4 + depth * 12}px"
      onclick={() => toggleFolder(node)}
      title={node.entry.path}
    >
      <span class="w-3 text-center text-text-muted">{expanded.has(node.entry.path) ? "\u25BE" : "\u25B8"}</span>
      <span class="truncate text-text-bright">{node.entry.name}</span>
      {#if node.loading}
        <span class="ml-auto text-[10px] text-text-muted">...</span>
      {/if}
    </button>
    {#if expanded.has(node.entry.path)}
      {#each node.children as child (child.entry.path)}
        {@render renderNode(child, depth + 1)}
      {/each}
    {/if}
  {:else}
    {@const icon = fileIcon(node.entry.name)}
    <button
      class="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-xs transition-colors hover:bg-bg-tertiary {selectedPath === node.entry.path ? 'bg-bg-tertiary' : ''}"
      style="padding-left: {4 + depth * 12}px"
      title="{node.entry.path} ({formatSize(node.entry.size)})"
      onclick={() => handleFileClick(node.entry)}
      ondblclick={() => handleFileDblClick(node.entry)}
    >
      <span class="w-3 text-center text-[10px] font-bold {icon.color}">{icon.label}</span>
      <span class="truncate text-text">{node.entry.name}</span>
    </button>
  {/if}
{/snippet}

<div class="flex flex-col gap-0.5 py-1">
  {#each roots as node (node.entry.path)}
    {@render renderNode(node, 0)}
  {:else}
    <div class="px-2 py-4 text-center text-xs text-text-muted">No project open</div>
  {/each}
</div>
