<script>
  import { UserPlus, RefreshCw, UsersRound, CircleAlert } from 'lucide-svelte';
  import { api, rows } from '../api.js';
  import { attachValidationSync } from '../validation.js';
  import Modal from './Modal.svelte';
  import RecordsDataTable from './DataTable.svelte';

  let { roles = [], users = [], onupdated = () => {}, onnotify = () => {} } = $props();

  let formEl = $state();
  let open = $state(false);
  let saving = $state(false);
  let error = $state('');
  let editing = $state(null);
  let deleting = $state(null);
  let form = $state({ nombres: '', apellidos: '', rol_id: '', password: '' });

  let displayUsers = $derived(users.map((user) => ({ ...user, _id: user.usuario_id })));
  const userColumns = [
    { key: 'nombres', label: 'Nombre' },
    { key: 'apellidos', label: 'Apellido' },
    { key: 'rol_nombre', label: 'Rol asignado' },
    { key: 'estado', label: 'Estado', type: 'status' },
  ];

  $effect(() => {
    if (open && formEl) {
      return attachValidationSync(formEl);
    }
  });

  function reset() {
    form = { nombres: '', apellidos: '', rol_id: '', password: '' };
    editing = null;
    error = '';
  }

  function startCreate() {
    reset();
    open = true;
  }

  function startEdit(user) {
    form = {
      nombres: user.nombres || '',
      apellidos: user.apellidos || '',
      rol_id: String(user.rol_id || ''),
      password: '',
    };
    editing = user;
    error = '';
    open = true;
  }

  async function refresh() {
    try {
      onupdated(rows(await api('/auth/users')));
    } catch (e) {
      onnotify(e.message, 'error');
    }
  }

  async function save(e) {
    e.preventDefault();
    saving = true;
    error = '';
    try {
      const payload = { ...form, rol_id: Number(form.rol_id) };
      if (!payload.password) delete payload.password;
      await api(editing ? `/auth/users/${editing.usuario_id}` : '/auth/users', {
        method: editing ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      });
      open = false;
      await refresh();
      onnotify(editing ? 'Cuenta actualizada correctamente.' : 'Cuenta creada correctamente.', 'success');
      reset();
    } catch (e) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  async function remove() {
    if (!deleting) return;
    saving = true;
    try {
      await api(`/auth/users/${deleting.usuario_id}`, { method: 'DELETE' });
      deleting = null;
      await refresh();
      onnotify('Cuenta desactivada; se conservó su historial.', 'success');
    } catch (e) {
      onnotify(e.message, 'error');
    } finally {
      saving = false;
    }
  }
</script>

<section class="panel user-manager">
  <div class="records-heading">
    <div>
      <div class="records-title-row">
        <h2>Cuentas de acceso</h2>
        <span class="count-pill">{users.length}</span>
      </div>
      <p>Administra nombres, apellidos, roles y acceso de las personas.</p>
    </div>
    <div class="user-manager-actions">
      <button type="button" class="icon-button refresh-button" onclick={refresh} aria-label="Actualizar cuentas">
        <RefreshCw size={16} aria-hidden="true" />
      </button>
      <button type="button" class="button primary" onclick={startCreate}>
        <UserPlus size={15} aria-hidden="true" />
        Crear cuenta
      </button>
    </div>
  </div>

  {#if users.length}
    <RecordsDataTable
      columns={userColumns}
      data={displayUsers}
      caption="Cuentas de acceso registradas"
      canUpdate={true}
      canDelete={true}
      onedit={startEdit}
      ondelete={(user) => (deleting = user)}
    />
  {:else}
    <div class="table-empty">
      <UsersRound size={18} aria-hidden="true" />
      <span>No hay cuentas registradas.</span>
    </div>
  {/if}
</section>

{#if open}
  <Modal
    title={editing ? 'Editar cuenta de acceso' : 'Crear cuenta de acceso'}
    subtitle={editing
      ? 'Actualiza el nombre, apellido, rol o contraseña de la cuenta.'
      : 'Asigna nombre, contraseña y rol a la persona.'}
    onclose={() => {
      open = false;
      reset();
    }}
  >
    <form bind:this={formEl} class="record-form" onsubmit={save}>
      <div class="form-grid">
        <div class="form-field required-field">
          <label for="user-nombres">Nombre</label>
          <input
            id="user-nombres"
            bind:value={form.nombres}
            autocomplete="off"
            data-error="user-nombres-error"
            required
          />
          <div id="user-nombres-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Ingresa el nombre de la cuenta.</span>
          </div>
        </div>

        <div class="form-field required-field">
          <label for="user-apellidos">Apellido</label>
          <input
            id="user-apellidos"
            bind:value={form.apellidos}
            autocomplete="off"
            data-error="user-apellidos-error"
            required
          />
          <div id="user-apellidos-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Ingresa el apellido de la cuenta.</span>
          </div>
        </div>

        <div class="form-field required-field">
          <label for="user-rol">Rol</label>
          <select id="user-rol" bind:value={form.rol_id} data-error="user-rol-error" required>
            <option value="" disabled>Selecciona un rol</option>
            {#each roles as role (role.rol_id)}
              <option value={String(role.rol_id)}>{role.nombre}</option>
            {/each}
          </select>
          <div id="user-rol-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Selecciona un rol activo.</span>
          </div>
        </div>

        <div class="form-field" class:required-field={!editing}>
          <label for="user-password">{editing ? 'Nueva contraseña (opcional)' : 'Contraseña inicial'}</label>
          <input
            id="user-password"
            type="password"
            bind:value={form.password}
            minlength="12"
            autocomplete="new-password"
            placeholder={editing ? 'Déjala vacía para conservarla' : 'Al menos 12 caracteres'}
            data-error="user-password-error"
            required={!editing}
          />
          <div id="user-password-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">La contraseña debe tener al menos 12 caracteres.</span>
          </div>
        </div>
      </div>

      {#if error}
        <div class="form-error" role="alert">
          <CircleAlert size={16} aria-hidden="true" />
          <span>{error}</span>
        </div>
      {/if}

      <div class="form-footer">
        <span class="form-note">El acceso se realiza con nombre, apellido y contraseña.</span>
        <div class="form-actions">
          <button
            type="button"
            class="button secondary"
            onclick={() => {
              open = false;
              reset();
            }}
          >
            Cancelar
          </button>
          <button type="submit" class="button primary" disabled={saving}>
            {saving ? (editing ? 'Guardando…' : 'Creando…') : editing ? 'Guardar cambios' : 'Crear cuenta'}
          </button>
        </div>
      </div>
    </form>
  </Modal>
{/if}

{#if deleting}
  <Modal
    title="Desactivar cuenta"
    subtitle="La persona ya no podrá iniciar sesión; sus datos e historial se conservarán."
    onclose={() => (deleting = null)}
  >
    <div class="delete-confirm">
      <div class="delete-mark"><CircleAlert size={22} aria-hidden="true" /></div>
      <p>¿Desactivar la cuenta de <strong>{deleting.nombres} {deleting.apellidos}</strong>?</p>
      <div class="delete-actions">
        <!-- svelte-ignore a11y_autofocus -->
        <button type="button" class="button secondary" autofocus onclick={() => (deleting = null)}>Cancelar</button>
        <button type="button" class="button delete-button" disabled={saving} onclick={remove}>
          {saving ? 'Guardando…' : 'Desactivar cuenta'}
        </button>
      </div>
    </div>
  </Modal>
{/if}
