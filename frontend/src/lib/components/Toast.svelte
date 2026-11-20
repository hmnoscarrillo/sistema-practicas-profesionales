<script>
  import { fade } from 'svelte/transition';
  import { Check, CircleAlert, X } from 'lucide-svelte';
  import { fadeMotion } from '../motion.js';
  let { message = '', kind = 'success', onclose = () => {} } = $props();
</script>
{#if message}<div class="toast {kind}" role="status" out:fade={fadeMotion({ duration: 140 })}>{#if kind === 'error'}<CircleAlert size={18}/>{:else}<Check size={18}/>{/if}<span>{message}</span><button class="icon-button" onclick={onclose} aria-label="Cerrar"><X size={16}/></button></div>{/if}
