<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    label?: string
    placeholder?: string
    rows?: number
    error?: string
    hint?: string
    required?: boolean
    disabled?: boolean
    maxlength?: number
  }>(),
  {
    rows: 4,
    required: false,
    disabled: false,
  },
)

defineEmits<{ 'update:modelValue': [value: string] }>()

const textareaId = useId()
const describedBy = computed(() => (props.error ? `${textareaId}-error` : props.hint ? `${textareaId}-hint` : undefined))
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="textareaId" class="text-xs font-medium text-[var(--color-ink-muted)]">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <textarea
      :id="textareaId"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
      :required="required"
      :maxlength="maxlength"
      :aria-invalid="Boolean(error)"
      :aria-describedby="describedBy"
      class="resize-none rounded-lg border border-[var(--color-border-subtle)] bg-white px-3 py-2 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] transition-colors focus:border-[var(--color-ink)] disabled:bg-[var(--color-accent-soft)] disabled:text-[var(--color-ink-faint)]"
      :class="error ? 'border-red-400 focus:border-red-500' : ''"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <p v-if="error" :id="`${textareaId}-error`" class="text-xs text-red-600">{{ error }}</p>
    <p v-else-if="hint" :id="`${textareaId}-hint`" class="text-xs text-[var(--color-ink-faint)]">{{ hint }}</p>
  </div>
</template>
