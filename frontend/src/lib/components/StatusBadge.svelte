<script>
  let { value = '' } = $props();
  const tone = $derived(/activo|vigente|aprobado|completado|finalizada/i.test(value) ? 'positive' : /pendiente|proceso|revisi/i.test(value) ? 'warning' : /inactivo|rechazado|suspendido|vencido/i.test(value) ? 'negative' : 'neutral');
</script>
<span class="badge {tone}"><i></i>{value || '—'}</span>
