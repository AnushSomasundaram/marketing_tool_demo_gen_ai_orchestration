<script setup lang="ts">
import { Loader2 } from '@lucide/vue'

withDefaults(defineProps<{ size?: 'sm' | 'md' | 'lg'; label?: string }>(), { size: 'md' })

const sizeClasses = { sm: 'size-4', md: 'size-5', lg: 'size-8' }
</script>

<template>
  <div class="inline-flex items-center gap-2 text-[var(--color-ink-muted)]" role="status">
    <Loader2 :class="sizeClasses[size]" class="animate-spin" />
    <span v-if="label" class="text-sm">{{ label }}</span>
    <span v-else class="sr-only">Loading</span>
  </div>
</template>
