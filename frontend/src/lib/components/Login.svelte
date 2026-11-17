<script>
  import { BriefcaseBusiness, ArrowRight, CircleAlert, LockKeyhole, UserRound, ShieldCheck, Eye, EyeOff } from 'lucide-svelte';
  import { attachValidationSync } from '../validation.js';

  let { busy = false, error = '', onlogin = () => {} } = $props();

  let formEl = $state();
  let nombres = $state('');
  let apellidos = $state('');
  let password = $state('');
  let showPassword = $state(false);

  $effect(() => {
    if (formEl) {
      return attachValidationSync(formEl);
    }
  });

  function submit(e) {
    e.preventDefault();
    onlogin({ nombres: nombres.trim(), apellidos: apellidos.trim(), password });
  }
</script>

<main class="login-page">
  <section class="login-visual">
    <div class="login-visual-top">
      <div class="brand-mark"><BriefcaseBusiness size={20} aria-hidden="true" /></div>
      <strong>Prácticas<span> · Gestión profesional</span></strong>
    </div>
    <div class="login-visual-copy">
      <div class="eyebrow"><span></span> PLATAFORMA ACADÉMICA</div>
      <h1>El siguiente paso<br />en tu <em>futuro profesional.</em></h1>
      <p>Una plataforma para acompañar, conectar y hacer seguimiento a las prácticas profesionales.</p>
      <div class="visual-stat-row">
        <div class="visual-stat">
          <strong>360°</strong>
          <span>Acompañamiento</span>
        </div>
        <div class="visual-divider"></div>
        <div class="visual-stat">
          <strong>Un solo lugar</strong>
          <span>para cada proceso</span>
        </div>
      </div>
    </div>
    <div class="login-visual-footer">
      <span>Portal universitario de prácticas</span>
      <span>© 2026</span>
    </div>
  </section>

  <section class="login-form-side">
    <div class="login-card">
      <div class="login-mobile-brand">
        <span class="brand-mark"><BriefcaseBusiness size={18} aria-hidden="true" /></span>
        Prácticas
      </div>
      <div class="login-welcome">
        <div class="login-icon"><LockKeyhole size={19} aria-hidden="true" /></div>
        <div class="eyebrow">BIENVENIDO DE NUEVO</div>
        <h2>Ingresa a tu espacio</h2>
        <p>Ingresa tu nombre, apellido y contraseña registrados.</p>
      </div>

      <form bind:this={formEl} onsubmit={submit}>
        <div class="form-field required-field login-input">
          <label for="login-nombres">Nombre</label>
          <div class="input-wrap">
            <UserRound size={17} aria-hidden="true" />
            <input
              id="login-nombres"
              type="text"
              bind:value={nombres}
              autocomplete="given-name"
              placeholder="Tu nombre"
              data-error="login-nombres-error"
              required
            />
          </div>
          <div id="login-nombres-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Ingresa tu nombre registrado.</span>
          </div>
        </div>

        <div class="form-field required-field login-input">
          <label for="login-apellidos">Apellido</label>
          <div class="input-wrap">
            <UserRound size={17} aria-hidden="true" />
            <input
              id="login-apellidos"
              type="text"
              bind:value={apellidos}
              autocomplete="family-name"
              placeholder="Tu apellido"
              data-error="login-apellidos-error"
              required
            />
          </div>
          <div id="login-apellidos-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Ingresa tu apellido registrado.</span>
          </div>
        </div>

        <div class="form-field required-field login-input">
          <label for="login-password">Contraseña</label>
          <div class="input-wrap">
            <LockKeyhole size={17} aria-hidden="true" />
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              bind:value={password}
              autocomplete="current-password"
              placeholder="Ingresa tu contraseña"
              data-error="login-password-error"
              required
            />
            <button
              type="button"
              class="password-toggle"
              aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              aria-pressed={showPassword}
              onclick={() => (showPassword = !showPassword)}
            >
              {#if showPassword}
                <EyeOff size={16} aria-hidden="true" />
              {:else}
                <Eye size={16} aria-hidden="true" />
              {/if}
            </button>
          </div>
          <div id="login-password-error" class="error-msg">
            <CircleAlert size={14} aria-hidden="true" />
            <span class="error-text">Ingresa tu contraseña.</span>
          </div>
        </div>

        {#if error}
          <div class="login-error" role="alert">
            <CircleAlert size={16} aria-hidden="true" />
            <span>{error}</span>
          </div>
        {/if}

        <button type="submit" class="button primary login-submit" disabled={busy}>
          {busy ? 'Conectando…' : 'Continuar'}
          {#if !busy}<ArrowRight size={17} aria-hidden="true" />{/if}
        </button>
      </form>

      <div class="login-note">
        <ShieldCheck size={16} aria-hidden="true" />
        <span>Tu rol y tus permisos se obtienen de la cuenta registrada.</span>
      </div>
      <div class="auth-limitation">
        El administrador de prácticas debe crear tu cuenta y asignar tu rol antes del primer ingreso.
      </div>
    </div>
    <div class="login-footer">¿Problemas de acceso? Comunícate con soporte académico.</div>
  </section>
</main>
