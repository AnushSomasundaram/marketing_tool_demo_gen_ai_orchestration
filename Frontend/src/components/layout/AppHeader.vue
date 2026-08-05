<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Sparkles } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import { useChatStore } from '@/stores/chatStore'
import { useUiStore } from '@/stores/uiStore'
import AppButton from '@/components/shared/AppButton.vue'

const campaignStore = useCampaignStore()
const chatStore = useChatStore()
const uiStore = useUiStore()

const status = computed(() => {
  const campaignStatus = campaignStore.campaign?.status
  if (!campaignStatus) return { label: 'Ready', dot: 'bg-[var(--color-ink-faint)]' }
  if (campaignStatus === 'planning' || campaignStatus === 'generating') {
    return { label: 'Generating…', dot: 'bg-amber-500 animate-pulse' }
  }
  if (campaignStatus === 'publishing') return { label: 'Publishing…', dot: 'bg-amber-500 animate-pulse' }
  if (campaignStatus === 'published') return { label: 'Published', dot: 'bg-blue-500' }
  if (campaignStatus === 'failed' || campaignStatus === 'partially_failed') {
    return { label: 'Needs attention', dot: 'bg-red-500' }
  }
  return { label: 'Campaign ready', dot: 'bg-emerald-500' }
})

function handleNewCampaign() {
  if (!campaignStore.campaign) {
    campaignStore.resetCampaign()
    chatStore.reset()
    return
  }

  uiStore.openConfirmDialog({
    title: 'Start a new campaign?',
    message: 'Your current campaign, assets, and chat history will be cleared.',
    confirmLabel: 'Start new',
    danger: true,
    onConfirm: () => {
      campaignStore.resetCampaign()
      chatStore.reset()
      uiStore.setMobileTab('create')
    },
  })
}
</script>

<template>
  <header class="flex h-14 shrink-0 items-center justify-between border-b border-[var(--color-border-subtle)] bg-white px-4">
    <div class="flex items-center gap-2.5">
      <div class="flex size-7 items-center justify-center rounded-lg bg-[var(--color-ink)] text-white">
        <Sparkles class="size-4" />
      </div>
      <span class="text-sm font-semibold text-[var(--color-ink)]">Campaign Studio</span>
    </div>

    <div class="flex items-center gap-3">
      <div class="hidden items-center gap-1.5 sm:flex">
        <span class="size-1.5 rounded-full" :class="status.dot" />
        <span class="text-xs text-[var(--color-ink-muted)]">{{ status.label }}</span>
      </div>
      <AppButton variant="secondary" size="sm" @click="handleNewCampaign">
        <template #icon><Plus class="size-3.5" /></template>
        New campaign
      </AppButton>
    </div>
  </header>
</template>
