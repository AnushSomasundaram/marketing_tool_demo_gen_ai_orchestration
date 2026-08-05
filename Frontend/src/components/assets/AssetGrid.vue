<script setup lang="ts">
import { useCampaignStore } from '@/stores/campaignStore'
import { useUiStore } from '@/stores/uiStore'
import type { CampaignAsset } from '@/types/campaign'
import ImageAssetCard from './ImageAssetCard.vue'
import VideoAssetCard from './VideoAssetCard.vue'
import EmptyAssetsState from './EmptyAssetsState.vue'

const props = defineProps<{ assets: CampaignAsset[] }>()

const campaignStore = useCampaignStore()
const uiStore = useUiStore()

function handleDelete(asset: CampaignAsset) {
  uiStore.openConfirmDialog({
    title: `Delete "${asset.title}"?`,
    message: 'This asset and its caption history will be permanently removed.',
    confirmLabel: 'Delete',
    danger: true,
    onConfirm: () => campaignStore.deleteAsset(asset.id),
  })
}

function handleRefine(asset: CampaignAsset) {
  campaignStore.selectAsset(asset.id)
  uiStore.pushToast('Selected asset — describe your refinement in the chat', 'info')
}
</script>

<template>
  <EmptyAssetsState v-if="props.assets.length === 0" />
  <div v-else class="grid grid-cols-1 gap-4 p-5 sm:grid-cols-2 xl:grid-cols-3">
    <template v-for="asset in props.assets" :key="asset.id">
      <VideoAssetCard
        v-if="asset.type === 'video'"
        :asset="asset"
        :selected="campaignStore.selectedAssetId === asset.id"
        @select="campaignStore.selectAsset(asset.id)"
        @preview="uiStore.openAssetPreview(asset.id)"
        @regenerate="campaignStore.regenerateAsset(asset.id)"
        @download="campaignStore.downloadAsset(asset.id)"
        @delete="handleDelete(asset)"
        @refine="handleRefine(asset)"
      />
      <ImageAssetCard
        v-else
        :asset="asset"
        :selected="campaignStore.selectedAssetId === asset.id"
        @select="campaignStore.selectAsset(asset.id)"
        @preview="uiStore.openAssetPreview(asset.id)"
        @regenerate="campaignStore.regenerateAsset(asset.id)"
        @download="campaignStore.downloadAsset(asset.id)"
        @delete="handleDelete(asset)"
        @refine="handleRefine(asset)"
      />
    </template>
  </div>
</template>
