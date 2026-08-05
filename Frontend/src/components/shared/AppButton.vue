<script setup lang="ts">
import { Loader2 } from '@lucide/vue'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    loading?: boolean
    disabled?: boolean
    type?: 'button' | 'submit'
    fullWidth?: boolean
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    loading: false,
    disabled: false,
    type: 'button',
    fullWidth: false,
  },
)

const variantClasses: Record<Variant, string> = {
  primary: 'bg-[var(--color-accent)] text-white hover:bg-black focus-visible:outline-black disabled:bg-ink-faint',
  secondary:
    'bg-[var(--color-accent-soft)] text-[var(--color-ink)] hover:bg-[var(--color-border-strong)]/60 border border-[var(--color-border-subtle)]',
  ghost: 'bg-transparent text-[var(--color-ink-muted)] hover:bg-[var(--color-accent-soft)]',
  danger: 'bg-red-600 text-white hover:bg-red-700',
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-8 px-2.5 text-xs gap-1.5',
  md: 'h-9 px-3.5 text-sm gap-2',
  lg: 'h-11 px-5 text-sm gap-2',
}
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60"
    :class="[variantClasses[variant], sizeClasses[size], fullWidth ? 'w-full' : '']"
  >
    <Loader2 v-if="loading" class="size-4 animate-spin" />
    <slot v-else name="icon" />
    <slot />
  </button>
</template>
