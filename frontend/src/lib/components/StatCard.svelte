<script>
  import { ArrowUpRight } from 'lucide-svelte';

  let { label, value, hint, icon: Icon, accent = 'blue' } = $props();
</script>

<article class="stat-card glass-card accent-{accent}">
  <span class="stat-glow" aria-hidden="true"></span>
  <div class="stat-top">
    <span class="stat-icon {accent}"><Icon size={20} aria-hidden="true" /></span>
    <span class="stat-hint">{hint}<ArrowUpRight size={13} aria-hidden="true" /></span>
  </div>
  <div class="stat-value">{value}</div>
  <div class="stat-label">{label}</div>
  <span class="stat-accent-bar" aria-hidden="true"></span>
</article>
