<script>
  import { onMount, onDestroy, tick } from 'svelte';
  import {
    Search,
    Bell,
    RefreshCw,
    BriefcaseBusiness,
    CheckCircle2,
    AlertCircle,
    X,
    ShieldAlert,
    CalendarClock,
    ArrowRight,
  } from 'lucide-svelte';
  import { api, rows } from './lib/api.js';
  import { moduleDefinitions } from './lib/data/modules.js';
  import Login from './lib/components/Login.svelte';
  import ModuleTabs from './lib/components/ModuleTabs.svelte';
  import PageHeader from './lib/components/PageHeader.svelte';
  import Dashboard from './lib/components/Dashboard.svelte';
  import DataTable from './lib/components/DataTable.svelte';
  import RecordForm from './lib/components/RecordForm.svelte';
  import Modal from './lib/components/Modal.svelte';
  import Toast from './lib/components/Toast.svelte';
  import UserManager from './lib/components/UserManager.svelte';

  let roles = $state([]);
  let users = $state([]);
  let session = $state(null);
  let permissionRows = $state([]);
  let activeCode = $state('dashboard');
  let toast = $state({ message: '', kind: 'success' });
  let toastTimer;
  let loading = $state(false);
  let refreshing = $state(false);
  let pageError = $state('');
  let formOpen = $state(false);
  let deleting = $state(null);
  let editing = $state(null);
  let saving = $state(false);
  let formError = $state('');
  let loginBusy = $state(false);
  let loginError = $state('');
  let referenceData = $state({});
  let sessionChecked = $state(false);
  let profileMenuOpen = $state(false);
  let notificationsOpen = $state(false);
  let apiConnected = $state(true);

  const dataByCode = $state({});

  let permissionMap = $derived(new Map(permissionRows.map((item) => [item.modulo_codigo, { ...item }])));
  let allowedModules = $derived(
    permissionRows
      .filter((item) => item.modulo_codigo && item.puede_leer && moduleDefinitions[item.modulo_codigo])
      .map((item) => ({ ...item })),
  );
  let activePermission = $derived(permissionMap.get(activeCode));
  let activeSchema = $derived(moduleDefinitions[activeCode]);
  let canCreate = $derived(Boolean(activePermission?.puede_crear && !activeSchema?.readOnly));
  let canUpdate = $derived(Boolean(activePermission?.puede_actualizar && !activeSchema?.readOnly));
  let canDelete = $derived(Boolean(activePermission?.puede_eliminar && !activeSchema?.readOnly));
  let activeData = $derived(dataByCode[activeCode] || []);

  let refLookups = $derived.by(() => {
    const out = {};
    for (const [key, list] of Object.entries(referenceData)) {
      out[key] = list.map((item) => ({ ...item, _label: referenceLabel(key, item) }));
    }
    return out;
  });

  let notifications = $derived.by(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const horizon = new Date(today);
    horizon.setDate(horizon.getDate() + 30);

    return (dataByCode.PRACTICAS || [])
      .filter((p) => /proceso/i.test(p.estado || '') && p.fecha_fin)
      .map((p) => {
        const end = new Date(`${p.fecha_fin}T12:00:00`);
        const student = (dataByCode.ESTUDIANTES || []).find((e) => e._id === p.estudiante_id);
        const name = student ? `${student.nombres} ${student.apellidos}` : p.cargo;
        const diffDays = Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        return { id: p._id, name, cargo: p.cargo, fecha_fin: p.fecha_fin, diffDays, end };
      })
      .filter((item) => !Number.isNaN(item.end.getTime()) && item.end <= horizon)
      .sort((a, b) => a.end - b.end)
      .slice(0, 5);
  });

  function notify(message, kind = 'success') {
    toast = { message, kind };
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toast = { message: '', kind: 'success' }), 4200);
  }

  function publicRow(row) {
    if (!row || typeof row !== 'object') return row;
    const copy = { ...row };
    for (const key of ['creado', 'actualizado']) delete copy[key];
    return copy;
  }

  function normalizeModule(row) {
    if (Array.isArray(row)) {
      return {
        rol_id: row[0],
        modulo_id: row[1],
        modulo_nombre: row[2],
        modulo_codigo: row[3],
        modulo_ruta: row[4],
        modulo_descripcion: row[5],
        puede_crear: row[6],
        puede_leer: row[7],
        puede_actualizar: row[8],
        puede_eliminar: row[9],
        estado: row[10],
      };
    }
    return row || {};
  }

  function normalizeRole(row) {
    if (Array.isArray(row)) {
      return {
        rol_id: row[0],
        nombre: row[1],
        descripcion: row[2],
        nivel_jerarquia: row[3],
        estado: row[4],
      };
    }
    return row || {};
  }

  function referenceLabel(key, row) {
    if (key === 'empresas' || key === 'programas') return row.nombre || row.codigo || '';
    if (key === 'personas') return `${[row.nombres, row.apellidos].filter(Boolean).join(' ')} · ${row.documento || ''}`.trim();
    if (key === 'estudiantes' || key === 'tutores_academicos' || key === 'tutores_empresariales') {
      return [row.nombres, row.apellidos].filter(Boolean).join(' ');
    }
    if (key === 'convenios') return row.codigo || '';
    if (key === 'practicas') {
      const student = (referenceData.estudiantes || []).find((item) => item.estudiante_id === row.estudiante_id);
      return `${student ? [student.nombres, student.apellidos].filter(Boolean).join(' ') : 'Práctica'} · ${row.cargo || ''}`.trim();
    }
    return row.nombre_documento || row.nombre || row.cargo || 'Registro';
  }

  async function loadRoles() {
    const result = rows(await api('/roles/'));
    roles = result.map(normalizeRole);
  }

  async function bootstrapSession() {
    pageError = '';
    try {
      const saved = localStorage.getItem('practicas.session');
      const token = localStorage.getItem('practicas.token');
      if (saved && token) {
        const parsed = JSON.parse(saved);
        const current = await api('/auth/me');
        apiConnected = true;
        const role = { rol_id: current.rol_id, nombre: current.rol_nombre };
        session = {
          ...parsed,
          nombreCompleto: `${current.nombres} ${current.apellidos}`,
          nombres: current.nombres,
          apellidos: current.apellidos,
          role,
        };
        await loadPermissions(role);
        if (permissionRows.length) await selectLanding();
      } else {
        localStorage.removeItem('practicas.session');
        localStorage.removeItem('practicas.token');
      }
    } catch (error) {
      localStorage.removeItem('practicas.session');
      localStorage.removeItem('practicas.token');
      session = null;
      if (String(error.message).includes('No se pudo conectar')) apiConnected = false;
      if (!String(error.message).includes('401')) pageError = error.message;
    } finally {
      sessionChecked = true;
    }
  }

  onMount(() => {
    bootstrapSession();
  });

  onDestroy(() => clearTimeout(toastTimer));

  async function login({ nombres, apellidos, password }) {
    loginError = '';
    if (!nombres || !apellidos || !password) return;
    loginBusy = true;
    try {
      const result = await api('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ nombres, apellidos, password }),
      });
      apiConnected = true;
      localStorage.setItem('practicas.token', result.access_token);
      const role = { rol_id: result.rol_id, nombre: result.rol_nombre };
      session = {
        nombres: result.nombres,
        apellidos: result.apellidos,
        nombreCompleto: `${result.nombres} ${result.apellidos}`,
        role,
      };
      localStorage.setItem('practicas.session', JSON.stringify(session));
      await loadPermissions(role);
      if (!permissionRows.length) throw new Error('Este rol no tiene módulos con permiso de lectura.');
      await selectLanding();
      notify(`Bienvenido, ${session.nombreCompleto}.`);
    } catch (error) {
      session = null;
      localStorage.removeItem('practicas.session');
      localStorage.removeItem('practicas.token');
      if (String(error.message).includes('No se pudo conectar')) apiConnected = false;
      loginError = error.message;
    } finally {
      loginBusy = false;
    }
  }

  async function loadPermissions(role) {
    const payload = await api(`/roles/${role.rol_id}/modulos`);
    permissionRows = rows(payload).map(normalizeModule);
  }

  async function selectLanding() {
    const readable = permissionRows.filter((x) => x.puede_leer && moduleDefinitions[x.modulo_codigo]);
    const first =
      readable.find((x) => !['TUTORES_ACADEMICOS', 'TUTORES_EMPRESARIALES', 'SEGURIDAD'].includes(x.modulo_codigo)) ||
      readable[0];
    activeCode = first?.modulo_codigo || 'dashboard';
    await loadDashboardData();
    if (activeCode !== 'dashboard') await loadModule(activeCode);
  }

  async function loadDashboardData() {
    const codes = ['PRACTICAS', 'ESTUDIANTES', 'EMPRESAS', 'CONVENIOS'];
    await Promise.allSettled(
      codes.map(async (code) => {
        const permitted = permissionMap.get(code)?.puede_leer;
        if (!permitted) return;
        const schema = moduleDefinitions[code];
        const result = rows(await api(schema.endpoint));
        apiConnected = true;
        dataByCode[code] = result.map((item) => ({ ...publicRow(item), _id: rowId(item, code) }));
      }),
    );
    await buildReferenceData();
  }

  async function buildReferenceData() {
    const endpoints = {
      programas: '/programas/',
      empresas: '/empresas/',
      estudiantes: '/estudiantes/',
      personas: '/personas/',
      convenios: '/convenios/',
      tutores_academicos: '/tutores-academicos/',
      tutores_empresariales: '/tutores-empresariales/',
      practicas: '/practicas/',
    };
    const aliases = {
      programa: 'programas',
      empresa: 'empresas',
      estudiante: 'estudiantes',
      persona: 'personas',
      convenio: 'convenios',
      tutor_academico: 'tutores_academicos',
      tutor_empresarial: 'tutores_empresariales',
      practica: 'practicas',
    };
    const needed = new Set();
    for (const code of permissionRows.filter((x) => x.puede_leer).map((x) => x.modulo_codigo)) {
      const schema = moduleDefinitions[code];
      for (const ref of Object.keys(schema?.refs || {})) {
        const key = ref.replace(/_id$/, '');
        needed.add(aliases[key] || key);
      }
    }
    await Promise.allSettled(
      [...needed].map(async (ref) => {
        if (!endpoints[ref]) return;
        try {
          const result = rows(await api(endpoints[ref]));
          referenceData[ref] = result.map((item) => ({ ...publicRow(item), _id: referenceId(item, ref) }));
        } catch {
          referenceData[ref] = [];
        }
      }),
    );
  }

  function rowId(row, code) {
    const ids = {
      PROGRAMAS: 'programa_id',
      ESTUDIANTES: 'estudiante_id',
      EMPRESAS: 'empresa_id',
      PERSONAS: 'persona_id',
      TUTORES_ACADEMICOS: 'tutor_academico_id',
      TUTORES_EMPRESARIALES: 'tutor_empresarial_id',
      CONVENIOS: 'convenio_id',
      PRACTICAS: 'practica_id',
      SEGUIMIENTOS: 'seguimiento_id',
      EVALUACIONES: 'evaluacion_id',
      DOCUMENTOS: 'documento_id',
      SEGURIDAD: 'rol_id',
    };
    return row?.[ids[code]];
  }

  function referenceId(row, key) {
    const ids = {
      programas: 'programa_id',
      empresas: 'empresa_id',
      estudiantes: 'estudiante_id',
      personas: 'persona_id',
      convenios: 'convenio_id',
      tutores_academicos: 'tutor_academico_id',
      tutores_empresariales: 'tutor_empresarial_id',
      practicas: 'practica_id',
    };
    return row?.[ids[key]];
  }

  async function selectModule(code) {
    profileMenuOpen = false;
    notificationsOpen = false;
    if (code === 'dashboard') {
      activeCode = 'dashboard';
      await loadDashboardData();
      return;
    }
    const permission = permissionMap.get(code);
    if (!permission?.puede_leer) {
      notify('No tienes permiso para consultar este módulo.', 'error');
      return;
    }
    activeCode = code;
    pageError = '';
    await loadModule(code);
  }

  async function loadModule(code = activeCode) {
    if (code === 'dashboard') return;
    const schema = moduleDefinitions[code];
    if (!schema || !permissionMap.get(code)?.puede_leer) return;
    loading = true;
    pageError = '';
    try {
      const result = rows(await api(schema.endpoint));
      apiConnected = true;
      dataByCode[code] = result.map((item) => ({ ...publicRow(item), _id: rowId(item, code) }));
      await buildReferenceData();
      if (code === 'SEGURIDAD') {
        await loadRoles();
        if (session.role?.nombre === 'Administrador') {
          users = rows(await api('/auth/users'));
        }
      }
    } catch (error) {
      if (String(error.message).includes('No se pudo conectar')) apiConnected = false;
      pageError = error.message;
    } finally {
      loading = false;
    }
  }

  async function focusSearch() {
    notificationsOpen = false;
    profileMenuOpen = false;
    if (activeCode === 'dashboard') {
      const target =
        allowedModules.find((m) => m.modulo_codigo === 'PRACTICAS')?.modulo_codigo ||
        allowedModules[0]?.modulo_codigo;
      if (target) {
        await selectModule(target);
      }
    }
    await tick();
    document.querySelector('.search-field input')?.focus();
  }

  function handleWindowClick(event) {
    if (!event.target?.closest?.('.topbar-right')) {
      profileMenuOpen = false;
      notificationsOpen = false;
    }
  }

  function handleWindowKeydown(event) {
    if (event.key === 'Escape') {
      profileMenuOpen = false;
      notificationsOpen = false;
    }
  }

  function prepareCreate() {
    editing = null;
    formError = '';
    formOpen = true;
  }

  function prepareEdit(record) {
    editing = record;
    formError = '';
    formOpen = true;
  }

  async function saveRecord(payload) {
    saving = true;
    formError = '';
    try {
      if (editing) {
        await api(`${activeSchema.endpoint}${editing._id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        notify(`${capitalize(activeSchema.singular)} actualizado correctamente.`);
      } else {
        await api(activeSchema.endpoint, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        notify(`${capitalize(activeSchema.singular)} creado correctamente.`);
      }
      formOpen = false;
      await Promise.all([loadModule(), loadDashboardData()]);
    } catch (error) {
      formError = error.message;
      notify(error.message, 'error');
    } finally {
      saving = false;
    }
  }

  async function confirmDelete() {
    if (!deleting) return;
    saving = true;
    try {
      await api(`${activeSchema.endpoint}${deleting._id}`, { method: 'DELETE' });
      notify(`${capitalize(activeSchema.singular)} desactivado correctamente. El registro se conserva en el historial.`);
      deleting = null;
      await Promise.all([loadModule(), loadDashboardData()]);
    } catch (error) {
      notify(error.message, 'error');
    } finally {
      saving = false;
    }
  }

  function exportCsv() {
    const cols = activeSchema.columns;
    const csv = [cols.map((c) => c.label), ...activeData.map((row) => cols.map((c) => csvValue(row[c.key], c)))]
      .map((row) => row.map((v) => `"${String(v ?? '').replaceAll('"', '""')}"`).join(';'))
      .join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activeSchema.title.toLowerCase().replaceAll(' ', '-')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    notify('Archivo exportado correctamente.');
  }

  function csvValue(value, col) {
    if (col.type === 'ref') {
      return refLookups[col.ref]?.find((x) => String(x._id) === String(value))?._label || '';
    }
    if (value == null) return '';
    return value;
  }

  function logout() {
    session = null;
    permissionRows = [];
    users = [];
    profileMenuOpen = false;
    notificationsOpen = false;
    localStorage.removeItem('practicas.session');
    localStorage.removeItem('practicas.token');
    activeCode = 'dashboard';
    dataByCode.PRACTICAS = [];
  }

  function capitalize(value) {
    return value?.charAt(0).toUpperCase() + value?.slice(1) || 'Registro';
  }
</script>

<svelte:window onclick={handleWindowClick} onkeydown={handleWindowKeydown} />

{#if !sessionChecked}
  <main class="boot-screen">
    <div class="boot-brand"><BriefcaseBusiness size={22} aria-hidden="true" /></div>
    <span class="loading-spinner" aria-hidden="true"></span>
    <p>Conectando con la plataforma…</p>
    {#if pageError}
      <div class="boot-error">
        <span>{pageError}</span>
        <button type="button" class="button secondary" onclick={bootstrapSession}>Reintentar</button>
      </div>
    {/if}
  </main>
{:else if !session}
  <Login busy={loginBusy} error={loginError} onlogin={login} />
{:else}
  <a href="#main-content" class="skip-link">Ir al contenido principal</a>
  <div class="app-shell">
    <main id="main-content" class="main-area">
      <div class="topbar">
        <div class="topbar-breadcrumb">
          <span class="topbar-mark"><BriefcaseBusiness size={17} aria-hidden="true" /></span>
          <span>Portal académico</span>
          <span class="breadcrumb-slash" aria-hidden="true">/</span>
          <span>{activeCode === 'dashboard' ? 'Resumen' : activeSchema?.title || 'Gestión'}</span>
        </div>

        <div class="topbar-right">
          <div class="api-status" class:offline={!apiConnected}>
            <span aria-hidden="true"></span>
            {apiConnected ? 'API conectada' : 'Sin conexión'}
          </div>

          <button type="button" class="top-icon" aria-label="Buscar en los registros" onclick={focusSearch}>
            <Search size={18} aria-hidden="true" />
          </button>

          <div class="popover-anchor">
            <button
              type="button"
              class="top-icon notification-button"
              class:has-alerts={notifications.length > 0}
              aria-label="Notificaciones y alertas de vencimiento"
              aria-expanded={notificationsOpen}
              onclick={() => {
                notificationsOpen = !notificationsOpen;
                profileMenuOpen = false;
              }}
            >
              <Bell size={18} aria-hidden="true" />
            </button>

            {#if notificationsOpen}
              <div class="topbar-popover notifications-menu" role="region" aria-label="Alertas próximas">
                <div class="popover-header">
                  <strong>Recordatorios de prácticas</strong>
                  <span>{notifications.length}</span>
                </div>
                {#if notifications.length}
                  <div class="notification-list">
                    {#each notifications as item (item.id)}
                      <button
                        type="button"
                        class="notification-item"
                        onclick={() => selectModule('PRACTICAS')}
                      >
                        <CalendarClock size={16} aria-hidden="true" />
                        <div>
                          <strong>{item.name}</strong>
                          <small>
                            {item.diffDays < 0
                              ? `Venció hace ${Math.abs(item.diffDays)} días`
                              : item.diffDays === 0
                                ? 'Finaliza hoy'
                                : `Finaliza en ${item.diffDays} días`}
                            · {item.fecha_fin}
                          </small>
                        </div>
                        <ArrowRight size={14} aria-hidden="true" />
                      </button>
                    {/each}
                  </div>
                {:else}
                  <p class="popover-empty">No hay prácticas próximas a vencer en los siguientes 30 días.</p>
                {/if}
              </div>
            {/if}
          </div>

          <span class="top-divider" aria-hidden="true"></span>

          <div class="profile-menu-wrap">
            <button
              type="button"
              class="top-user profile-trigger"
              aria-expanded={profileMenuOpen}
              onclick={() => {
                profileMenuOpen = !profileMenuOpen;
                notificationsOpen = false;
              }}
            >
              <span class="top-user-avatar" aria-hidden="true">{session.nombres?.charAt(0) || 'U'}</span>
              <span class="top-user-copy">
                <strong>{session.nombreCompleto || session.nombres}</strong>
                <small>{session.role?.nombre}</small>
              </span>
            </button>
            {#if profileMenuOpen}
              <div class="profile-menu">
                {#if permissionMap.get('SEGURIDAD')?.puede_leer}
                  <button
                    type="button"
                    onclick={() => {
                      profileMenuOpen = false;
                      selectModule('SEGURIDAD');
                    }}
                  >
                    <ShieldAlert size={15} aria-hidden="true" />
                    Seguridad y roles
                  </button>
                {/if}
                <button
                  type="button"
                  onclick={() => {
                    profileMenuOpen = false;
                    logout();
                  }}
                >
                  <X size={15} aria-hidden="true" />
                  Cerrar sesión
                </button>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <section class="page-content">
        {#if activeCode === 'dashboard'}
          <PageHeader
            title="Resumen general"
            subtitle="Monitorea los procesos de prácticas profesionales en un solo lugar."
          />
          <ModuleTabs modules={allowedModules} active={activeCode} onnavigate={selectModule} />
          <Dashboard
            modules={allowedModules}
            data={dataByCode}
            role={session.nombreCompleto || session.nombres}
            onnavigate={selectModule}
          />
        {:else if activeSchema}
          <PageHeader
            title={activeSchema.title}
            subtitle={activeSchema.subtitle}
            canCreate={canCreate}
            oncreate={prepareCreate}
            showExport={Boolean(activeData.length)}
            onexport={exportCsv}
          />
          <ModuleTabs modules={allowedModules} active={activeCode} onnavigate={selectModule} />
          <div class="module-summary">
            <span class="summary-dot" aria-hidden="true"></span>
            <span>{activeData.length} {activeData.length === 1 ? 'registro' : 'registros'} en este módulo</span>
            <span class="summary-separator" aria-hidden="true">·</span>
            <span>{session.role?.nombre}</span>
            <span class="summary-role-icon" aria-hidden="true"><CheckCircle2 size={14} /></span>
          </div>

          {#if pageError}
            <div class="notice error-notice" role="alert">
              <AlertCircle size={18} aria-hidden="true" />
              <div>
                <strong>No se pudo cargar la información</strong>
                <span>{pageError}</span>
              </div>
              <button type="button" class="button secondary" onclick={() => loadModule()}>
                <RefreshCw size={15} aria-hidden="true" />
                Reintentar
              </button>
            </div>
          {:else}
            <section class="panel records-panel">
              <div class="records-heading">
                <div>
                  <div class="records-title-row">
                    <h2>Todos los {activeSchema.title.toLowerCase()}</h2>
                    <span class="count-pill">{activeData.length}</span>
                  </div>
                  <p>Consulta y administra la información registrada en la plataforma.</p>
                </div>
                <button
                  type="button"
                  class="icon-button refresh-button"
                  class:rotating={refreshing || loading}
                  onclick={() => loadModule()}
                  aria-label="Actualizar registros"
                >
                  <RefreshCw size={17} aria-hidden="true" />
                </button>
              </div>
              {#if !loading}
                <DataTable
                  columns={activeSchema.columns}
                  data={activeData}
                  lookups={refLookups}
                  caption={`Tabla de ${activeSchema.title.toLowerCase()}`}
                  canUpdate={canUpdate}
                  canDelete={canDelete}
                  onedit={prepareEdit}
                  ondelete={(record) => (deleting = record)}
                />
              {:else}
                <div class="table-empty">
                  <span class="loading-spinner" aria-hidden="true"></span>
                  <span>Actualizando registros…</span>
                </div>
              {/if}
            </section>
          {/if}

          {#if activeCode === 'SEGURIDAD'}
            <div class="security-note">
              <ShieldAlert size={17} aria-hidden="true" />
              <span>
                Los permisos se aplican en el servidor desde <strong>roles_modulos</strong>. Cada cuenta utiliza el rol
                que el administrador le asignó.
              </span>
            </div>
            {#if session.role?.nombre === 'Administrador'}
              <UserManager {roles} {users} onupdated={(value) => (users = value)} onnotify={notify} />
            {/if}
          {/if}
        {/if}
      </section>

      <footer class="app-footer">
        <span>Prácticas profesionales <i>·</i> Portal institucional</span>
        <span>
          Datos sincronizados con la API
          <span class="footer-status" class:offline={!apiConnected} aria-hidden="true"></span>
        </span>
      </footer>
    </main>
  </div>

  {#if toast.message}
    <Toast
      message={toast.message}
      kind={toast.kind}
      onclose={() => (toast = { message: '', kind: 'success' })}
    />
  {/if}

  {#if formOpen && activeSchema}
    <Modal
      title={editing ? `Editar ${activeSchema.singular}` : `Nuevo ${activeSchema.singular}`}
      subtitle={editing
        ? 'Actualiza la información del registro.'
        : 'Completa la información para registrar un nuevo elemento.'}
      onclose={() => (formOpen = false)}
    >
      <RecordForm
        schema={activeSchema}
        record={editing}
        lookups={refLookups}
        saving={saving}
        onsubmit={saveRecord}
        oncancel={() => (formOpen = false)}
      />
      {#if formError}
        <div class="form-error" role="alert">
          <AlertCircle size={16} aria-hidden="true" />
          <span>{formError}</span>
        </div>
      {/if}
    </Modal>
  {/if}

  {#if deleting}
    <Modal
      title={`Desactivar ${activeSchema.singular}`}
      subtitle="El registro conservará su historial y dejará de aparecer en los listados activos."
      onclose={() => (deleting = null)}
    >
      <div class="delete-confirm">
        <div class="delete-mark"><AlertCircle size={22} aria-hidden="true" /></div>
        <p>¿Quieres cambiar este registro al estado inactivo?</p>
        <div class="delete-actions">
          <!-- svelte-ignore a11y_autofocus -->
          <button type="button" class="button secondary" autofocus onclick={() => (deleting = null)}>
            Cancelar
          </button>
          <button type="button" class="button delete-button" disabled={saving} onclick={confirmDelete}>
            {saving ? 'Guardando…' : 'Sí, desactivar'}
          </button>
        </div>
      </div>
    </Modal>
  {/if}
{/if}
