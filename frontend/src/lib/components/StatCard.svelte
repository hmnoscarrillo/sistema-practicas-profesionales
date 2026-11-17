<script>
  import { ArrowUpRight } from 'lucide-svelte';
  let { label, value, hint, icon: Icon, accent = 'blue' } = $props();
</script>
<article class="stat-card"><div class="stat-top"><span class="stat-icon {accent}"><Icon size={19}/></span><span class="stat-hint">{hint}<ArrowUpRight size={13}/></span></div><div class="stat-value">{value}</div><div class="stat-label">{label}</div></article>
