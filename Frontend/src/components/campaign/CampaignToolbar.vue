<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Download, MoreHorizontal, RefreshCw, Trash2 } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import { useUiStore } from '@/stores/uiStore'
import AppButton from '@/components/shared/AppButton.vue'

const campaignStore = useCampaignStore()
const uiStore = useUiStore()

const isMenuOpen = ref(false)
const menuRef = ref<HTMLDivElement | null>(null)

const statusLabel = computed(() => {
  switch (campaignStore.campaign?.status) {
    case 'planning':
    case 'generating':
      return 'Generating…'
    case 'publishing':
      return 'Publishing…'
    case 'published':
      return 'Published'
    case 'completed': // mock mode
    case 'ready': // real backend
      return 'Ready to publish'
    case 'partially_failed':
      return 'Some assets failed'
    case 'failed':
      return 'Generation failed'
    default:
      return 'Draft'
  }
})

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    isMenuOpen.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    isMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})

function handleDeleteCampaign() {
  isMenuOpen.value = false
  uiStore.openConfirmDialog({
    title: 'Delete this campaign?',
    message: 'This will permanently remove the campaign, all generated assets, and captions.',
    confirmLabel: 'Delete',
    danger: true,
    onConfirm: () => {
      campaignStore.deleteCampaign()
    },
  })
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-border-subtle)] px-5 py-3.5">
    <div class="min-w-0">
      <h1 class="truncate text-sm font-semibold text-[var(--color-ink)]">
        {{ campaignStore.campaign?.title ?? 'No campaign yet' }}
      </h1>
      <p class="text-xs text-[var(--color-ink-faint)]">{{ statusLabel }}</p>
    </div>

    <div class="flex items-center gap-1.5">
      <AppButton
        variant="secondary"
        size="sm"
        :disabled="!campaignStore.campaign"
        :loading="campaignStore.isRegeneratingCampaign"
        @click="campaignStore.regenerateCampaign"
      >
        <template #icon><RefreshCw class="size-3.5" /></template>
        Regenerate
      </AppButton>
      <AppButton
        variant="secondary"
        size="sm"
        :disabled="!campaignStore.campaign"
        :loading="campaignStore.isDownloadingAll"
        @click="campaignStore.downloadAllAssets"
      >
        <template #icon><Download class="size-3.5" /></template>
        Download all
      </AppButton>
      <div ref="menuRef" class="relative">
        <button
          type="button"
          aria-haspopup="menu"
          :aria-expanded="isMenuOpen"
          aria-label="More actions"
          class="flex size-8 items-center justify-center rounded-lg text-[var(--color-ink-muted)] hover:bg-[var(--color-accent-soft)]"
          @click="isMenuOpen = !isMenuOpen"
        >
          <MoreHorizontal class="size-4" />
        </button>
        <div
          v-if="isMenuOpen"
          role="menu"
          class="absolute right-0 z-20 mt-1 w-44 overflow-hidden rounded-xl border border-[var(--color-border-subtle)] bg-white py-1 shadow-[var(--shadow-float)]"
        >
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
            @click="handleDeleteCampaign"
          >
            <Trash2 class="size-3.5" /> Delete campaign
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
