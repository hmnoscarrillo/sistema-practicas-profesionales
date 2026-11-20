import { cubicOut } from 'svelte/easing';

export function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

export function flyMotion(options = {}) {
  if (prefersReducedMotion()) {
    return { duration: 0, x: 0, y: 0, opacity: 1 };
  }
  return {
    duration: 240,
    x: 0,
    y: 12,
    opacity: 0,
    easing: cubicOut,
    ...options,
  };
}

export function fadeMotion(options = {}) {
  if (prefersReducedMotion()) {
    return { duration: 0 };
  }
  return {
    duration: 160,
    ...options,
  };
}

export function animateCount({ from = 0, to = 0, duration = 680, decimals = 0, onUpdate }) {
  const startVal = Number(from) || 0;
  const endVal = Number(to) || 0;
  const factor = 10 ** decimals;
  const round = (val) => Math.round(val * factor) / factor;

  if (prefersReducedMotion() || typeof window === 'undefined' || startVal === endVal) {
    onUpdate(round(endVal));
    return () => {};
  }

  let rafId = 0;
  let startTime = 0;

  const step = (now) => {
    if (!startTime) startTime = now;
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / duration);
    const eased = 1 - (1 - progress) ** 3;
    const current = startVal + (endVal - startVal) * eased;
    onUpdate(progress >= 1 ? round(endVal) : round(current));
    if (progress < 1) {
      rafId = window.requestAnimationFrame(step);
    }
  };

  rafId = window.requestAnimationFrame(step);
  return () => {
    if (rafId) window.cancelAnimationFrame(rafId);
  };
}
