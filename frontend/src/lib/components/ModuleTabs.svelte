<script>
  import {
    LayoutDashboard,
    Building2,
    UsersRound,
    BriefcaseBusiness,
    BarChart3,
    FileSpreadsheet,
  } from 'lucide-svelte';

  let { modules = [], active = '', onnavigate = () => {} } = $props();

  const groups = [
    { key: 'institution', label: 'Institución', icon: Building2, codes: ['PROGRAMAS', 'EMPRESAS', 'CONVENIOS'] },
    { key: 'people', label: 'Personas', icon: UsersRound, codes: ['PERSONAS', 'TUTORES_ACADEMICOS', 'TUTORES_EMPRESARIALES', 'ESTUDIANTES'] },
    { key: 'practice', label: 'Prácticas', icon: BriefcaseBusiness, codes: ['PRACTICAS', 'SEGUIMIENTOS', 'EVALUACIONES', 'DOCUMENTOS'] }
  ];

  const labels = {
    PROGRAMAS: 'Programas', EMPRESAS: 'Empresas', CONVENIOS: 'Convenios',
    ESTUDIANTES: 'Estudiantes', PERSONAS: 'Directorio',
    TUTORES_ACADEMICOS: 'Tutoría académica', TUTORES_EMPRESARIALES: 'Tutoría empresarial',
    PRACTICAS: 'Prácticas', SEGUIMIENTOS: 'Seguimientos', EVALUACIONES: 'Evaluaciones', DOCUMENTOS: 'Documentos'
  };

  let readable = $derived(modules.filter((module) => module.modulo_codigo !== 'SEGURIDAD'));
  let readableCodes = $derived(new Set(readable.map((module) => module.modulo_codigo)));
  let activeGroup = $derived(groups.find((group) => group.codes.includes(active)) || null);
  let groupModules = $derived(activeGroup ? activeGroup.codes.map((code) => readable.find((module) => module.modulo_codigo === code)).filter(Boolean) : []);

  function openGroup(group) {
    const available = readable.filter((module) => group.codes.includes(module.modulo_codigo));
    const preferred = group.key === 'people' ? 'PERSONAS' : group.codes[0];
    const destination = available.find((module) => module.modulo_codigo === preferred) || available[0];
    if (destination) onnavigate(destination.modulo_codigo);
  }
</script>

<div class="module-navigation">
  <nav class="module-tabs" aria-label="Secciones principales">
    <button type="button" class:active={active === 'dashboard'} onclick={() => onnavigate('dashboard')}>
      <LayoutDashboard size={15} aria-hidden="true" /><span>Inicio</span>
    </button>
    {#each groups as group (group.key)}
      {@const Icon = group.icon}
      {#if group.codes.some((code) => readableCodes.has(code))}
        <button type="button" class:active={activeGroup?.key === group.key} onclick={() => openGroup(group)}>
          <Icon size={15} aria-hidden="true" /><span>{group.label}</span>
        </button>
      {/if}
    {/each}
    <button type="button" class:active={active === 'tablero'} onclick={() => onnavigate('tablero')}>
      <BarChart3 size={15} aria-hidden="true" /><span>Tablero</span>
    </button>
    <button type="button" class:active={active === 'reportes'} onclick={() => onnavigate('reportes')}>
      <FileSpreadsheet size={15} aria-hidden="true" /><span>Reportes</span>
    </button>
  </nav>

  {#if activeGroup && groupModules.length > 1}
    <nav class="module-subtabs" aria-label={`Módulos de ${activeGroup.label}`}>
      {#each groupModules as module (module.modulo_codigo)}
        <button type="button" class:active={active === module.modulo_codigo} onclick={() => onnavigate(module.modulo_codigo)}>
          {labels[module.modulo_codigo] || module.modulo_nombre}
        </button>
      {/each}
    </nav>
  {/if}
</div>
