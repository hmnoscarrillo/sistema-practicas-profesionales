<script module>
  let formSeq = 0;
</script>

<script>
  import { Save, LoaderCircle, CircleAlert } from 'lucide-svelte';
  import { attachValidationSync } from '../validation.js';

  let {
    schema,
    record = null,
    lookups = {},
    saving = false,
    onsubmit = () => {},
    oncancel = () => {},
    allowedFields = null,
  } = $props();

  const formUid = `record-form-${++formSeq}`;
  const optionalFields = new Set(['telefono', 'direccion', 'ruta_archivo', 'comentarios']);

  let formEl = $state();
  let values = $state({});
  let dateError = $state('');

  $effect(() => {
    const next = {};
    for (const field of schema.fields) {
      if (allowedFields && !allowedFields.has(field.key)) continue;
      next[field.key] = record?.[field.key] ?? (field.type === 'select' ? field.options?.[0] ?? '' : '');
    }
    values = next;
    dateError = '';
  });

  $effect(() => {
    if (formEl) {
      return attachValidationSync(formEl);
    }
  });

  function validateDateRange() {
    if (!formEl) return true;
    const endInput = formEl.querySelector('[name="fecha_fin"]');
    if (!endInput) {
      dateError = '';
      return true;
    }
    if (values.fecha_inicio && values.fecha_fin && values.fecha_fin < values.fecha_inicio) {
      const msg = 'La fecha de finalización no puede ser anterior a la fecha de inicio.';
      endInput.setCustomValidity(msg);
      dateError = msg;
      return false;
    }
    endInput.setCustomValidity('');
    dateError = '';
    return true;
  }

  function handleFieldInput(fieldKey) {
    if (fieldKey === 'nota_academica' || fieldKey === 'nota_empresarial') {
      const a = Number(values.nota_academica);
      const b = Number(values.nota_empresarial);
      if (
        values.nota_academica !== '' &&
        values.nota_empresarial !== '' &&
        !Number.isNaN(a) &&
        !Number.isNaN(b)
      ) {
        values.nota_final = String(Math.round(((a + b) / 2) * 10) / 10);
      }
    }
    if (fieldKey === 'fecha_inicio' || fieldKey === 'fecha_fin') {
      validateDateRange();
    }
  }

  function minValueFor(field) {
    if (field.type !== 'number') return undefined;
    if (field.key.includes('nota')) return '0';
    if (field.key === 'semestre' || field.key === 'duracion_semestres') return '1';
    return '0';
  }

  function maxValueFor(field) {
    if (field.type !== 'number') return undefined;
    if (field.key.includes('nota')) return '5';
    if (field.key === 'semestre' || field.key === 'duracion_semestres') return '20';
    return undefined;
  }

  function stepValueFor(field) {
    if (field.type !== 'number') return undefined;
    return field.key.includes('nota') ? '0.1' : '1';
  }

  function submit(e) {
    e.preventDefault();
    if (!validateDateRange()) {
      formEl?.reportValidity();
      return;
    }
    const body = { ...values };
    for (const field of schema.fields) {
      if (field.type === 'number' && body[field.key] !== '' && body[field.key] != null) {
        body[field.key] = Number(body[field.key]);
      }
      if (field.type === 'ref' && body[field.key] !== '' && body[field.key] != null) {
        body[field.key] = Number(body[field.key]);
      }
      if (body[field.key] === '') delete body[field.key];
    }
    onsubmit(body);
  }
</script>

<form bind:this={formEl} class="record-form" onsubmit={submit}>
  <div class="form-grid">
    {#each schema.fields as field (field.key)}
      {#if !allowedFields || allowedFields.has(field.key)}
        {@const isRequired = !optionalFields.has(field.key)}
        {@const inputId = `${formUid}-${field.key}`}
        {@const errorId = `${inputId}-error`}
        <div class="form-field" class:required-field={isRequired} class:full-width={field.type === 'textarea'}>
          <label for={inputId}>{field.label}</label>
          {#if field.type === 'select'}
            <select
              id={inputId}
              name={field.key}
              bind:value={values[field.key]}
              data-error={errorId}
              required={isRequired}
            >
              <option value="" disabled>Selecciona una opción</option>
              {#each field.options as option (option)}
                <option value={option}>{option}</option>
              {/each}
            </select>
          {:else if field.type === 'ref'}
            <select
              id={inputId}
              name={field.key}
              bind:value={values[field.key]}
              data-error={errorId}
              required={isRequired}
            >
              <option value="" disabled>Selecciona {field.label.toLowerCase()}</option>
              {#each lookups[field.options] || [] as item (item._id)}
                <option value={String(item._id)}>{item._label}</option>
              {/each}
            </select>
          {:else if field.type === 'textarea'}
            <textarea
              id={inputId}
              name={field.key}
              bind:value={values[field.key]}
              data-error={errorId}
              rows="3"
              placeholder="Escribe la información relevante…"
              required={isRequired}
            ></textarea>
          {:else}
            <input
              id={inputId}
              name={field.key}
              type={field.type}
              bind:value={values[field.key]}
              oninput={() => handleFieldInput(field.key)}
              min={minValueFor(field)}
              max={maxValueFor(field)}
              step={stepValueFor(field)}
              data-error={errorId}
              placeholder={field.type === 'number' ? '0' : field.type === 'url' ? 'https://…' : `Ingresa ${field.label.toLowerCase()}`}
              required={isRequired}
            />
          {/if}
          <div id={errorId} class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Completa este campo correctamente.</span>
          </div>
        </div>
      {/if}
    {/each}
  </div>

  {#if dateError}
    <div class="form-error inline-date-error" role="alert">
      <CircleAlert size={16} aria-hidden="true" />
      <span>{dateError}</span>
    </div>
  {/if}

  <div class="form-footer">
    <span class="form-note">Los campos con asterisco son obligatorios</span>
    <div class="form-actions">
      <button type="button" class="button secondary" onclick={oncancel}>Cancelar</button>
      <button type="submit" class="button primary" disabled={saving}>
        {#if saving}
          <LoaderCircle size={16} class="spin" aria-hidden="true" />
          Guardando…
        {:else}
          <Save size={16} aria-hidden="true" />
          {record ? 'Guardar cambios' : 'Crear registro'}
        {/if}
      </button>
    </div>
  </div>
</form>
