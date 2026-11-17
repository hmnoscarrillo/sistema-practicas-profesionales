<script>
  import { SearchX } from 'lucide-svelte';
  let { title = 'No hay información', description = 'Cuando existan registros, aparecerán aquí.' } = $props();
</script>
<div class="empty-state"><span class="empty-icon"><SearchX size={22}/></span><strong>{title}</strong><p>{description}</p></div>
