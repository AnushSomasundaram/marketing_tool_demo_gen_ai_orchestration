<script setup lang="ts">
const props = withDefaults(defineProps<{ percent?: number; label?: string; indeterminate?: boolean }>(), {
  percent: 0,
  indeterminate: false,
})

const clamped = () => Math.max(0, Math.min(100, props.percent))
</script>

<template>
  <div class="flex flex-col gap-1">
    <div v-if="label" class="flex items-center justify-between text-xs text-[var(--color-ink-muted)]">
      <span>{{ label }}</span>
      <span v-if="!indeterminate">{{ Math.round(clamped()) }}%</span>
    </div>
    <div class="h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-accent-soft)]" role="progressbar" :aria-valuenow="indeterminate ? undefined : clamped()" aria-valuemin="0" aria-valuemax="100">
      <div
        v-if="indeterminate"
        class="h-full w-1/3 animate-[indeterminate_1.2s_ease-in-out_infinite] rounded-full bg-[var(--color-ink)]"
      />
      <div v-else class="h-full rounded-full bg-[var(--color-ink)] transition-all duration-300" :style="{ width: `${clamped()}%` }" />
    </div>
  </div>
</template>

<style scoped>
@keyframes indeterminate {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(300%);
  }
}
</style>
