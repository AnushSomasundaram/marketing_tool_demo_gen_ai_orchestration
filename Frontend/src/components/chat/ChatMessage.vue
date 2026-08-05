<script setup lang="ts">
import { Sparkles } from '@lucide/vue'
import type { ChatMessage } from '@/types/chat'

defineProps<{ message: ChatMessage }>()

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}
</script>

<template>
  <div class="flex gap-2" :class="message.role === 'user' ? 'flex-row-reverse' : 'flex-row'">
    <div
      v-if="message.role === 'assistant'"
      class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-ink)] text-white"
    >
      <Sparkles class="size-3.5" />
    </div>
    <div class="flex max-w-[80%] flex-col gap-1" :class="message.role === 'user' ? 'items-end' : 'items-start'">
      <div
        class="rounded-2xl px-3.5 py-2 text-sm leading-relaxed whitespace-pre-wrap"
        :class="
          message.role === 'user'
            ? 'bg-[var(--color-ink)] text-white rounded-tr-sm'
            : 'bg-[var(--color-accent-soft)] text-[var(--color-ink)] rounded-tl-sm'
        "
      >
        {{ message.content }}
      </div>
      <span class="px-1 text-[10px] text-[var(--color-ink-faint)]">{{ formatTime(message.createdAt) }}</span>
    </div>
  </div>
</template>
