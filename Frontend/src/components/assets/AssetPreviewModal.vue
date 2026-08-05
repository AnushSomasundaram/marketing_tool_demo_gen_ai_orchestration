<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Download, RefreshCw, X } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import { useUiStore } from '@/stores/uiStore'
import AppButton from '@/components/shared/AppButton.vue'

const campaignStore = useCampaignStore()
const uiStore = useUiStore()

const asset = computed(() => {
  if (!uiStore.previewAssetId || !campaignStore.campaign) return null
  return campaignStore.campaign.assets.find((a) => a.id === uiStore.previewAssetId) ?? null
})

// Mock mode's downloadUrl for a video asset is just another image, so a
// <video> element can't play it — fall back to the static thumbnail if
// playback actually fails.
const videoUnplayable = ref(false)
watch(() => uiStore.previewAssetId, () => {
  videoUnplayable.value = false
})
const canPlayRealVideo = computed(
  () => asset.value?.type === 'video' && Boolean(asset.value.downloadUrl) && !videoUnplayable.value,
)

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && asset.value) {
    uiStore.closeAssetPreview()
  }
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <Transition name="dialog">
    <div
      v-if="asset"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      :aria-label="`Preview of ${asset.title}`"
      @click.self="uiStore.closeAssetPreview()"
    >
      <div class="flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-[var(--shadow-float)]">
        <div class="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-4 py-3">
          <div>
            <p class="text-sm font-semibold text-[var(--color-ink)]">{{ asset.title }}</p>
            <p class="text-xs text-[var(--color-ink-faint)]">{{ asset.aspectRatio }} · v{{ asset.version }}</p>
          </div>
          <button
            type="button"
            aria-label="Close preview"
            class="flex size-8 items-center justify-center rounded-lg text-[var(--color-ink-muted)] hover:bg-[var(--color-accent-soft)]"
            @click="uiStore.closeAssetPreview()"
          >
            <X class="size-4" />
          </button>
        </div>

        <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-5 sm:flex-row">
          <div class="flex flex-1 items-center justify-center overflow-hidden rounded-xl bg-[var(--color-accent-soft)]">
            <video
              v-if="canPlayRealVideo"
              :key="asset.id"
              :src="asset.downloadUrl ?? undefined"
              :poster="asset.previewUrl ?? undefined"
              class="max-h-[60vh] w-auto object-contain"
              controls
              playsinline
              @error="videoUnplayable = true"
            />
            <img v-else :src="asset.previewUrl ?? undefined" :alt="asset.title" class="max-h-[60vh] w-auto object-contain" />
          </div>
          <div class="w-full shrink-0 sm:w-64">
            <p class="text-xs font-medium text-[var(--color-ink-muted)]">Caption</p>
            <p class="mt-1 whitespace-pre-wrap text-sm text-[var(--color-ink)]">{{ asset.caption }}</p>
            <div class="mt-3 flex flex-wrap gap-1">
              <span
                v-for="tag in asset.hashtags"
                :key="tag"
                class="rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-xs text-[var(--color-ink-muted)]"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 border-t border-[var(--color-border-subtle)] px-4 py-3">
          <AppButton
            variant="secondary"
            size="sm"
            :loading="campaignStore.assetIsRegenerating(asset.id)"
            @click="campaignStore.regenerateAsset(asset.id)"
          >
            <template #icon><RefreshCw class="size-3.5" /></template>
            Regenerate
          </AppButton>
          <AppButton
            variant="primary"
            size="sm"
            :loading="campaignStore.assetIsDownloading(asset.id)"
            @click="campaignStore.downloadAsset(asset.id)"
          >
            <template #icon><Download class="size-3.5" /></template>
            Download
          </AppButton>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}
</style>
