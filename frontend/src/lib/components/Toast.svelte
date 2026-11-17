<script>
  import { Check, CircleAlert, X } from 'lucide-svelte';
  let { message = '', kind = 'success', onclose = () => {} } = $props();
</script>
{#if message}<div class="toast {kind}" role="status">{#if kind === 'error'}<CircleAlert size={18}/>{:else}<Check size={18}/>{/if}<span>{message}</span><button class="icon-button" onclick={onclose} aria-label="Cerrar"><X size={16}/></button></div>{/if}
