<script setup lang="ts">
import { useCampaignStore } from '@/stores/campaignStore'
import { useChatStore } from '@/stores/chatStore'
import { useUiStore } from '@/stores/uiStore'
import type { CampaignAsset } from '@/types/campaign'
import ImageAssetCard from './ImageAssetCard.vue'
import VideoAssetCard from './VideoAssetCard.vue'
import EmptyAssetsState from './EmptyAssetsState.vue'

const props = defineProps<{ assets: CampaignAsset[] }>()

const campaignStore = useCampaignStore()
const chatStore = useChatStore()
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
  // "Refine with AI" only means anything once the chat is actually scoped to
  // this one asset — leaving the scope on whatever it was before (e.g. the
  // "Entire campaign" default) silently applies the next message everywhere.
  chatStore.setScope('selected_asset')
  uiStore.setMobileTab('create')
  chatStore.requestFocus()
  uiStore.pushToast(`Chat scoped to "${asset.title}" — describe your change below`, 'info')
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
