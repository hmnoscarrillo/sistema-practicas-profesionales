<script>
  import { onMount, untrack } from 'svelte';
  import {
    BriefcaseBusiness,
    Activity,
    FileCheck2,
    Award,
    SlidersHorizontal,
    CalendarRange,
    RotateCcw,
    Copy,
    Check,
    ExternalLink,
    RefreshCw,
    AlertCircle,
    BarChart3,
    PieChart,
  } from 'lucide-svelte';
  import { api } from '../api.js';
  import { animateCount } from '../motion.js';

  let { embedded = false, onnotify = () => {} } = $props();

  const palette = ['#2552d0', '#0ea5e9', '#7c3aed', '#10b981', '#f59e0b', '#ec4899'];

  let loading = $state(true);
  let error = $state('');
  let copied = $state(false);
  let customEmbedUrl = $state('');

  let filters = $state({
    programa: '',
    empresa: '',
    modalidad: '',
    estado: '',
    fecha_desde: '',
    fecha_hasta: '',
  });

  let payload = $state({
    kpis: {
      total_practicas: 0,
      practicas_en_proceso: 0,
      convenios_vigentes: 0,
      promedio_evaluacion: 0,
    },
    graficos: {
      por_estado: [],
      por_modalidad: [],
      por_programa: [],
      por_empresa: [],
      seguimientos_por_tipo: [],
      convenios_por_estado: [],
    },
    filtros_disponibles: {
      programas: [],
      empresas: [],
      modalidades: [],
      estados: [],
    },
  });

  let defaultEmbedUrl = $derived(
    typeof window !== 'undefined' ? `${window.location.origin}/?embed=tablero` : '/?embed=tablero',
  );
  let activeIframeUrl = $derived(customEmbedUrl.trim() || defaultEmbedUrl);

  let kpiDisplay = $state({
    total_practicas: 0,
    practicas_en_proceso: 0,
    convenios_vigentes: 0,
    promedio_evaluacion: 0,
  });

  $effect(() => {
    const kpis = payload?.kpis || {};
    const specs = [
      { key: 'total_practicas', decimals: 0 },
      { key: 'practicas_en_proceso', decimals: 0 },
      { key: 'convenios_vigentes', decimals: 0 },
      { key: 'promedio_evaluacion', decimals: 2 },
    ];
    const cleanups = specs.map(({ key, decimals }) => {
      const target = Number(kpis[key] || 0);
      const start = untrack(() => kpiDisplay[key]);
      return animateCount({
        from: start,
        to: target,
        duration: 720,
        decimals,
        onUpdate: (val) => {
          kpiDisplay[key] = val;
        },
      });
    });
    return () => cleanups.forEach((fn) => fn());
  });

  async function loadDashboard() {
    loading = true;
    error = '';
    try {
      const params = new URLSearchParams();
      for (const [k, v] of Object.entries(filters)) {
        if (v) params.set(k, v);
      }
      const qs = params.toString();
      payload = await api(`/tablero/resumen${qs ? `?${qs}` : ''}`);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function resetFilters() {
    filters = {
      programa: '',
      empresa: '',
      modalidad: '',
      estado: '',
      fecha_desde: '',
      fecha_hasta: '',
    };
    loadDashboard();
  }

  async function copyShareUrl() {
    try {
      await navigator.clipboard.writeText(activeIframeUrl);
      copied = true;
      onnotify('Enlace del tablero copiado al portapapeles.');
      setTimeout(() => (copied = false), 2500);
    } catch {
      onnotify('No se pudo copiar automáticamente; copia el enlace desde el campo.', 'error');
    }
  }

  function conicGradientFor(items) {
    const valid = (items || []).filter((i) => Number(i.value) > 0);
    const total = valid.reduce((sum, i) => sum + Number(i.value), 0);
    if (!total) return 'conic-gradient(#d8e2f3 0% 100%)';

    let acc = 0;
    const stops = valid.map((item, idx) => {
      const start = (acc / total) * 100;
      acc += Number(item.value);
      const end = (acc / total) * 100;
      const color = palette[idx % palette.length];
      return `${color} ${start.toFixed(2)}% ${end.toFixed(2)}%`;
    });
    return `conic-gradient(${stops.join(', ')})`;
  }

  function totalOf(items) {
    return (items || []).reduce((sum, item) => sum + Number(item.value || 0), 0);
  }

  function maxOf(items) {
    return Math.max(1, ...(items || []).map((item) => Number(item.value || 0)));
  }

  onMount(() => {
    if (embedded) {
      loadDashboard();
    } else {
      loading = false;
    }
  });
</script>

{#if !embedded}
  <section class="tablero-host">
    <div class="panel glass-panel tablero-share-bar">
      <div class="tablero-share-copy">
        <span class="panel-kicker">MÓDULO TABLERO · EMBEBIDO EN IFRAME</span>
        <h2>Tablero analítico de prácticas profesionales</h2>
        <p>
          Visualización interactiva publicada mediante <code>&lt;iframe&gt;</code> con 4 indicadores, 6 gráficos de
          barras/circulares y 2 paneles de filtros.
        </p>
      </div>

      <div class="tablero-share-controls">
        <label class="tablero-url-field">
          <span class="visually-hidden">URL embebida del tablero</span>
          <input
            type="url"
            bind:value={customEmbedUrl}
            placeholder={defaultEmbedUrl}
            aria-label="URL del tablero embebido"
          />
        </label>
        <button type="button" class="button secondary" onclick={copyShareUrl}>
          {#if copied}
            <Check size={15} aria-hidden="true" />
            Copiado
          {:else}
            <Copy size={15} aria-hidden="true" />
            Copiar enlace
          {/if}
        </button>
        <a
          class="button primary"
          href={activeIframeUrl}
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={15} aria-hidden="true" />
          Abrir tablero
        </a>
      </div>
    </div>

    <div class="panel glass-panel tablero-iframe-shell">
      <iframe
        src={activeIframeUrl}
        title="Tablero interactivo de prácticas profesionales"
        class="tablero-iframe"
      ></iframe>
    </div>
  </section>
{:else}
  <main class="tablero-embed-canvas">
    <header class="tablero-embed-header">
      <div>
        <span class="panel-kicker">TABLERO ANALÍTICO EN TIEMPO REAL</span>
        <h1>Indicadores y analítica de prácticas profesionales</h1>
      </div>
      <button type="button" class="button secondary" onclick={loadDashboard} disabled={loading}>
        <RefreshCw size={15} class={loading ? 'spin' : ''} aria-hidden="true" />
        Actualizar
      </button>
    </header>

    {#if error}
      <div class="notice error-notice" role="alert">
        <AlertCircle size={18} aria-hidden="true" />
        <div>
          <strong>No se pudo cargar el tablero</strong>
          <span>{error}</span>
        </div>
        <button type="button" class="button secondary" onclick={loadDashboard}>Reintentar</button>
      </div>
    {/if}

    <!-- Distribución exigida: Izquierda (4 Rojos arriba + 6 Verdes abajo 2x3), Derecha (2 Violetas) -->
    <div class="tablero-board-grid">
      <div class="tablero-left-zone">
        <!-- 4 BLOQUES ROJOS: Indicadores -->
        <section class="tablero-red-row" aria-label="Indicadores clave de desempeño">
          <article class="tablero-kpi-card glass-card">
            <span class="zone-tag red-tag">INDICADOR 01</span>
            <div class="kpi-row">
              <span class="kpi-icon red"><BriefcaseBusiness size={18} aria-hidden="true" /></span>
              <strong>{kpiDisplay.total_practicas}</strong>
            </div>
            <p>Total prácticas</p>
          </article>

          <article class="tablero-kpi-card glass-card">
            <span class="zone-tag red-tag">INDICADOR 02</span>
            <div class="kpi-row">
              <span class="kpi-icon red"><Activity size={18} aria-hidden="true" /></span>
              <strong>{kpiDisplay.practicas_en_proceso}</strong>
            </div>
            <p>En proceso</p>
          </article>

          <article class="tablero-kpi-card glass-card">
            <span class="zone-tag red-tag">INDICADOR 03</span>
            <div class="kpi-row">
              <span class="kpi-icon red"><FileCheck2 size={18} aria-hidden="true" /></span>
              <strong>{kpiDisplay.convenios_vigentes}</strong>
            </div>
            <p>Convenios vigentes</p>
          </article>

          <article class="tablero-kpi-card glass-card">
            <span class="zone-tag red-tag">INDICADOR 04</span>
            <div class="kpi-row">
              <span class="kpi-icon red"><Award size={18} aria-hidden="true" /></span>
              <strong>{Number(kpiDisplay.promedio_evaluacion || 0).toFixed(2)}</strong>
            </div>
            <p>Promedio nota final</p>
          </article>
        </section>

        <!-- 6 BLOQUES VERDES (cuadrícula 2x3): Únicamente gráficos de barras o circulares -->
        <section class="tablero-green-grid" aria-label="Gráficos estadísticos">
          <!-- Gráfico 1: Circular - Prácticas por Estado -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">CIRCULAR</span>
                <h2>Prácticas por estado</h2>
              </div>
              <PieChart size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.por_estado.length}
              {@const total = totalOf(payload.graficos.por_estado)}
              <div class="pie-layout">
                <div
                  class="pie-ring"
                  role="img"
                  aria-label="Distribución circular de prácticas por estado"
                  style={`background: ${conicGradientFor(payload.graficos.por_estado)}`}
                >
                  <span class="pie-hole"><strong>{total}</strong><small>Total</small></span>
                </div>
                <dl class="chart-legend-list">
                  {#each payload.graficos.por_estado as item, idx (item.label)}
                    <div class="chart-legend-row">
                      <dt>
                        <span class="swatch" style={`background:${palette[idx % palette.length]}`}></span>
                        {item.label}
                      </dt>
                      <dd>{item.value} ({Math.round((Number(item.value) / Math.max(1, total)) * 100)}%)</dd>
                    </div>
                  {/each}
                </dl>
              </div>
            {:else}
              <p class="chart-empty">Sin datos para los filtros seleccionados.</p>
            {/if}
          </article>

          <!-- Gráfico 2: Circular - Prácticas por Modalidad -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">CIRCULAR</span>
                <h2>Prácticas por modalidad</h2>
              </div>
              <PieChart size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.por_modalidad.length}
              {@const total = totalOf(payload.graficos.por_modalidad)}
              <div class="pie-layout">
                <div
                  class="pie-ring"
                  role="img"
                  aria-label="Distribución circular de prácticas por modalidad"
                  style={`background: ${conicGradientFor(payload.graficos.por_modalidad)}`}
                >
                  <span class="pie-hole"><strong>{total}</strong><small>Total</small></span>
                </div>
                <dl class="chart-legend-list">
                  {#each payload.graficos.por_modalidad as item, idx (item.label)}
                    <div class="chart-legend-row">
                      <dt>
                        <span class="swatch" style={`background:${palette[idx % palette.length]}`}></span>
                        {item.label}
                      </dt>
                      <dd>{item.value} ({Math.round((Number(item.value) / Math.max(1, total)) * 100)}%)</dd>
                    </div>
                  {/each}
                </dl>
              </div>
            {:else}
              <p class="chart-empty">Sin datos para los filtros seleccionados.</p>
            {/if}
          </article>

          <!-- Gráfico 3: Barras - Prácticas por Programa -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">BARRAS</span>
                <h2>Prácticas por programa</h2>
              </div>
              <BarChart3 size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.por_programa.length}
              {@const maxVal = maxOf(payload.graficos.por_programa)}
              <div class="bar-list">
                {#each payload.graficos.por_programa as item, idx (item.label)}
                  <div class="bar-item">
                    <div class="bar-meta">
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                    <div class="bar-track" aria-hidden="true">
                      <span
                        class="bar-fill"
                        style={`width:${(Number(item.value) / maxVal) * 100}%; background:${palette[idx % palette.length]}`}
                      ></span>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="chart-empty">Sin datos para los filtros seleccionados.</p>
            {/if}
          </article>

          <!-- Gráfico 4: Barras - Prácticas por Empresa -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">BARRAS</span>
                <h2>Prácticas por empresa</h2>
              </div>
              <BarChart3 size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.por_empresa.length}
              {@const maxVal = maxOf(payload.graficos.por_empresa)}
              <div class="bar-list">
                {#each payload.graficos.por_empresa as item, idx (item.label)}
                  <div class="bar-item">
                    <div class="bar-meta">
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                    <div class="bar-track" aria-hidden="true">
                      <span
                        class="bar-fill"
                        style={`width:${(Number(item.value) / maxVal) * 100}%; background:${palette[(idx + 1) % palette.length]}`}
                      ></span>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="chart-empty">Sin datos para los filtros seleccionados.</p>
            {/if}
          </article>

          <!-- Gráfico 5: Barras - Seguimientos por Tipo -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">BARRAS</span>
                <h2>Seguimientos por tipo</h2>
              </div>
              <BarChart3 size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.seguimientos_por_tipo.length}
              {@const maxVal = maxOf(payload.graficos.seguimientos_por_tipo)}
              <div class="bar-list">
                {#each payload.graficos.seguimientos_por_tipo as item, idx (item.label)}
                  <div class="bar-item">
                    <div class="bar-meta">
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                    <div class="bar-track" aria-hidden="true">
                      <span
                        class="bar-fill"
                        style={`width:${(Number(item.value) / maxVal) * 100}%; background:${palette[(idx + 2) % palette.length]}`}
                      ></span>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="chart-empty">Sin seguimientos para los filtros seleccionados.</p>
            {/if}
          </article>

          <!-- Gráfico 6: Circular - Convenios por Estado -->
          <article class="tablero-chart-card glass-card">
            <header class="chart-card-head">
              <div>
                <span class="zone-tag green-tag">CIRCULAR</span>
                <h2>Convenios por estado</h2>
              </div>
              <PieChart size={16} aria-hidden="true" />
            </header>
            {#if payload.graficos.convenios_por_estado.length}
              {@const total = totalOf(payload.graficos.convenios_por_estado)}
              <div class="pie-layout">
                <div
                  class="pie-ring"
                  role="img"
                  aria-label="Distribución circular de convenios por estado"
                  style={`background: ${conicGradientFor(payload.graficos.convenios_por_estado)}`}
                >
                  <span class="pie-hole"><strong>{total}</strong><small>Total</small></span>
                </div>
                <dl class="chart-legend-list">
                  {#each payload.graficos.convenios_por_estado as item, idx (item.label)}
                    <div class="chart-legend-row">
                      <dt>
                        <span class="swatch" style={`background:${palette[(idx + 3) % palette.length]}`}></span>
                        {item.label}
                      </dt>
                      <dd>{item.value} ({Math.round((Number(item.value) / Math.max(1, total)) * 100)}%)</dd>
                    </div>
                  {/each}
                </dl>
              </div>
            {:else}
              <p class="chart-empty">Sin convenios para los filtros seleccionados.</p>
            {/if}
          </article>
        </section>
      </div>

      <!-- 2 BLOQUES VIOLETAS (derecha): Paneles de filtros interactivos -->
      <aside class="tablero-violet-col" aria-label="Paneles de filtros del tablero">
        <section class="tablero-filter-card glass-card">
          <header class="filter-card-head">
            <span class="zone-tag violet-tag">FILTROS 01</span>
            <h2><SlidersHorizontal size={16} aria-hidden="true" /> Filtros institucionales</h2>
          </header>

          <div class="filter-stack">
            <label class="form-field">
              <span>Programa académico</span>
              <select bind:value={filters.programa} onchange={loadDashboard}>
                <option value="">Todos los programas</option>
                {#each payload.filtros_disponibles.programas as prog (prog)}
                  <option value={prog}>{prog}</option>
                {/each}
              </select>
            </label>

            <label class="form-field">
              <span>Empresa aliada</span>
              <select bind:value={filters.empresa} onchange={loadDashboard}>
                <option value="">Todas las empresas</option>
                {#each payload.filtros_disponibles.empresas as emp (emp)}
                  <option value={emp}>{emp}</option>
                {/each}
              </select>
            </label>

            <label class="form-field">
              <span>Modalidad</span>
              <select bind:value={filters.modalidad} onchange={loadDashboard}>
                <option value="">Todas las modalidades</option>
                {#each payload.filtros_disponibles.modalidades as mod (mod)}
                  <option value={mod}>{mod}</option>
                {/each}
              </select>
            </label>
          </div>
        </section>

        <section class="tablero-filter-card glass-card">
          <header class="filter-card-head">
            <span class="zone-tag violet-tag">FILTROS 02</span>
            <h2><CalendarRange size={16} aria-hidden="true" /> Estado y periodo</h2>
          </header>

          <div class="filter-stack">
            <label class="form-field">
              <span>Estado de práctica</span>
              <select bind:value={filters.estado} onchange={loadDashboard}>
                <option value="">Todos los estados</option>
                {#each payload.filtros_disponibles.estados as est (est)}
                  <option value={est}>{est}</option>
                {/each}
              </select>
            </label>

            <label class="form-field">
              <span>Fecha de inicio desde</span>
              <input type="date" bind:value={filters.fecha_desde} onchange={loadDashboard} />
            </label>

            <label class="form-field">
              <span>Fecha de finalización hasta</span>
              <input type="date" bind:value={filters.fecha_hasta} onchange={loadDashboard} />
            </label>

            <button type="button" class="button secondary full-btn" onclick={resetFilters}>
              <RotateCcw size={15} aria-hidden="true" />
              Limpiar filtros
            </button>
          </div>
        </section>
      </aside>
    </div>
  </main>
{/if}
