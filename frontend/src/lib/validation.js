/**
 * Sincroniza la validación diferida tras la interacción (:user-invalid + fallback)
 * con los atributos aria-invalid y aria-describedby para lectores de pantalla.
 */
export function attachValidationSync(form) {
  if (!form) return () => {};

  const supportsUserInvalid = typeof CSS !== 'undefined' && CSS.supports('selector(:user-invalid)');
  const dirtyState = new WeakMap();
  const flagged = new WeakSet();

  const linkError = (el, shown) => {
    const errorId = el.dataset?.error;
    if (!errorId) return;
    const ids = (el.getAttribute('aria-describedby') || '')
      .split(/\s+/)
      .filter((id) => id && id !== errorId);
    if (shown) ids.push(errorId);
    if (ids.length) el.setAttribute('aria-describedby', ids.join(' '));
    else el.removeAttribute('aria-describedby');
  };

  const updateErrorText = (el) => {
    const errorId = el.dataset?.error;
    if (!errorId) return;
    const errorEl = document.getElementById(errorId);
    if (!errorEl) return;
    const textEl = errorEl.querySelector('.error-text');
    if (textEl) {
      textEl.textContent = el.validationMessage || 'Revisa este campo antes de continuar.';
    }
  };

  const syncAria = (el, forcedInvalid = null) => {
    if (!el?.matches?.('input, select, textarea')) return;
    const invalid =
      forcedInvalid !== null
        ? forcedInvalid
        : supportsUserInvalid
          ? el.matches(':user-invalid')
          : el.classList.contains('user-invalid-fallback');

    if (invalid) {
      updateErrorText(el);
      el.setAttribute('aria-invalid', 'true');
      linkError(el, true);
      flagged.add(el);
    } else if (flagged.has(el) || el.getAttribute('aria-invalid') !== 'true') {
      el.setAttribute('aria-invalid', 'false');
      linkError(el, false);
      flagged.delete(el);
    }
  };

  const updateFallback = (el) => {
    const isValid = el.validity.valid;
    el.classList.toggle('user-invalid-fallback', !isValid);
    el.classList.toggle('user-valid-fallback', isValid);
    syncAria(el, !isValid);
  };

  const onBlur = (e) => {
    const el = e.target;
    if (!el?.matches?.('input, select, textarea')) return;
    if (supportsUserInvalid) {
      syncAria(el);
      return;
    }
    const state = dirtyState.get(el) || { hasInteracted: false, hasBlurred: false };
    state.hasBlurred = true;
    dirtyState.set(el, state);
    if (state.hasInteracted) updateFallback(el);
  };

  const onInput = (e) => {
    const el = e.target;
    if (!el?.matches?.('input, select, textarea')) return;
    if (supportsUserInvalid) {
      if (el.getAttribute('aria-invalid') === 'true' || el.matches(':user-invalid')) {
        syncAria(el);
      }
      return;
    }
    const state = dirtyState.get(el) || { hasInteracted: false, hasBlurred: false };
    state.hasInteracted = true;
    dirtyState.set(el, state);
    if (state.hasBlurred) updateFallback(el);
  };

  const onChange = (e) => {
    const el = e.target;
    if (!el?.matches?.('input, select, textarea')) return;
    if (supportsUserInvalid) {
      syncAria(el);
      return;
    }
    const state = dirtyState.get(el) || { hasInteracted: false, hasBlurred: false };
    state.hasInteracted = true;
    state.hasBlurred = true;
    dirtyState.set(el, state);
    updateFallback(el);
  };

  const onInvalid = (e) => {
    const el = e.target;
    if (!el?.matches?.('input, select, textarea')) return;
    if (!supportsUserInvalid) {
      dirtyState.set(el, { hasInteracted: true, hasBlurred: true });
      updateFallback(el);
    } else {
      syncAria(el, true);
    }
  };

  const onReset = () => {
    setTimeout(() => {
      for (const el of form.querySelectorAll('input, select, textarea')) {
        dirtyState.delete(el);
        el.classList.remove('user-invalid-fallback', 'user-valid-fallback');
        flagged.delete(el);
        syncAria(el, false);
      }
    });
  };

  for (const el of form.querySelectorAll('input, select, textarea')) {
    syncAria(el, false);
  }

  form.addEventListener('blur', onBlur, true);
  form.addEventListener('input', onInput);
  form.addEventListener('change', onChange, true);
  form.addEventListener('invalid', onInvalid, true);
  form.addEventListener('reset', onReset, true);

  return () => {
    form.removeEventListener('blur', onBlur, true);
    form.removeEventListener('input', onInput);
    form.removeEventListener('change', onChange, true);
    form.removeEventListener('invalid', onInvalid, true);
    form.removeEventListener('reset', onReset, true);
  };
}
