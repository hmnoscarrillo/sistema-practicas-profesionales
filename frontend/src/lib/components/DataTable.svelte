<script module>
  let tableSeq = 0;
  const collator = new Intl.Collator('es-CO', { numeric: true, sensitivity: 'base' });
</script>

<script>
  import { fly } from 'svelte/transition';
  import { Search, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, Eye } from 'lucide-svelte';
  import { flyMotion } from '../motion.js';
  import StatusBadge from './StatusBadge.svelte';

  let {
    columns = [],
    data = [],
    lookups = {},
    caption = 'Registros del módulo',
    onedit = () => {},
    ondelete = () => {},
    canUpdate = false,
    canDelete = false,
  } = $props();

  const captionId = `table-caption-${++tableSeq}`;

  let query = $state('');
  let filterKey = $state('');
  let filterValue = $state('');
  let page = $state(1);
  let size = $state(8);
  let order = $state({ key: '', asc: true });
  let sortAnnouncement = $state('');

  let filterableColumns = $derived(
    columns.filter((col) => {
      const values = new Set(data.map((row) => String(row[col.key] ?? '')).filter(Boolean));
      return values.size > 1 && values.size <= 12;
    }),
  );

  let filterValues = $derived(
    filterKey
      ? [...new Set(data.map((row) => row[filterKey]).filter((value) => value != null && value !== ''))].sort((a, b) =>
          collator.compare(String(a), String(b)),
        )
      : [],
  );

  let filtered = $derived(
    data.filter((row) => {
      const term = query.trim().toLocaleLowerCase('es-CO');
      const textMatches =
        !term ||
        columns.some((col) =>
          String(display(row[col.key], col, lookups)).toLocaleLowerCase('es-CO').includes(term),
        );
      const valueMatches = !filterValue || String(row[filterKey] ?? '') === filterValue;
      return textMatches && valueMatches;
    }),
  );

  function compareRows(a, b, column) {
    const rawA = a?.[column.key];
    const rawB = b?.[column.key];
    if (rawA == null && rawB == null) return 0;
    if (rawA == null) return 1;
    if (rawB == null) return -1;

    if (column.type === 'rating' || (typeof rawA === 'number' && typeof rawB === 'number')) {
      return Number(rawA) - Number(rawB);
    }

    if (column.type === 'date') {
      const timeA = Date.parse(String(rawA));
      const timeB = Date.parse(String(rawB));
      if (!Number.isNaN(timeA) && !Number.isNaN(timeB)) {
        return timeA - timeB;
      }
    }

    return collator.compare(
      String(display(rawA, column, lookups)),
      String(display(rawB, column, lookups)),
    );
  }

  let sorted = $derived.by(() => {
    if (!order.key) return filtered;
    const column = columns.find((item) => item.key === order.key);
    if (!column) return filtered;
    const factor = order.asc ? 1 : -1;
    return [...filtered].sort((a, b) => compareRows(a, b, column) * factor);
  });

  let totalPages = $derived(Math.max(1, Math.ceil(filtered.length / size)));
  let visible = $derived(sorted.slice((page - 1) * size, page * size));

  function display(value, col, refs) {
    if (value == null || value === '') return '—';
    if (!col) return value;
    if (col.type === 'ref') {
      const found = refs[col.ref]?.find((item) => String(item._id) === String(value));
      return found ? labelFor(col.ref, found) : '—';
    }
    if (col.type === 'date') {
      const date = new Date(`${value}T12:00:00`);
      return Number.isNaN(date.getTime())
        ? value
        : date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
    }
    return value;
  }

  function labelFor(ref, row) {
    if (ref === 'empresas' || ref === 'programas') return row.nombre;
    if (ref === 'personas') return `${row.nombres} ${row.apellidos} · ${row.documento}`;
    if (ref === 'estudiantes' || ref === 'tutores_academicos' || ref === 'tutores_empresariales') {
      return `${row.nombres} ${row.apellidos}`;
    }
    if (ref === 'convenios') return row.codigo;
    if (ref === 'practicas') {
      const student = lookups.estudiantes?.find((item) => String(item._id) === String(row.estudiante_id));
      return student ? `${student.nombres} ${student.apellidos} · ${row.cargo}` : row.cargo;
    }
    return row.nombre_documento || row.nombre || 'Registro';
  }

  function sort(column) {
    const nextAsc = order.key === column.key ? !order.asc : true;
    order = { key: column.key, asc: nextAsc };
    page = 1;
    sortAnnouncement = `Ordenado por ${column.label}, ${nextAsc ? 'ascendente' : 'descendente'}, ${filtered.length} filas`;
  }

  function changeFilterColumn(event) {
    filterKey = event.currentTarget.value;
    filterValue = '';
    page = 1;
  }

  function clearFilters() {
    query = '';
    filterKey = '';
    filterValue = '';
    page = 1;
  }

  $effect(() => {
    query;
    data.length;
    page = 1;
  });

  $effect(() => {
    if (page > totalPages) page = totalPages;
  });
