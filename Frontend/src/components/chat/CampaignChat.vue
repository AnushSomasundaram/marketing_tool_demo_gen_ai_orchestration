<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { MessageSquare } from '@lucide/vue'
import { useChatStore } from '@/stores/chatStore'
import { SUGGESTED_PROMPTS } from '@/types/chat'
import ChatMessageItem from './ChatMessage.vue'
import ChatComposer from './ChatComposer.vue'
import ChatScopeSelector from './ChatScopeSelector.vue'
import TypingIndicator from './TypingIndicator.vue'

const chatStore = useChatStore()
const scrollRef = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)
watch(() => chatStore.isAssistantTyping, scrollToBottom)

function sendPrompt(prompt: string) {
  chatStore.sendMessage(prompt)
}
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div ref="scrollRef" class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-3">
      <div v-if="chatStore.messages.length === 0" class="flex flex-1 flex-col items-center justify-center gap-4 py-6 text-center">
        <div class="flex size-10 items-center justify-center rounded-full bg-[var(--color-accent-soft)]">
          <MessageSquare class="size-5 text-[var(--color-ink-muted)]" />
        </div>
        <div>
          <p class="text-sm font-medium text-[var(--color-ink)]">Talk to your campaign assistant</p>
          <p class="mt-0.5 text-xs text-[var(--color-ink-faint)]">Try one of these to get started</p>
        </div>
        <div class="flex w-full flex-col gap-1.5">
          <button
            v-for="prompt in SUGGESTED_PROMPTS"
            :key="prompt"
            type="button"
            class="rounded-lg border border-[var(--color-border-subtle)] bg-white px-3 py-2 text-left text-xs text-[var(--color-ink-muted)] transition-colors hover:border-[var(--color-border-strong)] hover:text-[var(--color-ink)]"
            @click="sendPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </div>

      <ChatMessageItem v-for="message in chatStore.messages" :key="message.id" :message="message" />
      <TypingIndicator v-if="chatStore.isAssistantTyping" />
    </div>

    <div class="flex flex-col gap-2 border-t border-[var(--color-border-subtle)] p-3">
      <ChatScopeSelector v-model="chatStore.scope" />
      <ChatComposer :disabled="chatStore.isSending" @send="chatStore.sendMessage" />
    </div>
  </div>
</template>
