<script module>
  let modalSeq = 0;
</script>

<script>
  import { onMount } from 'svelte';
  import { X } from 'lucide-svelte';

  let { title, subtitle = '', onclose = () => {}, children } = $props();

  const titleId = `modal-title-${++modalSeq}`;
  let dialogEl = $state();
  let unmounting = false;

  function handleClose() {
    if (dialogEl) dialogEl.returnValue = '';
    if (!unmounting) onclose();
  }

  onMount(() => {
    if (!dialogEl) return;
    if (!dialogEl.open) dialogEl.showModal();

    let cleanupBackdrop = () => {};
    if (!('closedBy' in HTMLDialogElement.prototype)) {
      const onBackdropClick = (event) => {
        if (event.target !== dialogEl) return;
        const rect = dialogEl.getBoundingClientRect();
        const isDialogContent =
          rect.top <= event.clientY &&
          event.clientY <= rect.top + rect.height &&
          rect.left <= event.clientX &&
          event.clientX <= rect.left + rect.width;
        if (isDialogContent) return;
        dialogEl.close();
      };
      dialogEl.addEventListener('click', onBackdropClick);
      cleanupBackdrop = () => dialogEl?.removeEventListener('click', onBackdropClick);
    }

    return () => {
      unmounting = true;
      cleanupBackdrop();
      if (dialogEl?.open) dialogEl.close();
    };
  });
</script>

<dialog
  bind:this={dialogEl}
  class="modal-dialog"
  closedby="any"
  aria-labelledby={titleId}
  onclose={handleClose}
>
  <div class="modal-panel">
    <header class="modal-header">
      <div>
        <h2 id={titleId}>{title}</h2>
        {#if subtitle}<p>{subtitle}</p>{/if}
      </div>
      <button
        type="button"
        class="icon-button"
        onclick={() => dialogEl?.close()}
        aria-label="Cerrar ventana"
      >
        <X size={19} aria-hidden="true" />
      </button>
    </header>
    {@render children()}
  </div>
</dialog>
