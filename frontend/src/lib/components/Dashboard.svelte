<script>
  import {
    Activity,
    BriefcaseBusiness,
    Building2,
    GraduationCap,
    ArrowRight,
    Sparkles,
    Clock3,
    CircleCheck,
    CalendarDays,
    FileCheck2,
    BookOpen,
    UsersRound,
    ClipboardList,
    ChartNoAxesColumn,
    FileText,
    UserCheck,
  } from 'lucide-svelte';
  import StatCard from './StatCard.svelte';
  import StatusBadge from './StatusBadge.svelte';

  let { modules = [], data = {}, role = '', onnavigate = () => {} } = $props();

  const activePractices = $derived(
    (data.PRACTICAS || []).filter((x) => /proceso/i.test(x.estado || '')),
  );
  const finishedPractices = $derived(
    (data.PRACTICAS || []).filter((x) => /finalizada|completad/i.test(x.estado || '')),
  );
  const activeAgreements = $derived(
    (data.CONVENIOS || []).filter((x) => /vigente/i.test(x.estado || '')),
  );
  const activeCompanies = $derived(
    (data.EMPRESAS || []).filter((x) => /activ/i.test(x.estado || '')),
  );

  const statusSegments = $derived([
    {
      key: 'proceso',
      label: 'En proceso',
      count: activePractices.length,
      tone: 'blue',
      icon: BriefcaseBusiness,
    },
    {
      key: 'finalizadas',
      label: 'Finalizadas',
      count: finishedPractices.length,
      tone: 'green',
      icon: CircleCheck,
    },
    {
      key: 'convenios',
      label: 'Convenios vigentes',
      count: activeAgreements.length,
      tone: 'violet',
      icon: FileCheck2,
    },
    {
      key: 'empresas',
      label: 'Empresas activas',
      count: activeCompanies.length,
      tone: 'amber',
      icon: Building2,
    },
  ]);

  const totalDistribution = $derived(
    statusSegments.reduce((sum, item) => sum + item.count, 0),
  );

  const upcoming = $derived(
    (data.PRACTICAS || [])
      .filter((x) => x.fecha_fin && new Date(x.fecha_fin) >= new Date())
      .sort((a, b) => String(a.fecha_fin).localeCompare(String(b.fecha_fin)))
      .slice(0, 4),
  );

  const sampleUpcoming = (() => {
    const today = new Date();
    today.setHours(12, 0, 0, 0);
    return [
      { days: 3, title: 'Entrega del informe de avance', context: 'Seguimiento académico' },
      { days: 8, title: 'Reunión de seguimiento', context: 'Tutoría con la empresa' },
      { days: 15, title: 'Evaluación de desempeño', context: 'Revisión de mitad de período' },
      { days: 24, title: 'Presentación del informe final', context: 'Cierre de práctica' },
    ].map((event, index) => {
      const date = new Date(today);
      date.setDate(date.getDate() + event.days);
      return {
        _id: `agenda-demo-${index}`,
        cargo: event.title,
        contexto: event.context,
        fecha_fin: date.toISOString().slice(0, 10),
        demo: true,
      };
    });
  })();

  const agendaItems = $derived(upcoming.length ? upcoming : sampleUpcoming);
  const quickModules = $derived(
    modules
      .filter(
        (module) =>
          !['TUTORES_ACADEMICOS', 'TUTORES_EMPRESARIALES', 'SEGURIDAD'].includes(
            module.modulo_codigo || module.codigo,
          ),
      )
      .slice(0, 4),
  );

  const accents = ['blue', 'violet', 'amber', 'green'];
  const moduleIcons = {
    PROGRAMAS: BookOpen,
    ESTUDIANTES: GraduationCap,
    EMPRESAS: Building2,
    PERSONAS: UsersRound,
    TUTORES_ACADEMICOS: UserCheck,
    TUTORES_EMPRESARIALES: BriefcaseBusiness,
    CONVENIOS: FileCheck2,
    PRACTICAS: BriefcaseBusiness,
    SEGUIMIENTOS: ClipboardList,
    EVALUACIONES: ChartNoAxesColumn,
    DOCUMENTOS: FileText,
  };

  function label(key, row) {
    const m = {
      ESTUDIANTES: ['nombres', 'apellidos'],
      EMPRESAS: ['nombre'],
      PROGRAMAS: ['nombre'],
      PRACTICAS: ['cargo'],
      SEGUIMIENTOS: ['tipo'],
    };
    if (key === 'PRACTICAS') {
      const st = (data.ESTUDIANTES || []).find((v) => v._id === row.estudiante_id);
      return st ? `${st.nombres} ${st.apellidos}` : row.cargo;
    }
    return (m[key] || ['nombre'])
      .map((f) => row[f])
      .filter(Boolean)
      .join(' ');
  }
