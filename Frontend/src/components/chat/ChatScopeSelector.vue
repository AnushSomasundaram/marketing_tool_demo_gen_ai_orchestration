<script setup lang="ts">
import { CHAT_SCOPE_OPTIONS, type ChatScope } from '@/types/chat'

defineProps<{ modelValue: ChatScope }>()
defineEmits<{ 'update:modelValue': [value: ChatScope] }>()
</script>

<template>
  <div class="flex items-center gap-1 overflow-x-auto pb-0.5" role="radiogroup" aria-label="Refinement scope">
    <button
      v-for="option in CHAT_SCOPE_OPTIONS"
      :key="option.value"
      type="button"
      role="radio"
      :aria-checked="modelValue === option.value"
      :title="option.description"
      class="shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium whitespace-nowrap transition-colors"
      :class="
        modelValue === option.value
          ? 'border-[var(--color-ink)] bg-[var(--color-ink)] text-white'
          : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-ink-muted)] hover:border-[var(--color-border-strong)]'
      "
      @click="$emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>
