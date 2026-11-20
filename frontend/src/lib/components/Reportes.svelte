<script>
  import { onMount } from 'svelte';
  import {
    FileSpreadsheet,
    FileDown,
    Mail,
    Search,
    RotateCcw,
    CalendarRange,
    Building2,
    BookOpen,
    AlertCircle,
    Send,
    LoaderCircle,
  } from 'lucide-svelte';
  import { api, apiBase } from '../api.js';
  import Modal from './Modal.svelte';
  import StatusBadge from './StatusBadge.svelte';

  let { onnotify = () => {} } = $props();

  let loading = $state(false);
  let exporting = $state('');
  let error = $state('');

  let available = $state({
    programas: [],
    empresas: [],
    estados: [],
    modalidades: [],
  });

  let filters = $state({
    fecha_desde: '',
    fecha_hasta: '',
    programa: '',
    empresa: '',
    estado: '',
    modalidad: '',
  });

  let report = $state({
    generado: '',
    criterios: 'Todos los registros activos',
    total: 0,
    columnas: [],
    registros: [],
  });

  let mailOpen = $state(false);
  let mailSending = $state(false);
  let mailError = $state('');
  let mailForm = $state({
    destinatario: '',
    asunto: 'Reporte de Prácticas Profesionales',
    formato: 'pdf',
    mensaje: 'Adjunto se remite el reporte consolidado de prácticas profesionales.',
  });

  function buildQuery() {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v) params.set(k, v);
    }
    return params.toString();
  }

  async function loadFilters() {
    try {
      available = await api('/reportes/filtros');
    } catch {
      // Si la BD no responde al inicio, los selectores permanecen vacíos hasta consultar.
    }
  }

  async function runReport() {
    if (filters.fecha_desde && filters.fecha_hasta && filters.fecha_hasta < filters.fecha_desde) {
      error = 'La fecha final no puede ser anterior a la fecha inicial.';
      return;
    }
    loading = true;
    error = '';
    try {
      const qs = buildQuery();
      report = await api(`/reportes/practicas${qs ? `?${qs}` : ''}`);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  function clearFilters() {
    filters = {
      fecha_desde: '',
      fecha_hasta: '',
      programa: '',
      empresa: '',
      estado: '',
      modalidad: '',
    };
    runReport();
  }

  async function downloadFile(format) {
    if (filters.fecha_desde && filters.fecha_hasta && filters.fecha_hasta < filters.fecha_desde) {
      onnotify('La fecha final no puede ser anterior a la fecha inicial.', 'error');
      return;
    }
    exporting = format;
    try {
      const token = localStorage.getItem('practicas.token');
      const qs = buildQuery();
      const response = await fetch(`${apiBase}/reportes/exportar/${format}${qs ? `?${qs}` : ''}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `No se pudo generar el archivo (${response.status})`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download =
        format === 'pdf'
          ? 'reporte-practicas-profesionales.pdf'
          : 'reporte-practicas-profesionales.xlsx';
      link.click();
      URL.revokeObjectURL(url);
      onnotify(`Reporte en ${format.toUpperCase()} descargado correctamente.`);
    } catch (err) {
      onnotify(err.message, 'error');
    } finally {
      exporting = '';
    }
  }

  async function sendEmail(e) {
    e.preventDefault();
    mailSending = true;
    mailError = '';
    try {
      const body = {
        ...mailForm,
        fecha_desde: filters.fecha_desde || null,
        fecha_hasta: filters.fecha_hasta || null,
        programa: filters.programa || null,
        empresa: filters.empresa || null,
        estado: filters.estado || null,
        modalidad: filters.modalidad || null,
      };
      const res = await api('/reportes/enviar-correo', {
        method: 'POST',
        body: JSON.stringify(body),
      });
      mailOpen = false;
      onnotify(res.mensaje || 'Reporte enviado por correo.');
    } catch (err) {
      mailError = err.message;
    } finally {
      mailSending = false;
    }
  }

  onMount(async () => {
    await loadFilters();
    await runReport();
  });
</script>

<section class="reportes-view">
  <div class="panel glass-panel reportes-filters-card">
    <div class="reportes-head">
      <div>
        <span class="panel-kicker">CRITERIOS DE BÚSQUEDA (MULTITABLA · SIN IDs)</span>
        <h2>Generador de reportes institucionales</h2>
        <p>Combina rango de fechas, programa académico, empresa aliada y estado antes de visualizar o exportar.</p>
      </div>
      <div class="reportes-actions">
        <button type="button" class="button secondary" onclick={clearFilters}>
          <RotateCcw size={15} aria-hidden="true" />
          Limpiar
        </button>
        <button
          type="button"
          class="button secondary"
          disabled={exporting === 'pdf'}
          onclick={() => downloadFile('pdf')}
        >
          {#if exporting === 'pdf'}
            <LoaderCircle size={15} class="spin" aria-hidden="true" />
          {:else}
            <FileDown size={15} aria-hidden="true" />
          {/if}
          Exportar PDF
        </button>
        <button
          type="button"
          class="button secondary"
          disabled={exporting === 'excel'}
          onclick={() => downloadFile('excel')}
        >
          {#if exporting === 'excel'}
            <LoaderCircle size={15} class="spin" aria-hidden="true" />
          {:else}
            <FileSpreadsheet size={15} aria-hidden="true" />
          {/if}
          Exportar Excel
        </button>
        <button
          type="button"
          class="button primary"
          onclick={() => {
            mailError = '';
            mailOpen = true;
          }}
        >
          <Mail size={15} aria-hidden="true" />
          Enviar por correo
        </button>
      </div>
    </div>

    <form
      class="reportes-criteria-grid"
      onsubmit={(e) => {
        e.preventDefault();
        runReport();
      }}
    >
      <label class="form-field">
        <span><CalendarRange size={13} aria-hidden="true" /> Fecha desde</span>
        <input type="date" bind:value={filters.fecha_desde} />
      </label>

      <label class="form-field">
        <span><CalendarRange size={13} aria-hidden="true" /> Fecha hasta</span>
        <input type="date" bind:value={filters.fecha_hasta} />
      </label>

      <label class="form-field">
        <span><BookOpen size={13} aria-hidden="true" /> Programa académico</span>
        <select bind:value={filters.programa}>
          <option value="">Todos los programas</option>
          {#each available.programas as prog (prog)}
            <option value={prog}>{prog}</option>
          {/each}
        </select>
      </label>

      <label class="form-field">
        <span><Building2 size={13} aria-hidden="true" /> Empresa aliada</span>
        <select bind:value={filters.empresa}>
          <option value="">Todas las empresas</option>
          {#each available.empresas as emp (emp)}
            <option value={emp}>{emp}</option>
          {/each}
        </select>
      </label>

      <label class="form-field">
        <span>Estado</span>
        <select bind:value={filters.estado}>
          <option value="">Todos los estados</option>
          {#each available.estados as est (est)}
            <option value={est}>{est}</option>
          {/each}
        </select>
      </label>

      <label class="form-field">
        <span>Modalidad</span>
        <select bind:value={filters.modalidad}>
          <option value="">Todas</option>
          {#each available.modalidades as mod (mod)}
            <option value={mod}>{mod}</option>
          {/each}
        </select>
      </label>

      <div class="reportes-submit-cell">
        <button type="submit" class="button primary" disabled={loading}>
          {#if loading}
            <LoaderCircle size={15} class="spin" aria-hidden="true" />
            Consultando…
          {:else}
            <Search size={15} aria-hidden="true" />
            Visualizar reporte
          {/if}
        </button>
      </div>
    </form>
  </div>

  {#if error}
    <div class="notice error-notice" role="alert">
      <AlertCircle size={18} aria-hidden="true" />
      <div>
        <strong>No se pudo generar la vista previa</strong>
        <span>{error}</span>
      </div>
      <button type="button" class="button secondary" onclick={runReport}>Reintentar</button>
    </div>
  {:else}
    <!-- Documento con encabezado, criterios, tabla sin IDs y pie -->
    <article class="panel glass-panel report-sheet">
      <header class="report-sheet-header">
        <div>
          <span class="report-sheet-kicker">SISTEMA DE GESTIÓN DE PRÁCTICAS PROFESIONALES</span>
          <h3>Reporte Consolidado de Prácticas</h3>
          <p><strong>Criterios aplicados:</strong> {report.criterios}</p>
        </div>
        <div class="report-sheet-meta">
          {#key report.generado}
            <span class="count-pill report-count-pop">{report.total} {report.total === 1 ? 'registro' : 'registros'}</span>
          {/key}
          {#if report.generado}
            <small>Generado: {report.generado.replace('T', ' ')}</small>
          {/if}
        </div>
      </header>

      {#if loading}
        <div class="table-empty">
          <span class="loading-spinner" aria-hidden="true"></span>
          <span>Consultando tablas relacionadas…</span>
        </div>
      {:else if !report.registros.length}
        <div class="table-empty">
          <Search size={18} aria-hidden="true" />
          <span>No se encontraron registros para los criterios seleccionados.</span>
        </div>
      {:else}
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div class="table-scroll report-table-wrap" tabindex="0" role="region" aria-label="Vista previa del reporte">
          <table class="data-table">
            <thead>
              <tr>
                {#each report.columnas as col (col.key)}
                  <th scope="col">{col.label}</th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each report.registros as row, i (i)}
                <tr>
                  {#each report.columnas as col (col.key)}
                    <td>
                      {#if col.key === 'estado'}
                        <StatusBadge value={row[col.key]} />
                      {:else if col.key === 'nota_final'}
                        <span class="rating-value">
                          {row[col.key] != null ? `★ ${Number(row[col.key]).toFixed(1)}` : '—'}
                        </span>
                      {:else}
                        {row[col.key] ?? '—'}
                      {/if}
                    </td>
                  {/each}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}

      <footer class="report-sheet-footer">
        <span>Fuente: Prácticas · Estudiantes · Programas · Empresas · Convenios · Tutores · Evaluaciones</span>
        <span>Documento formateado sin identificadores internos (*_id)</span>
      </footer>
    </article>
  {/if}
</section>

{#if mailOpen}
  <Modal
    title="Enviar reporte por correo"
    subtitle="Adjunta el reporte generado con los filtros actuales en PDF, Excel o ambos."
    onclose={() => (mailOpen = false)}
  >
    <form class="record-form" onsubmit={sendEmail}>
      <div class="form-grid">
        <label class="form-field required-field full-width">
          <span>Correo destinatario</span>
          <input
            type="email"
            bind:value={mailForm.destinatario}
            placeholder="ejemplo@institucion.edu.co"
            required
          />
        </label>

        <label class="form-field required-field">
          <span>Asunto</span>
          <input type="text" bind:value={mailForm.asunto} required />
        </label>

        <label class="form-field required-field">
          <span>Formato adjunto</span>
          <select bind:value={mailForm.formato} required>
            <option value="pdf">Documento PDF</option>
            <option value="excel">Libro Excel (.xlsx)</option>
            <option value="ambos">Ambos (PDF + Excel)</option>
          </select>
        </label>

        <label class="form-field full-width">
          <span>Mensaje</span>
          <textarea rows="3" bind:value={mailForm.mensaje}></textarea>
        </label>
      </div>

      {#if mailError}
        <div class="form-error inline-date-error" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <span>{mailError}</span>
        </div>
      {/if}

      <div class="form-footer">
        <span class="form-note">Se enviarán {report.total} registros según los filtros actuales.</span>
        <div class="form-actions">
          <button type="button" class="button secondary" onclick={() => (mailOpen = false)}>Cancelar</button>
          <button type="submit" class="button primary" disabled={mailSending}>
            {#if mailSending}
              <LoaderCircle size={16} class="spin" aria-hidden="true" />
              Enviando…
            {:else}
              <Send size={16} aria-hidden="true" />
              Enviar ahora
            {/if}
          </button>
        </div>
      </div>
    </form>
  </Modal>
{/if}
