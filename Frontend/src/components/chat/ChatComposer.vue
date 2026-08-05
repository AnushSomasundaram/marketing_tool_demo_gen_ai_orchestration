<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { Send } from '@lucide/vue'

const props = defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ send: [content: string] }>()

const draft = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function resize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 140)}px`
}

function handleSend() {
  const content = draft.value.trim()
  if (!content || props.disabled) return
  emit('send', content)
  draft.value = ''
  nextTick(resize)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="flex items-end gap-2 rounded-xl border border-[var(--color-border-subtle)] bg-white p-2 focus-within:border-[var(--color-ink)]">
    <textarea
      ref="textareaRef"
      v-model="draft"
      rows="1"
      :disabled="disabled"
      placeholder="Ask the assistant to refine your campaign…"
      aria-label="Message the campaign assistant"
      class="max-h-[140px] min-h-9 flex-1 resize-none border-0 bg-transparent px-1.5 py-1.5 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] focus:outline-none disabled:text-[var(--color-ink-faint)]"
      @keydown="handleKeydown"
      @input="resize"
    />
    <button
      type="button"
      :disabled="disabled || !draft.trim()"
      aria-label="Send message"
      class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-ink)] text-white transition-opacity disabled:opacity-30"
      @click="handleSend"
    >
      <Send class="size-4" />
    </button>
  </div>
</template>
