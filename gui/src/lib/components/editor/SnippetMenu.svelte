<script lang="ts">
  import { showSnippetMenu } from "$lib/stores/project";

  interface Snippet {
    name: string;
    description: string;
    preview: string;
    body: string;
  }

  const snippets: Snippet[] = [
    {
      name: "Figure",
      description: "Floating figure with image",
      preview: "\\begin{figure}...\\end{figure}",
      body: "\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{${1:filename}}\n\\caption{${2:Caption text}}\n\\label{fig:${3:label}}\n\\end{figure}",
    },
    {
      name: "Table",
      description: "Basic table environment",
      preview: "\\begin{table}...\\end{table}",
      body: "\\begin{table}[htbp]\n\\centering\n\\caption{${1:Caption text}}\n\\label{tab:${2:label}}\n\\begin{tabular}{${3:lcc}}\n\\hline\n${4:Header 1} & ${5:Header 2} & ${6:Header 3} \\\\\\\\\n\\hline\n${7:data} & ${8:data} & ${9:data} \\\\\\\\\n\\hline\n\\end{tabular}\n\\end{table}",
    },
    {
      name: "Equation",
      description: "Numbered equation",
      preview: "\\begin{equation}...\\end{equation}",
      body: "\\begin{equation}\n${1:expression}\n\\label{eq:${2:label}}\n\\end{equation}",
    },
    {
      name: "Itemize",
      description: "Bulleted list",
      preview: "\\begin{itemize}...\\end{itemize}",
      body: "\\begin{itemize}\n\\item ${1:First item}\n\\item ${2:Second item}\n\\end{itemize}",
    },
    {
      name: "Enumerate",
      description: "Numbered list",
      preview: "\\begin{enumerate}...\\end{enumerate}",
      body: "\\begin{enumerate}\n\\item ${1:First item}\n\\item ${2:Second item}\n\\end{enumerate}",
    },
    {
      name: "Section",
      description: "New section heading",
      preview: "\\section{...}",
      body: "\\section{${1:Section Title}}\n\\label{sec:${2:label}}\n",
    },
    {
      name: "Subsection",
      description: "New subsection heading",
      preview: "\\subsection{...}",
      body: "\\subsection{${1:Subsection Title}}\n\\label{sec:${2:label}}\n",
    },
    {
      name: "Citation Block",
      description: "Block quote with citation",
      preview: "\\begin{quote}...\\end{quote}",
      body: "\\begin{quote}\n``${1:quoted text}'' \\\\citep{${2:key}}\n\\end{quote}",
    },
  ];

  let { editor = null, monaco = null }: { editor: any; monaco: any } = $props();
  let menuRef: HTMLDivElement | undefined = $state();

  function insertSnippet(snippet: Snippet) {
    if (!editor) return;
    editor.focus();
    // Use Monaco's built-in snippet insertion with tab stops
    const contribution = editor.getContribution("snippetController2");
    if (contribution) {
      contribution.insert(snippet.body);
    } else {
      // Fallback: use the snippet command
      editor.trigger("snippetMenu", "editor.action.insertSnippet", {
        snippet: snippet.body,
      });
    }
    showSnippetMenu.set(false);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      showSnippetMenu.set(false);
    }
  }

  function handleBackdropClick(e: MouseEvent) {
    if (menuRef && !menuRef.contains(e.target as Node)) {
      showSnippetMenu.set(false);
    }
  }
</script>

{#if $showSnippetMenu}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 z-50"
    onmousedown={handleBackdropClick}
    onkeydown={handleKeydown}
  >
    <div
      bind:this={menuRef}
      class="absolute right-4 top-12 w-80 max-h-96 overflow-y-auto rounded-lg border border-border bg-bg-secondary shadow-xl"
    >
      <div class="flex items-center justify-between border-b border-border px-3 py-2">
        <span class="text-xs font-medium text-text-bright">Insert Snippet</span>
        <kbd class="rounded bg-bg-tertiary px-1.5 py-0.5 text-xs text-text-muted">
          {navigator?.platform?.includes("Mac") ? "\u2318" : "Ctrl"}+J
        </kbd>
      </div>
      <div class="py-1">
        {#each snippets as snippet}
          <button
            class="group flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-bg-tertiary"
            onclick={() => insertSnippet(snippet)}
          >
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-text-bright group-hover:text-accent">
                {snippet.name}
              </span>
              <span class="text-xs text-text-muted">{snippet.description}</span>
            </div>
            <code class="text-xs text-text-muted/60 font-mono truncate block max-w-full">
              {snippet.preview}
            </code>
          </button>
        {/each}
      </div>
    </div>
  </div>
{/if}
