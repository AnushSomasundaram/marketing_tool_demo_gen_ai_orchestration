import { ref } from 'vue'
import { defineStore } from 'pinia'

import { sendCampaignMessage } from '@/services/chatService'
import type { ChatMessage, ChatScope } from '@/types/chat'
import { useCampaignStore } from './campaignStore'
import { useUiStore } from './uiStore'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const scope = ref<ChatScope>('campaign')
  const isSending = ref(false)
  const isAssistantTyping = ref(false)

  function setScope(next: ChatScope) {
    scope.value = next
  }

  function addUserMessage(content: string): ChatMessage {
    const message: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    messages.value.push(message)
    return message
  }

  async function sendMessage(content: string) {
    const trimmed = content.trim()
    if (!trimmed || isSending.value) return

    const campaignStore = useCampaignStore()
    const uiStore = useUiStore()

    addUserMessage(trimmed)
    isSending.value = true
    isAssistantTyping.value = true

    try {
      const assistantMessage = await sendCampaignMessage({
        campaignId: campaignStore.campaign?.id ?? '',
        message: trimmed,
        scope: scope.value,
        selectedAssetId: scope.value === 'campaign' ? undefined : campaignStore.selectedAssetId ?? undefined,
      })
      messages.value.push(assistantMessage)

      if (campaignStore.campaign) {
        await campaignStore.refreshCampaign()
      }
    } catch (error) {
      uiStore.pushToast(error instanceof Error ? error.message : 'Failed to send message', 'error')
    } finally {
      isSending.value = false
      isAssistantTyping.value = false
    }
  }

  function reset() {
    messages.value = []
    scope.value = 'campaign'
    isSending.value = false
    isAssistantTyping.value = false
  }

  return {
    messages,
    scope,
    isSending,
    isAssistantTyping,
    setScope,
    sendMessage,
    reset,
  }
})
