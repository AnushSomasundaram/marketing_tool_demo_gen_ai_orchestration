<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    label?: string
    placeholder?: string
    type?: string
    error?: string
    hint?: string
    required?: boolean
    disabled?: boolean
  }>(),
  {
    type: 'text',
    required: false,
    disabled: false,
  },
)

defineEmits<{ 'update:modelValue': [value: string] }>()

const inputId = useId()
const describedBy = computed(() => (props.error ? `${inputId}-error` : props.hint ? `${inputId}-hint` : undefined))
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-xs font-medium text-[var(--color-ink-muted)]">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :aria-invalid="Boolean(error)"
      :aria-describedby="describedBy"
      class="h-9 rounded-lg border border-[var(--color-border-subtle)] bg-white px-3 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] transition-colors focus:border-[var(--color-ink)] disabled:bg-[var(--color-accent-soft)] disabled:text-[var(--color-ink-faint)]"
      :class="error ? 'border-red-400 focus:border-red-500' : ''"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" :id="`${inputId}-error`" class="text-xs text-red-600">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="text-xs text-[var(--color-ink-faint)]">{{ hint }}</p>
  </div>
</template>
