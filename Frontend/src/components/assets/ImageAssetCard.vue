<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, Sparkles } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import type { CampaignAsset } from '@/types/campaign'
import AssetToolbar from './AssetToolbar.vue'
import LoadingSpinner from '@/components/shared/LoadingSpinner.vue'

const props = defineProps<{ asset: CampaignAsset; selected: boolean }>()
const campaignStore = useCampaignStore()

const emit = defineEmits<{
  select: []
  preview: []
  regenerate: []
  download: []
  delete: []
  refine: []
}>()

const isBusy = computed(() => props.asset.status === 'processing' || props.asset.status === 'queued')
</script>

<template>
  <div
    role="button"
    tabindex="0"
    class="group relative flex flex-col overflow-hidden rounded-xl border bg-white transition-shadow"
    :class="selected ? 'border-[var(--color-ink)] shadow-[var(--shadow-float)]' : 'border-[var(--color-border-subtle)] hover:shadow-[var(--shadow-panel)]'"
    @click="emit('select')"
    @keydown.enter="emit('select')"
  >
    <div class="relative aspect-square w-full overflow-hidden bg-[var(--color-accent-soft)]">
      <img :src="asset.previewUrl ?? undefined" :alt="asset.title" class="h-full w-full object-cover" :class="isBusy ? 'opacity-40' : ''" />

      <div v-if="isBusy" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/50">
        <LoadingSpinner />
        <span v-if="asset.progress" class="text-xs font-medium text-[var(--color-ink-muted)]">{{ asset.progress }}%</span>
      </div>

      <div v-else-if="asset.status === 'failed'" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/80 px-3 text-center">
        <AlertTriangle class="size-5 text-red-500" />
        <p class="text-xs text-[var(--color-ink-muted)]">{{ asset.errorMessage ?? 'Generation failed' }}</p>
        <button
          type="button"
          class="rounded-lg bg-[var(--color-ink)] px-2.5 py-1 text-xs font-medium text-white"
          @click.stop="emit('regenerate')"
        >
          Retry
        </button>
      </div>

      <div class="absolute left-2 top-2 flex gap-1.5">
        <span class="rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">{{ asset.aspectRatio }}</span>
        <span class="rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">v{{ asset.version }}</span>
      </div>

      <div class="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        <AssetToolbar
          :regenerating="campaignStore.assetIsRegenerating(asset.id)"
          :downloading="campaignStore.assetIsDownloading(asset.id)"
          @preview="emit('preview')"
          @edit="emit('select')"
          @regenerate="emit('regenerate')"
          @download="emit('download')"
          @delete="emit('delete')"
        />
      </div>
    </div>

    <div class="flex items-center justify-between gap-2 p-2.5">
      <p class="truncate text-xs font-medium text-[var(--color-ink)]">{{ asset.title }}</p>
      <button
        type="button"
        class="flex shrink-0 items-center gap-1 rounded-md bg-[var(--color-accent-soft)] px-2 py-1 text-[11px] font-medium text-[var(--color-ink)] hover:bg-[var(--color-border-strong)]/60"
        @click.stop="emit('refine')"
      >
        <Sparkles class="size-3" /> Refine with AI
      </button>
    </div>
  </div>
</template>
