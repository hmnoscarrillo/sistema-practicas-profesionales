<script>
  import { untrack } from 'svelte';
  import { ArrowUpRight } from 'lucide-svelte';
  import { animateCount } from '../motion.js';

  let { label, value, hint, icon: Icon, accent = 'blue' } = $props();

  let displayValue = $state(0);

  $effect(() => {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return;
    const start = untrack(() => displayValue);
    return animateCount({
      from: start,
      to: numeric,
      duration: 660,
      decimals: 0,
      onUpdate: (val) => {
        displayValue = val;
      },
    });
  });
</script>

<article class="stat-card glass-card accent-{accent}">
  <span class="stat-glow" aria-hidden="true"></span>
  <div class="stat-top">
    <span class="stat-icon {accent}"><Icon size={20} aria-hidden="true" /></span>
    <span class="stat-hint">{hint}<ArrowUpRight size={13} aria-hidden="true" /></span>
  </div>
  <div class="stat-value">{Number.isNaN(Number(value)) ? value : displayValue}</div>
  <div class="stat-label">{label}</div>
  <span class="stat-accent-bar" aria-hidden="true"></span>
</article>
