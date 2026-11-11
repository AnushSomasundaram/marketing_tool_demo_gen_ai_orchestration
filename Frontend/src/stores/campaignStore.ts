import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'

import * as campaignService from '@/services/campaignService'
import * as instagramService from '@/services/instagramService'
import { uploadProductImage, validateProductImage } from '@/services/uploadService'
import type { BrandTone, Campaign, CampaignAsset } from '@/types/campaign'
import { useUiStore } from './uiStore'

export interface ProductForm {
  productName: string
  productDescription: string
  targetAudience: string
  tone: BrandTone
  price: string
  websiteUrl: string
}

export interface UploadedProductImage {
  file: File
  previewUrl: string
  uploadedId: string
}

function createEmptyForm(): ProductForm {
  return {
    productName: '',
    productDescription: '',
    targetAudience: '',
    tone: 'professional',
    price: '',
    websiteUrl: '',
  }
}

// Campaign statuses that mean "still working" — covers both mock mode
// ('generating' only) and the real backend (which also has a 'planning'
// phase before generation starts).
const IN_PROGRESS_CAMPAIGN_STATUSES = new Set(['planning', 'generating'])

// Belt-and-suspenders alongside campaign.status: that field is a derived
// snapshot recomputed at specific points on the backend, so checking each
// asset's own status directly guards against any case where it lags behind
// what's actually still in flight.
function hasInProgressAssets(campaign: Campaign): boolean {
  return campaign.assets.some((asset) => asset.status === 'processing' || asset.status === 'queued')
}