</script>

<div class="dashboard-content">
  <section class="welcome-banner" aria-label="Resumen de bienvenida">
    <span class="liquid-orb orb-a" aria-hidden="true"></span>
    <span class="liquid-orb orb-b" aria-hidden="true"></span>
    <span class="liquid-orb orb-c" aria-hidden="true"></span>

    <div class="welcome-copy">
      <span class="welcome-label"><Sparkles size={14} aria-hidden="true" /> VISTA GENERAL</span>
      <h2>Hola, {role || 'bienvenido'}</h2>
      <p>Monitorea en tiempo real el avance académico, convenios y prácticas activas.</p>

      <div class="hero-pills">
        <span class="hero-pill">
          <BriefcaseBusiness size={14} aria-hidden="true" />
          <strong>{activePractices.length}</strong> en curso
        </span>
        <span class="hero-pill">
          <FileCheck2 size={14} aria-hidden="true" />
          <strong>{activeAgreements.length}</strong> convenios vigentes
        </span>
        <span class="hero-pill">
          <Building2 size={14} aria-hidden="true" />
          <strong>{activeCompanies.length}</strong> empresas activas
        </span>
      </div>
    </div>

    <div class="welcome-ornament" aria-hidden="true">
      <div class="ornament-orbit orbit-one"></div>
      <div class="ornament-orbit orbit-two"></div>
      <span><BriefcaseBusiness size={28} /></span>
    </div>
  </section>

  <div class="stats-grid">
    <StatCard
      label="Prácticas en curso"
      value={activePractices.length}
      hint="Seguimiento activo"
      icon={BriefcaseBusiness}
      accent="blue"
    />
    <StatCard
      label="Estudiantes"
      value={(data.ESTUDIANTES || []).length}
      hint="En la plataforma"
      icon={GraduationCap}
      accent="violet"
    />
    <StatCard
      label="Empresas aliadas"
      value={(data.EMPRESAS || []).length}
      hint="Organizaciones"
      icon={Building2}
      accent="amber"
    />
    <StatCard
      label="Módulos disponibles"
      value={modules.filter((module) => module.modulo_codigo !== 'SEGURIDAD').length}
      hint="Según tu rol"
      icon={Activity}
      accent="green"
    />
  </div>

  <section class="panel glass-panel status-strip" aria-label="Panorama del ecosistema de prácticas">
    <div class="status-strip-head">
      <div>
        <span class="panel-kicker">PANORAMA GENERAL</span>
        <h3>Distribución de prácticas y convenios</h3>
      </div>
      <span class="distribution-total">
        {totalDistribution} {totalDistribution === 1 ? 'indicador activo' : 'indicadores activos'}
      </span>
    </div>

    <div class="distribution-bar" role="presentation">
      {#if totalDistribution > 0}
        {#each statusSegments as segment (segment.key)}
          {#if segment.count > 0}
            <span
              class="distribution-segment tone-{segment.tone}"
              style={`width: ${(segment.count / totalDistribution) * 100}%`}
            ></span>
          {/if}
        {/each}
      {:else}
        <span class="distribution-segment empty"></span>
      {/if}
    </div>

    <div class="distribution-legend">
      {#each statusSegments as segment (segment.key)}
        {@const SegIcon = segment.icon}
        <div class="legend-chip tone-{segment.tone}">
          <span class="legend-icon" aria-hidden="true"><SegIcon size={14} /></span>
          <span class="legend-label">{segment.label}</span>
          <strong>{segment.count}</strong>
        </div>
      {/each}
    </div>
  </section>

  <div class="dashboard-grid">
    <section class="panel glass-panel activity-panel">
      <div class="panel-heading">
        <div>
          <span class="panel-kicker">ACTIVIDAD</span>
          <h3>Prácticas recientes</h3>
          <p>Un vistazo a las últimas asignaciones registradas</p>
        </div>
        <button type="button" class="text-button" onclick={() => onnavigate('PRACTICAS')}>
          Ver todas <ArrowRight size={15} aria-hidden="true" />
        </button>
      </div>

      {#if (data.PRACTICAS || []).length}
        <div class="activity-list">
          {#each [...(data.PRACTICAS || [])].slice(-5).reverse() as item, index (item._id)}
            {@const student = (data.ESTUDIANTES || []).find((x) => x._id === item.estudiante_id)}
            {@const company = (data.EMPRESAS || []).find((x) => x._id === item.empresa_id)}
            {@const tone = accents[index % accents.length]}
            <button type="button" class="activity-row" onclick={() => onnavigate('PRACTICAS')}>
              <div class="activity-avatar tone-{tone}">{student?.nombres?.charAt(0) || 'P'}</div>
              <div class="activity-main">
                <strong>{student ? `${student.nombres} ${student.apellidos}` : item.cargo}</strong>
                <span>{company?.nombre || 'Organización asignada'} · {item.cargo}</span>
              </div>
              <StatusBadge value={item.estado} />
            </button>
          {/each}
        </div>
      {:else}
        <div class="dash-empty">
          <CircleCheck size={19} aria-hidden="true" />
          <span>Los registros aparecerán aquí cuando la API esté disponible.</span>
        </div>
      {/if}
    </section>

    <section class="panel glass-panel deadlines-panel">
      <div class="panel-heading">
        <div>
          <span class="panel-kicker">{upcoming.length ? 'AGENDA' : 'AGENDA DE EJEMPLO'}</span>
          <h3>Fechas próximas</h3>
          <p>{upcoming.length ? 'Finalización de prácticas' : 'Fechas de referencia para organizar el seguimiento'}</p>
        </div>
        <span class="calendar-icon" aria-hidden="true"><CalendarDays size={18} /></span>
      </div>

      <div class="deadline-list">
        {#each agendaItems as item, index (item._id)}
          {@const company = (data.EMPRESAS || []).find((x) => x._id === item.empresa_id)}
          {@const tone = accents[index % accents.length]}
          <div class:demo-deadline={item.demo} class="deadline-row">
            <span class="deadline-symbol tone-{tone}" aria-hidden="true">
              {#if item.demo}
                <CalendarDays size={15} />
              {:else}
                <Clock3 size={16} />
              {/if}
            </span>
            <div class="deadline-main">
              <strong>{item.demo ? item.cargo : label('PRACTICAS', item)}</strong>
              <span>{item.demo ? item.contexto : company?.nombre || item.cargo}</span>
            </div>
            {#if item.demo}
              <span class="demo-deadline-label">Ejemplo</span>
            {/if}
            <span class="deadline-date">
              {new Date(`${item.fecha_fin}T12:00:00`).toLocaleDateString('es-CO', {
                day: '2-digit',
                month: 'short',
              })}
            </span>
          </div>
        {/each}
      </div>
    </section>
  </div>

  <section class="quick-access">
    <div class="quick-heading">
      <span class="panel-kicker">ACCESO RÁPIDO</span>
      <h3>Continúa con tu trabajo</h3>
    </div>

    <div class="quick-grid">
      {#each quickModules as module, i (module.modulo_codigo || module.codigo)}
        {@const name = module.modulo_nombre || module.nombre}
        {@const code = module.modulo_codigo || module.codigo}
        {@const accent = accents[i % accents.length]}
        {@const ModIcon = moduleIcons[code] || BriefcaseBusiness}
        <button type="button" class="quick-card glass-card accent-{accent}" onclick={() => onnavigate(code)}>
          <div class="quick-card-top">
            <span class="quick-icon {accent}" aria-hidden="true"><ModIcon size={17} /></span>
            <span class="quick-number">0{i + 1}</span>
          </div>
          <strong>{name}</strong>
          <span>{module.modulo_descripcion || module.descripcion || 'Gestiona este módulo'}</span>
          <span class="quick-arrow" aria-hidden="true"><ArrowRight size={15} /></span>
        </button>
      {/each}
    </div>
  </section>
</div>
