<script setup lang="ts">
import { useId } from 'vue'
import { ChevronDown } from '@lucide/vue'

export interface AppSelectOption {
  value: string
  label: string
}

withDefaults(
  defineProps<{
    modelValue: string
    options: AppSelectOption[]
    label?: string
    disabled?: boolean
  }>(),
  { disabled: false },
)

defineEmits<{ 'update:modelValue': [value: string] }>()

const selectId = useId()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="selectId" class="text-xs font-medium text-[var(--color-ink-muted)]">
      {{ label }}
    </label>
    <div class="relative">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        class="h-9 w-full appearance-none rounded-lg border border-[var(--color-border-subtle)] bg-white px-3 pr-8 text-sm text-[var(--color-ink)] transition-colors focus:border-[var(--color-ink)] disabled:bg-[var(--color-accent-soft)]"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <ChevronDown class="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
    </div>
  </div>
</template>
