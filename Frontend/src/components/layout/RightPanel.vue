<script setup lang="ts">
import { computed, ref } from 'vue'
import { Film, Grid2x2, Image as ImageIcon, MessageSquareText } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import CampaignToolbar from '@/components/campaign/CampaignToolbar.vue'
import AssetGrid from '@/components/assets/AssetGrid.vue'
import EmptyAssetsState from '@/components/assets/EmptyAssetsState.vue'
import CaptionEditor from '@/components/captions/CaptionEditor.vue'

type TabKey = 'all' | 'posts' | 'videos' | 'captions'

const campaignStore = useCampaignStore()
const activeTab = ref<TabKey>('all')

const tabs: Array<{ key: TabKey; label: string; icon: typeof Grid2x2 }> = [
  { key: 'all', label: 'All Assets', icon: Grid2x2 },
  { key: 'posts', label: 'Posts', icon: ImageIcon },
  { key: 'videos', label: 'Videos', icon: Film },
  { key: 'captions', label: 'Captions', icon: MessageSquareText },
]

const assets = computed(() => campaignStore.campaign?.assets ?? [])

const filteredAssets = computed(() => {
  if (activeTab.value === 'posts') return assets.value.filter((a) => a.type === 'image')
  if (activeTab.value === 'videos') return assets.value.filter((a) => a.type === 'video')
  return assets.value
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-[var(--color-canvas)]">
    <CampaignToolbar />

    <div class="flex shrink-0 items-center gap-1 border-b border-[var(--color-border-subtle)] bg-white px-5">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-xs font-medium transition-colors"
        :class="
          activeTab === tab.key
            ? 'border-[var(--color-ink)] text-[var(--color-ink)]'
            : 'border-transparent text-[var(--color-ink-faint)] hover:text-[var(--color-ink-muted)]'
        "
        @click="activeTab = tab.key"
      >
        <component :is="tab.icon" class="size-3.5" />
        {{ tab.label }}
      </button>
    </div>

    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div class="min-h-0 flex-[3] overflow-y-auto">
        <template v-if="activeTab === 'captions'">
          <EmptyAssetsState v-if="assets.length === 0" />
          <ul v-else class="flex flex-col divide-y divide-[var(--color-border-subtle)] px-5">
            <li v-for="asset in assets" :key="asset.id">
              <button
                type="button"
                class="flex w-full flex-col gap-1 py-3 text-left"
                @click="campaignStore.selectAsset(asset.id)"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-sm font-medium text-[var(--color-ink)]">{{ asset.title }}</span>
                  <span
                    class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                    :class="campaignStore.selectedAssetId === asset.id ? 'bg-[var(--color-ink)] text-white' : 'bg-[var(--color-accent-soft)] text-[var(--color-ink-muted)]'"
                  >
                    {{ campaignStore.selectedAssetId === asset.id ? 'Selected' : 'Select' }}
                  </span>
                </div>
                <p class="line-clamp-2 text-xs text-[var(--color-ink-muted)]">{{ asset.caption }}</p>
                <div class="flex flex-wrap gap-1">
                  <span v-for="tag in asset.hashtags" :key="tag" class="text-[11px] text-[var(--color-ink-faint)]">{{ tag }}</span>
                </div>
              </button>
            </li>
          </ul>
        </template>
        <AssetGrid v-else :assets="filteredAssets" />
      </div>

      <div class="min-h-0 flex-[2] border-t border-[var(--color-border-subtle)]">
        <CaptionEditor />
      </div>
    </div>
  </div>
</template>