</script>

<div class="table-tools">
  <label class="search-field">
    <Search size={16} aria-hidden="true" />
    <input
      type="search"
      bind:value={query}
      placeholder="Buscar en los registros…"
      aria-label="Buscar registros"
    />
  </label>

  {#if filterableColumns.length}
    <div class="quick-filters">
      <label class="quick-filter-control">
        <span>Filtrar por</span>
        <select value={filterKey} onchange={changeFilterColumn} aria-label="Columna para filtrar">
          <option value="">Todos los campos</option>
          {#each filterableColumns as column (column.key)}
            <option value={column.key}>{column.label}</option>
          {/each}
        </select>
      </label>

      {#if filterKey}
        <label class="quick-filter-control value-filter" in:fly={flyMotion({ x: -8, duration: 180 })}>
          <span>Valor</span>
          <select bind:value={filterValue} onchange={() => (page = 1)} aria-label="Valor del filtro">
            <option value="">Todos</option>
            {#each filterValues as value (String(value))}
              <option value={String(value)}>
                {display(value, columns.find((column) => column.key === filterKey), lookups)}
              </option>
            {/each}
          </select>
        </label>
      {/if}

      {#if query || filterKey}
        <button type="button" class="clear-filters" onclick={clearFilters}>Limpiar</button>
      {/if}
    </div>
  {/if}

  <div class="table-tools-right">
    <label class="page-size-control">
      <span>Filas</span>
      <select bind:value={size} onchange={() => (page = 1)} aria-label="Filas por página">
        <option value={8}>8</option>
        <option value={16}>16</option>
        <option value={32}>32</option>
      </select>
    </label>
    <div class="table-result" aria-live="polite">
      {filtered.length} {filtered.length === 1 ? 'registro' : 'registros'}
    </div>
  </div>
</div>

<div role="status" class="visually-hidden">{sortAnnouncement}</div>

{#if !data.length}
  <div class="table-empty">
    <span class="empty-table-icon"><Search size={17} aria-hidden="true" /></span>
    <strong>Sin registros todavía</strong>
    <small>La información que se registre en este módulo aparecerá aquí.</small>
  </div>
{:else if !filtered.length}
  <div class="table-empty">
    <span class="empty-table-icon"><Search size={17} aria-hidden="true" /></span>
    <strong>No encontramos coincidencias</strong>
    <small>Prueba con otro nombre o cambia el texto de búsqueda.</small>
  </div>
{:else}
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <div tabindex="0" role="region" aria-labelledby={captionId} class="table-scroll">
    <table class="data-table">
      <caption id={captionId} class="visually-hidden">{caption}</caption>
      <thead>
        <tr>
          {#each columns as column (column.key)}
            <th
              scope="col"
              aria-sort={order.key === column.key ? (order.asc ? 'ascending' : 'descending') : undefined}
            >
              <button type="button" class="th-button" onclick={() => sort(column)}>
                <span>{column.label}</span>
                <span class="sort-icon" aria-hidden="true">
                  {#if order.key === column.key}
                    <ArrowUp size={13} />
                  {:else}
                    <ArrowUpDown size={13} />
                  {/if}
                </span>
              </button>
            </th>
          {/each}
          {#if canUpdate || canDelete}
            <th scope="col" class="actions-heading">Acciones</th>
          {/if}
        </tr>
      </thead>
      <tbody>
        {#each visible as row (row._id)}
          <tr>
            {#each columns as column (column.key)}
              <td data-label={column.label}>
                {#if column.type === 'status'}
                  <StatusBadge value={row[column.key]} />
                {:else if column.type === 'rating'}
                  <span class="rating-value">★ {display(row[column.key], column, lookups)}</span>
                {:else if column.type === 'link' && row[column.key]}
                  <a href={row[column.key]} target="_blank" rel="noreferrer" class="table-link">Ver archivo</a>
                {:else}
                  <span class:cell-muted={row[column.key] == null}>{display(row[column.key], column, lookups)}</span>
                {/if}
              </td>
            {/each}
            {#if canUpdate || canDelete}
              <td data-label="Acciones" class="actions-cell">
                <div class="row-actions">
                  {#if canUpdate}
                    <button type="button" class="row-action" onclick={() => onedit(row)} aria-label="Editar registro">
                      <Eye size={15} aria-hidden="true" /><span>Ver / editar</span>
                    </button>
                  {/if}
                  {#if canDelete}
                    <button type="button" class="row-action danger" onclick={() => ondelete(row)} aria-label="Eliminar registro">
                      Eliminar
                    </button>
                  {/if}
                </div>
              </td>
            {/if}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  <footer class="table-footer">
    <span>Mostrando {Math.min((page - 1) * size + 1, filtered.length)}–{Math.min(page * size, filtered.length)} de {filtered.length}</span>
    <div class="pagination">
      <button type="button" class="icon-button" disabled={page === 1} onclick={() => page--} aria-label="Página anterior">
        <ChevronLeft size={17} aria-hidden="true" />
      </button>
      <span>Página {page} de {totalPages}</span>
      <button type="button" class="icon-button" disabled={page >= totalPages} onclick={() => page++} aria-label="Página siguiente">
        <ChevronRight size={17} aria-hidden="true" />
      </button>
    </div>
  </footer>
{/if}

<style>
  .quick-filters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .quick-filter-control {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: #5b6778;
    font-size: 0.8125rem;
    white-space: nowrap;
  }

  .quick-filter-control select {
    max-width: 11rem;
    min-height: 2.125rem;
    padding: 0 0.55rem;
    border: 1px solid #d9dfe8;
    border-radius: 0.45rem;
    background: #fff;
    color: #364357;
    font-size: 0.8125rem;
  }

  .clear-filters {
    border: 0;
    background: transparent;
    color: #2f56c6;
    cursor: pointer;
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 0.3rem 0.45rem;
  }

  .table-tools-right {
    display: flex;
    align-items: center;
    gap: 0.9rem;
  }

  .page-size-control {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    color: #5b6778;
    font-size: 0.8125rem;
    white-space: nowrap;
  }

  .page-size-control select {
    min-width: 3.5rem;
    min-height: 2.125rem;
    padding: 0 0.45rem;
    border: 1px solid #d9dfe8;
    border-radius: 0.45rem;
    background: #fff;
    color: #364357;
    font-size: 0.8125rem;
  }

  .table-scroll {
    overflow: auto;
    max-inline-size: 100%;
    max-block-size: min(36rem, 75dvh);
    container-type: inline-size;
    scrollbar-color: #cbd3df transparent;
    scrollbar-width: thin;
  }

  .table-scroll:focus-visible {
    outline: 2px solid #315dce;
    outline-offset: -2px;
  }

  .data-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    text-align: left;
  }

  .data-table thead {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
    background: #f8f9fb;
  }

  .data-table th:has(> .th-button) {
    padding: 0;
  }

  .th-button {
    width: 100%;
    min-height: 2.5rem;
    padding: 0.5rem 0.9375rem;
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    border: 0;
    background: none;
    color: inherit;
    text-transform: inherit;
    font-size: inherit;
    letter-spacing: inherit;
    font-weight: inherit;
    text-align: left;
  }

  .data-table th:first-child .th-button {
    padding-left: 1.25rem;
  }

  th[aria-sort] {
    color: #2649a8;
  }

  .sort-icon {
    display: inline-flex;
    align-items: center;
    opacity: 0.65;
    transition: transform 220ms cubic-bezier(0.22, 1, 0.36, 1), opacity 150ms ease-out, color 150ms ease-out;
  }

  th[aria-sort] .sort-icon {
    opacity: 1;
    color: #315dce;
  }

  th[aria-sort='descending'] .sort-icon {
    transform: rotate(180deg);
  }

  .table-empty {
    flex-direction: column;
    gap: 0.4rem;
    min-height: 10rem;
    padding: 1.5rem;
    text-align: center;
    animation: table-empty-in 240ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
  }

  @keyframes table-empty-in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .sort-icon {
      transition: none;
    }

    .table-empty {
      animation: none;
    }
  }

  .empty-table-icon {
    display: grid;
    width: 2.25rem;
    height: 2.25rem;
    margin-bottom: 0.25rem;
    place-items: center;
    border-radius: 0.625rem;
    background: #f1f4fb;
    color: #5d76b8;
  }

  .table-empty strong {
    color: #39475a;
    font-size: 0.9375rem;
  }

  .table-empty small {
    color: #5b6778;
    font-size: 0.8125rem;
  }

  @container (width < 600px) {
    .data-table,
    .data-table thead,
    .data-table tbody,
    .data-table tr,
    .data-table th,
    .data-table td {
      display: block;
    }

    .data-table thead {
      display: none;
    }

    .data-table tbody {
      padding: 0.75rem;
    }

    .data-table tr {
      margin-block-end: 0.75rem;
      border: 1px solid #e4e9f1;
      border-radius: 0.625rem;
      background: #fff;
      padding: 0.5rem 0.75rem;
    }

    .data-table tr:last-child {
      margin-block-end: 0;
    }

    .data-table td,
    .data-table td:first-child {
      height: auto;
      max-width: none;
      white-space: normal;
      padding: 0.45rem 0;
      border-bottom: 1px solid #f1f4f8;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
    }

    .data-table td:last-child {
      border-bottom: 0;
    }

    .data-table td::before {
      content: attr(data-label) ': ';
      font-weight: 700;
      font-size: 0.75rem;
      color: #5b6778;
      flex: 0 0 auto;
    }

    .actions-cell {
      justify-content: flex-end;
    }

    .actions-cell::before {
      margin-right: auto;
    }
  }

  @media (max-width: 540px) {
    .quick-filters {
      width: 100%;
    }

    .table-tools-right {
      width: 100%;
      justify-content: space-between;
    }
  }
</style>
