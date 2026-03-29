<script lang="ts">
  import { activePage, isProjectLoaded } from "$lib/stores/project";
  import ProjectPicker from "$lib/components/layout/ProjectPicker.svelte";
  import WorkspacePage from "$lib/components/layout/WorkspacePage.svelte";
  import TerminalPage from "$lib/components/layout/TerminalPage.svelte";
</script>

{#if !$isProjectLoaded}
  <ProjectPicker />
{:else if $activePage === "workspace"}
  <WorkspacePage />
{:else}
  <TerminalPage />
{/if}
