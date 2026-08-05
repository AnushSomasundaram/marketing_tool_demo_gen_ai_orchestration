<script setup lang="ts">
import { ref } from 'vue'
import { Hash, X } from '@lucide/vue'

const props = defineProps<{ modelValue: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()

const draft = ref('')

function normalize(tag: string): string {
  const trimmed = tag.trim().replace(/^#/, '')
  return trimmed ? `#${trimmed.replace(/\s+/g, '')}` : ''
}

function addTag() {
  const tag = normalize(draft.value)
  if (tag && !props.modelValue.includes(tag)) {
    emit('update:modelValue', [...props.modelValue, tag])
  }
  draft.value = ''
}

function removeTag(tag: string) {
  emit(
    'update:modelValue',
    props.modelValue.filter((t) => t !== tag),
  )
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ',') {
    event.preventDefault()
    addTag()
  } else if (event.key === 'Backspace' && !draft.value && props.modelValue.length > 0) {
    const lastTag = props.modelValue[props.modelValue.length - 1]
    if (lastTag) removeTag(lastTag)
  }
}
</script>

<template>
  <div>
    <p class="mb-1.5 flex items-center gap-1 text-xs font-medium text-[var(--color-ink-muted)]">
      <Hash class="size-3" /> Hashtags
    </p>
    <div class="flex flex-wrap items-center gap-1.5 rounded-lg border border-[var(--color-border-subtle)] bg-white p-2 focus-within:border-[var(--color-ink)]">
      <span
        v-for="tag in modelValue"
        :key="tag"
        class="flex items-center gap-1 rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-xs text-[var(--color-ink)]"
      >
        {{ tag }}
        <button type="button" :aria-label="`Remove ${tag}`" class="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]" @click="removeTag(tag)">
          <X class="size-3" />
        </button>
      </span>
      <input
        v-model="draft"
        type="text"
        placeholder="Add hashtag…"
        aria-label="Add hashtag"
        class="min-w-[100px] flex-1 border-0 bg-transparent text-xs text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] focus:outline-none"
        @keydown="handleKeydown"
        @blur="addTag"
      />
    </div>
  </div>
</template>
