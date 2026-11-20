<script>
  import { Plus, Download } from 'lucide-svelte';

  let {
    title,
    subtitle,
    oncreate = null,
    canCreate = false,
    showExport = false,
    onexport = () => {},
  } = $props();
</script>

<header class="page-header">
  {#key title}
    <div class="page-heading">
      <div class="breadcrumbs">PANEL <span>/</span> GESTIÓN</div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  {/key}
  <div class="header-actions">
    {#if showExport}
      <button type="button" class="button secondary" onclick={onexport}>
        <Download size={16} aria-hidden="true" />
        Exportar CSV
      </button>
    {/if}
    {#if canCreate}
      <button type="button" class="button primary" onclick={oncreate}>
        <Plus size={17} aria-hidden="true" />
        Nuevo registro
      </button>
    {/if}
  </div>
</header>