export const useCampaignStore = defineStore('campaign', () => {
  const productForm = reactive<ProductForm>(createEmptyForm())

  const productImage = ref<UploadedProductImage | null>(null)
  const isUploadingImage = ref(false)
  const uploadProgress = ref(0)
  const uploadError = ref<string | null>(null)

  const campaign = ref<Campaign | null>(null)
  const selectedAssetId = ref<string | null>(null)

  const isGeneratingCampaign = ref(false)
  const generationError = ref<string | null>(null)

  const regeneratingAssetIds = ref<Set<string>>(new Set())
  const downloadingAssetIds = ref<Set<string>>(new Set())
  const isRegeneratingCampaign = ref(false)
  const isDownloadingAll = ref(false)
  const isPublishing = ref(false)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const selectedAsset = computed<CampaignAsset | null>(() => {
    if (!campaign.value || !selectedAssetId.value) return null
    return campaign.value.assets.find((asset) => asset.id === selectedAssetId.value) ?? null
  })

  const canGenerate = computed(() => {
    return Boolean(productImage.value) && productForm.productDescription.trim().length > 0 && !isGeneratingCampaign.value
  })

  const isCampaignGenerating = computed(() =>
    Boolean(campaign.value && IN_PROGRESS_CAMPAIGN_STATUSES.has(campaign.value.status)),
  )

  const canPublish = computed(() => {
    return Boolean(selectedAsset.value && selectedAsset.value.status === 'completed') && !isPublishing.value
  })

  function assetIsRegenerating(assetId: string): boolean {
    return regeneratingAssetIds.value.has(assetId)
  }

  function assetIsDownloading(assetId: string): boolean {
    return downloadingAssetIds.value.has(assetId)
  }

  async function setProductImage(file: File) {
    const validationError = validateProductImage(file)
    if (validationError) {
      uploadError.value = validationError
      const ui = useUiStore()
      ui.pushToast(validationError, 'error')
      return
    }

    uploadError.value = null
    isUploadingImage.value = true
    uploadProgress.value = 0

    const previewUrl = URL.createObjectURL(file)

    try {
      const uploaded = await uploadProductImage(file, (percent) => {
        uploadProgress.value = percent
      })
      productImage.value = { file, previewUrl, uploadedId: uploaded.id }
    } catch (error) {
      uploadError.value = error instanceof Error ? error.message : 'Upload failed'
      const ui = useUiStore()
      ui.pushToast(uploadError.value, 'error')
    } finally {
      isUploadingImage.value = false
    }
  }

  function removeProductImage() {
    if (productImage.value) {
      URL.revokeObjectURL(productImage.value.previewUrl)
    }
    productImage.value = null
    uploadProgress.value = 0
    uploadError.value = null
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /** Revisions always create a NEW asset id (immutable versioning) — if the
   * selected asset was just superseded, its id no longer appears in `latest`
   * at all, so a plain lookup would silently go null. Fall back to the same
   * array position (assets keep a stable sort_order across revisions, same
   * convention already used in regenerateAsset below) so selection follows
   * the asset through its version history instead of quietly detaching —
   * which otherwise both blanks the caption editor AND causes the next chat
   * turn targeting "the selected asset" to reference a dead id and get
   * silently dropped by the backend's scope validation. */
  function reconcileSelectedAsset(latest: Campaign) {
    if (!selectedAssetId.value || !campaign.value) return
    if (latest.assets.some((a) => a.id === selectedAssetId.value)) return
    const oldIndex = campaign.value.assets.findIndex((a) => a.id === selectedAssetId.value)
    const replacement = oldIndex !== -1 ? latest.assets[oldIndex] : undefined
    selectedAssetId.value = replacement?.id ?? null
  }

  function startPolling() {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!campaign.value) return stopPolling()
      try {
        const latest = await campaignService.getCampaign(campaign.value.id)
        reconcileSelectedAsset(latest)
        campaign.value = latest
        if (!IN_PROGRESS_CAMPAIGN_STATUSES.has(latest.status) && !hasInProgressAssets(latest)) {
          stopPolling()
        }
      } catch {
        stopPolling()
      }
    }, 1000)
  }

  async function generateCampaign() {
    if (!productImage.value) return
    const ui = useUiStore()

    isGeneratingCampaign.value = true
    generationError.value = null

    try {
      const created = await campaignService.createCampaign(
        {
          productName: productForm.productName || 'Untitled Product',
          productDescription: productForm.productDescription,
          targetAudience: productForm.targetAudience || undefined,
          tone: productForm.tone,
          price: productForm.price || undefined,
          websiteUrl: productForm.websiteUrl || undefined,
          productImageId: productImage.value.uploadedId,
        },
        productImage.value.file,
      )
      const started = await campaignService.startGeneration(created.id)
      campaign.value = started
      selectedAssetId.value = started.assets[0]?.id ?? null
      startPolling()
      ui.pushToast('Campaign generation started', 'success')
    } catch (error) {
      generationError.value = error instanceof Error ? error.message : 'Failed to generate campaign'
      ui.pushToast(generationError.value, 'error')
    } finally {
      isGeneratingCampaign.value = false
    }
  }

  async function regenerateCampaign() {
    if (!campaign.value) return
    const ui = useUiStore()
    isRegeneratingCampaign.value = true
    try {
      const updated = await campaignService.regenerateCampaign(campaign.value.id)
      reconcileSelectedAsset(updated)
      campaign.value = updated
      startPolling()
      ui.pushToast('Regenerating the full campaign', 'success')
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to regenerate campaign', 'error')
    } finally {
      isRegeneratingCampaign.value = false
    }
  }

  function selectAsset(assetId: string) {
    selectedAssetId.value = assetId
  }

  async function regenerateAsset(assetId: string, instruction?: string) {
    if (!campaign.value) return
    const ui = useUiStore()
    const index = campaign.value.assets.findIndex((a) => a.id === assetId)
    if (index === -1) return
    const asset = campaign.value.assets[index]!

    regeneratingAssetIds.value.add(assetId)
    asset.status = 'processing'
    asset.progress = 10
    asset.errorMessage = undefined

    try {
      // The real backend gives a revision a brand-new asset id (immutable
      // version history), so we replace by array position, not by id match.
      const updated = await campaignService.regenerateAsset(assetId, instruction)
      campaign.value.assets[index] = updated
      if (selectedAssetId.value === assetId) {
        selectedAssetId.value = updated.id
      }
      if (updated.status === 'failed') {
        ui.pushToast(updated.errorMessage ?? 'Regeneration failed', 'error')
      } else if (updated.status === 'completed') {
        // Mock mode resolves the whole revision synchronously; the real
        // backend only ever returns 'queued' here (see the else branch).
        ui.pushToast('Asset regenerated', 'success')
      } else {
        // Real backend: this call only kicks off the revision (202,
        // status 'queued'/'processing') — the actual generation runs in the
        // background. Poll so the card's spinner can resolve to the real
        // outcome instead of appearing to hang forever.
        ui.pushToast('Regenerating asset…', 'info')
        startPolling()
      }
    } catch (error) {
      asset.status = 'failed'
      asset.errorMessage = error instanceof Error ? error.message : 'Regeneration failed'
      ui.pushToast(asset.errorMessage, 'error')
    } finally {
      regeneratingAssetIds.value.delete(assetId)
    }
  }

  async function saveCaption(
    assetId: string,
    updates: { caption: string; hashtags: string[]; callToAction?: string },
  ) {
    const ui = useUiStore()
    const asset = campaign.value?.assets.find((a) => a.id === assetId)
    if (!asset) return

    try {
      const idForCaption = asset.captionId ?? asset.id
      const result = await campaignService.updateCaption(idForCaption, updates.caption, {
        hashtags: updates.hashtags,
        callToAction: updates.callToAction,
      })
      asset.captionId = result.captionId
      asset.caption = result.caption
      asset.hashtags = result.hashtags
      asset.callToAction = result.callToAction
      ui.pushToast('Caption saved', 'success')
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to save caption', 'error')
      throw error
    }
  }

  async function generateAlternativeCaption(assetId: string, tone?: string) {
    const ui = useUiStore()
    const asset = campaign.value?.assets.find((a) => a.id === assetId)
    if (!asset) return

    try {
      const idForCaption = asset.captionId ?? asset.id
      const result = await campaignService.regenerateCaption(idForCaption, tone)
      asset.captionId = result.captionId
      asset.caption = result.caption
      asset.hashtags = result.hashtags
      asset.callToAction = result.callToAction
      ui.pushToast('Generated an alternative caption', 'success')
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to generate caption', 'error')
    }
  }

  async function deleteAsset(assetId: string) {
    if (!campaign.value) return
    const ui = useUiStore()
    try {
      await campaignService.deleteAsset(assetId)
      campaign.value.assets = campaign.value.assets.filter((asset) => asset.id !== assetId)
      if (selectedAssetId.value === assetId) {
        selectedAssetId.value = campaign.value.assets[0]?.id ?? null
      }
      ui.pushToast('Asset deleted', 'success')
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to delete asset', 'error')
    }
  }

  async function downloadAsset(assetId: string) {
    const ui = useUiStore()
    downloadingAssetIds.value.add(assetId)
    try {
      const { url, fileName } = await campaignService.downloadAsset(assetId)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      link.target = '_blank'
      link.rel = 'noopener'
      link.click()
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Download failed', 'error')
    } finally {
      downloadingAssetIds.value.delete(assetId)
    }
  }

  async function downloadAllAssets() {
    if (!campaign.value) return
    isDownloadingAll.value = true
    try {
      for (const asset of campaign.value.assets) {
        if (asset.status === 'completed') {
          await downloadAsset(asset.id)
        }
      }
    } finally {
      isDownloadingAll.value = false
    }
  }

  async function publishCampaign() {
    if (!campaign.value || !selectedAsset.value) return
    const ui = useUiStore()
    isPublishing.value = true
    try {
      let job = await instagramService.publishAsset({
        campaignId: campaign.value.id,
        assetId: selectedAsset.value.id,
        captionId: selectedAsset.value.captionId,
        isAiGenerated: true,
      })

      while (!instagramService.TERMINAL_PUBLISH_STATUSES.includes(job.status)) {
        await new Promise((resolve) => setTimeout(resolve, 1500))
        job = await instagramService.getPublishStatus(job.id)
      }

      if (job.status === 'completed') {
        ui.pushToast(job.isSimulated ? 'Published (simulated demo mode)' : 'Published to Instagram', 'success')
        await refreshCampaign()
      } else {
        ui.pushToast(job.errorMessage ?? 'Failed to publish campaign', 'error')
      }
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to publish campaign', 'error')
    } finally {
      isPublishing.value = false
    }
  }

  async function refreshCampaign() {
    if (!campaign.value) return
    try {
      const latest = await campaignService.getCampaign(campaign.value.id)
      reconcileSelectedAsset(latest)
      campaign.value = latest
      if (IN_PROGRESS_CAMPAIGN_STATUSES.has(latest.status) || hasInProgressAssets(latest)) {
        startPolling()
      }
    } catch {
      // Ignore transient refresh failures; polling (if active) will retry.
    }
  }

  function resetCampaign() {
    stopPolling()
    campaign.value = null
    selectedAssetId.value = null
    generationError.value = null
    removeProductImage()
    Object.assign(productForm, createEmptyForm())
  }

  /** Unlike resetCampaign (which only clears local state, used for "start a
   * new campaign"), this permanently deletes the campaign and its assets/
   * captions on the backend before clearing local state. */
  async function deleteCampaign() {
    if (!campaign.value) return
    const ui = useUiStore()
    try {
      await campaignService.deleteCampaign(campaign.value.id)
      resetCampaign()
      ui.pushToast('Campaign deleted', 'success')
    } catch (error) {
      ui.pushToast(error instanceof Error ? error.message : 'Failed to delete campaign', 'error')
    }
  }

  return {
    productForm,
    productImage,
    isUploadingImage,
    uploadProgress,
    uploadError,
    campaign,
    selectedAssetId,
    selectedAsset,
    canGenerate,
    isGeneratingCampaign,
    isCampaignGenerating,
    generationError,
    isRegeneratingCampaign,
    isDownloadingAll,
    isPublishing,
    canPublish,
    assetIsRegenerating,
    assetIsDownloading,
    setProductImage,
    removeProductImage,
    generateCampaign,
    regenerateCampaign,
    selectAsset,
    regenerateAsset,
    saveCaption,
    generateAlternativeCaption,
    deleteAsset,
    downloadAsset,
    downloadAllAssets,
    publishCampaign,
    refreshCampaign,
    resetCampaign,
    deleteCampaign,
  }
})
