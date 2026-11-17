export const moduleDefinitions = {
  PROGRAMAS: {
    endpoint: '/programas/',
    singular: 'programa',
    title: 'Programas',
    subtitle: 'Oferta académica y planes de formación',
    icon: 'book',
    fields: [
      f('nombre', 'Nombre del programa'),
      f('facultad', 'Facultad'),
      f('nivel', 'Nivel', 'select', ['Profesional', 'Tecnológico', 'Técnico']),
      f('duracion_semestres', 'Duración (semestres)', 'number'),
      f('estado', 'Estado', 'select', ['Activo', 'Inactivo'])
    ],
    columns: [
      c('nombre', 'Programa'),
      c('facultad', 'Facultad'),
      c('nivel', 'Nivel'),
      c('duracion_semestres', 'Semestres'),
      c('estado', 'Estado', 'status')
    ]
  },
  ESTUDIANTES: {
    endpoint: '/estudiantes/',
    singular: 'estudiante',
    title: 'Estudiantes',
    subtitle: 'Personas inscritas en prácticas profesionales',
    icon: 'graduation',
    refs: { programa_id: '/programas/' },
    fields: [
      f('documento', 'Documento'),
      f('nombres', 'Nombres'),
      f('apellidos', 'Apellidos'),
      f('correo', 'Correo electrónico', 'email'),
      f('telefono', 'Teléfono'),
      f('semestre', 'Semestre', 'number'),
      f('programa_id', 'Programa', 'ref', 'programas'),
      f('estado', 'Estado', 'select', ['Activo', 'Inactivo'])
    ],
    columns: [
      c('documento', 'Documento'),
      c('nombres', 'Nombres'),
      c('apellidos', 'Apellidos'),
      c('correo', 'Correo'),
      c('programa_id', 'Programa', 'ref', 'programas'),
      c('semestre', 'Semestre'),
      c('estado', 'Estado', 'status')
    ]
  },
  EMPRESAS: {
    endpoint: '/empresas/',
    singular: 'empresa',
    title: 'Empresas',
    subtitle: 'Organizaciones aliadas para la formación profesional',
    icon: 'building',
    fields: [
      f('nit', 'NIT'),
      f('nombre', 'Razón social'),
      f('sector', 'Sector'),
      f('ciudad', 'Ciudad'),
      f('direccion', 'Dirección'),
      f('telefono', 'Teléfono'),
      f('correo', 'Correo empresarial', 'email'),
      f('estado', 'Estado', 'select', ['Activa', 'Inactiva'])
    ],
    columns: [
      c('nit', 'NIT'),
      c('nombre', 'Empresa'),
      c('sector', 'Sector'),
      c('ciudad', 'Ciudad'),
      c('correo', 'Contacto'),
      c('estado', 'Estado', 'status')
    ]
  },
  PERSONAS: {
    endpoint: '/personas/',
    singular: 'persona',
    title: 'Personas',
    subtitle: 'Directorio compartido para las asignaciones de tutoría',
    icon: 'users',
    fields: [
      f('documento', 'Documento'),
      f('nombres', 'Nombres'),
      f('apellidos', 'Apellidos'),
      f('correo', 'Correo electrónico', 'email'),
      f('telefono', 'Teléfono'),
      f('estado', 'Estado', 'select', ['Activo', 'Inactivo'])
    ],
    columns: [
      c('documento', 'Documento'),
      c('nombres', 'Nombres'),
      c('apellidos', 'Apellidos'),
      c('correo', 'Correo'),
      c('telefono', 'Teléfono'),
      c('estado', 'Estado', 'status'),
      c('origen', 'Origen')
    ]
  },
  TUTORES_ACADEMICOS: {
    endpoint: '/tutores-academicos/',
    singular: 'asignación académica',
    title: 'Tutores académicos',
    subtitle: 'Asigna una persona existente a uno o varios programas',
    icon: 'user-check',
    refs: { persona_id: '/personas/', programa_id: '/programas/' },
    fields: [
      f('persona_id', 'Persona', 'ref', 'personas'),
      f('cargo', 'Cargo académico'),
      f('programa_id', 'Programa', 'ref', 'programas')
    ],
    columns: [
      c('persona_id', 'Persona', 'ref', 'personas'),
      c('programa_id', 'Programa', 'ref', 'programas'),
      c('cargo', 'Cargo'),
      c('estado', 'Estado', 'status'),
      c('origen', 'Origen')
    ]
  },
  TUTORES_EMPRESARIALES: {
    endpoint: '/tutores-empresariales/',
    singular: 'asignación empresarial',
    title: 'Tutores empresariales',
    subtitle: 'Asigna una persona existente a una o varias empresas',
    icon: 'briefcase',
    refs: { persona_id: '/personas/', empresa_id: '/empresas/' },
    fields: [
      f('persona_id', 'Persona', 'ref', 'personas'),
      f('cargo', 'Cargo empresarial'),
      f('empresa_id', 'Empresa', 'ref', 'empresas')
    ],
    columns: [
      c('persona_id', 'Persona', 'ref', 'personas'),
      c('empresa_id', 'Empresa', 'ref', 'empresas'),
      c('cargo', 'Cargo'),
      c('estado', 'Estado', 'status'),
      c('origen', 'Origen')
    ]
  },
  CONVENIOS: {
    endpoint: '/convenios/',
    singular: 'convenio',
    title: 'Convenios',
    subtitle: 'Acuerdos institucionales vigentes',
    icon: 'file-check',
    refs: { empresa_id: '/empresas/', programa_id: '/programas/' },
    fields: [
      f('codigo', 'Código de convenio'),
      f('empresa_id', 'Empresa', 'ref', 'empresas'),
      f('programa_id', 'Programa', 'ref', 'programas'),
      f('fecha_inicio', 'Fecha de inicio', 'date'),
      f('fecha_fin', 'Fecha de finalización', 'date'),
      f('estado', 'Estado', 'select', ['Vigente', 'Vencido', 'En revisión'])
    ],
    columns: [
      c('codigo', 'Código'),
      c('empresa_id', 'Empresa', 'ref', 'empresas'),
      c('programa_id', 'Programa', 'ref', 'programas'),
      c('fecha_inicio', 'Inicio', 'date'),
      c('fecha_fin', 'Finaliza', 'date'),
      c('estado', 'Estado', 'status')
    ]
  },
  PRACTICAS: {
    endpoint: '/practicas/',
    singular: 'práctica',
    title: 'Prácticas profesionales',
    subtitle: 'Asignaciones y avances de formación en el entorno laboral',
    icon: 'briefcase',
    refs: {
      estudiante_id: '/estudiantes/',
      empresa_id: '/empresas/',
      programa_id: '/programas/',
      convenio_id: '/convenios/',
      tutor_academico_id: '/tutores-academicos/',
      tutor_empresarial_id: '/tutores-empresariales/'
    },
    fields: [
      f('estudiante_id', 'Estudiante', 'ref', 'estudiantes'),
      f('empresa_id', 'Empresa', 'ref', 'empresas'),
      f('programa_id', 'Programa', 'ref', 'programas'),
      f('convenio_id', 'Convenio', 'ref', 'convenios'),
      f('tutor_academico_id', 'Tutor académico', 'ref', 'tutores_academicos'),
      f('tutor_empresarial_id', 'Tutor empresarial', 'ref', 'tutores_empresariales'),
      f('cargo', 'Cargo o rol'),
      f('fecha_inicio', 'Fecha de inicio', 'date'),
      f('fecha_fin', 'Fecha de finalización', 'date'),
      f('modalidad', 'Modalidad', 'select', ['Presencial', 'Remota', 'Híbrida']),
      f('estado', 'Estado', 'select', ['En proceso', 'Finalizada', 'Suspendida'])
    ],
    columns: [
      c('estudiante_id', 'Estudiante', 'ref', 'estudiantes'),
      c('empresa_id', 'Empresa', 'ref', 'empresas'),
      c('cargo', 'Cargo'),
      c('fecha_inicio', 'Inicio', 'date'),
      c('fecha_fin', 'Finaliza', 'date'),
      c('modalidad', 'Modalidad'),
      c('estado', 'Estado', 'status')
    ]
  },
  SEGUIMIENTOS: {
    endpoint: '/seguimientos/',
    singular: 'seguimiento',
    title: 'Seguimientos',
    subtitle: 'Bitácora de acompañamiento y visitas',
    icon: 'clipboard',
    refs: { practica_id: '/practicas/', tutor_academico_id: '/tutores-academicos/' },
    fields: [
      f('practica_id', 'Práctica', 'ref', 'practicas'),
      f('tutor_academico_id', 'Tutor académico', 'ref', 'tutores_academicos'),
      f('fecha_seguimiento', 'Fecha del seguimiento', 'date'),
      f('tipo', 'Tipo', 'select', ['Inicial', 'Periódico', 'Visita', 'Cierre']),
      f('observaciones', 'Observaciones', 'textarea'),
      f('estado', 'Estado', 'select', ['Pendiente', 'Completado', 'Reprogramado'])
    ],
    columns: [
      c('practica_id', 'Práctica', 'ref', 'practicas'),
      c('tutor_academico_id', 'Tutor', 'ref', 'tutores_academicos'),
      c('fecha_seguimiento', 'Fecha', 'date'),
      c('tipo', 'Tipo'),
      c('observaciones', 'Observaciones'),
      c('estado', 'Estado', 'status')
    ]
  },
  EVALUACIONES: {
    endpoint: '/evaluaciones/',
    singular: 'evaluación',
    title: 'Evaluaciones',
    subtitle: 'Resultados académicos y de desempeño profesional',
    icon: 'chart',
    refs: { practica_id: '/practicas/' },
    fields: [
      f('practica_id', 'Práctica', 'ref', 'practicas'),
      f('fecha_evaluacion', 'Fecha de evaluación', 'date'),
      f('evaluador', 'Nombre del evaluador'),
      f('nota_academica', 'Nota académica (0–5)', 'number'),
      f('nota_empresarial', 'Nota empresarial (0–5)', 'number'),
      f('nota_final', 'Nota final (0–5)', 'number'),
      f('estado', 'Estado', 'select', ['Activo', 'Inactivo']),
      f('comentarios', 'Comentarios', 'textarea')
    ],
    columns: [
      c('practica_id', 'Práctica', 'ref', 'practicas'),
      c('fecha_evaluacion', 'Fecha', 'date'),
      c('evaluador', 'Evaluador'),
      c('nota_academica', 'Académica'),
      c('nota_empresarial', 'Empresarial'),
      c('nota_final', 'Final', 'rating'),
      c('comentarios', 'Comentarios')
    ]
  },
  DOCUMENTOS: {
    endpoint: '/documentos/',
    singular: 'documento',
    title: 'Documentos',
    subtitle: 'Documentación asociada a las prácticas',
    icon: 'file',
    refs: { practica_id: '/practicas/' },
    fields: [
      f('practica_id', 'Práctica', 'ref', 'practicas'),
      f('nombre_documento', 'Nombre del documento'),
      f('tipo_documento', 'Tipo de documento', 'select', ['Hoja de vida', 'Carta', 'Convenio', 'Informe', 'Evaluación', 'Otro']),
      f('fecha_subida', 'Fecha de radicación', 'date'),
      f('ruta_archivo', 'Enlace al archivo', 'url'),
      f('estado', 'Estado', 'select', ['Pendiente', 'Aprobado', 'Rechazado'])
    ],
    columns: [
      c('nombre_documento', 'Documento'),
      c('tipo_documento', 'Tipo'),
      c('practica_id', 'Práctica', 'ref', 'practicas'),
      c('fecha_subida', 'Radicado', 'date'),
      c('estado', 'Estado', 'status'),
      c('ruta_archivo', 'Archivo', 'link')
    ]
  },
  SEGURIDAD: {
    endpoint: '/roles/',
    singular: 'rol',
    title: 'Seguridad y roles',
    subtitle: 'Roles disponibles y módulos autorizados por la base de datos',
    icon: 'shield',
    readOnly: true,
    columns: [
      c('nombre', 'Rol'),
      c('descripcion', 'Descripción'),
      c('nivel_jerarquia', 'Nivel'),
      c('estado', 'Estado', 'status')
    ]
  }
};

function f(key, label, type = 'text', options = []) {
  return { key, label, type, options };
}

function c(key, label, type = 'text', ref = '') {
  return { key, label, type, ref };
}

export const roleNames = ['Administrador', 'Coordinador', 'Profesor', 'Estudiante'];
export const moduleIcons = {
  PROGRAMAS: 'book',
  ESTUDIANTES: 'graduation',
  EMPRESAS: 'building',
  PERSONAS: 'users',
  TUTORES_ACADEMICOS: 'user-check',
  TUTORES_EMPRESARIALES: 'briefcase',
  CONVENIOS: 'file-check',
  PRACTICAS: 'briefcase',
  SEGUIMIENTOS: 'clipboard',
  EVALUACIONES: 'chart',
  DOCUMENTOS: 'file',
  SEGURIDAD: 'shield'
};
