import { apiClient, isMockMode } from './api'
import {
  mockCreateCampaign,
  mockDeleteAsset,
  mockDownloadAsset,
  mockGenerateAlternativeCaption,
  mockGetCampaign,
  mockRegenerateAsset,
  mockRegenerateCampaign,
  mockUpdateCaption,
} from './mock'
import type { Campaign, CampaignAsset, CreateCampaignPayload } from '@/types/campaign'

/** Caption endpoints on the real backend return a Caption resource, not an
 * asset — captions are a separate versioned entity there. Mock mode still
 * models a caption as fields embedded on the asset, so the mock branch below
 * adapts a mocked CampaignAsset into this same shape. */
export interface CaptionUpdateResult {
  captionId: string
  caption: string
  hashtags: string[]
  callToAction?: string
}

export async function createCampaign(payload: CreateCampaignPayload, imageFile?: File): Promise<Campaign> {
  if (isMockMode) return mockCreateCampaign(payload)

  const formData = new FormData()
  if (imageFile) formData.append('productImage', imageFile)
  formData.append('productName', payload.productName)
  formData.append('productDescription', payload.productDescription)
  if (payload.targetAudience) formData.append('targetAudience', payload.targetAudience)
  formData.append('tone', payload.tone)
  if (payload.price) formData.append('price', payload.price)
  if (payload.websiteUrl) formData.append('websiteUrl', payload.websiteUrl)

  const response = await apiClient.post<Campaign>('/campaigns', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/** No-op in mock mode, where creating a campaign already starts generation.
 * On the real backend, POST /campaigns only creates a draft — this separate
 * call is what actually kicks off planning + image/video/caption generation. */
export async function startGeneration(campaignId: string): Promise<Campaign> {
  if (isMockMode) return mockGetCampaign(campaignId)
  const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/generate`)
  return response.data
}

export async function getCampaign(campaignId: string): Promise<Campaign> {
  if (isMockMode) return mockGetCampaign(campaignId)
  const response = await apiClient.get<Campaign>(`/campaigns/${campaignId}`)
  return response.data
}

/** Returns the *new* asset version created by the revision — callers must
 * replace the old asset by array position, not by matching id, since the
 * real backend gives revisions a new id (see campaignStore.regenerateAsset). */
export async function regenerateAsset(assetId: string, instruction?: string): Promise<CampaignAsset> {
  if (isMockMode) return mockRegenerateAsset(assetId, instruction)
  const response = await apiClient.post<CampaignAsset>(`/assets/${assetId}/revise`, { instruction })
  return response.data
}

export async function updateCaption(
  captionId: string,
  caption: string,
  extra?: { hashtags?: string[]; callToAction?: string },
): Promise<CaptionUpdateResult> {
  if (isMockMode) {
    const asset = await mockUpdateCaption(captionId, caption)
    return { captionId: asset.id, caption: asset.caption, hashtags: asset.hashtags, callToAction: asset.callToAction }
  }
  const response = await apiClient.patch<{ id: string; caption: string; hashtags: string[]; callToAction?: string }>(
    `/captions/${captionId}`,
    { caption, hashtags: extra?.hashtags, callToAction: extra?.callToAction },
  )
  return {
    captionId: response.data.id,
    caption: response.data.caption,
    hashtags: response.data.hashtags,
    callToAction: response.data.callToAction,
  }
}

export async function deleteAsset(assetId: string): Promise<void> {
  if (isMockMode) return mockDeleteAsset(assetId)
  await apiClient.delete(`/assets/${assetId}`)
}

/** Mock mode has no persisted campaign to delete server-side — the store's
 * local reset is the whole of "deleting" a campaign there. On the real
 * backend this permanently removes the campaign row and its assets/captions. */
export async function deleteCampaign(campaignId: string): Promise<void> {
  if (isMockMode) return
  await apiClient.delete(`/campaigns/${campaignId}`)
}

export async function downloadAsset(assetId: string): Promise<{ url: string; fileName: string }> {
  if (isMockMode) return mockDownloadAsset(assetId)
  const response = await apiClient.get<{ url: string; fileName: string }>(`/assets/${assetId}/download`)
  return response.data
}

export async function regenerateCampaign(campaignId: string): Promise<Campaign> {
  if (isMockMode) return mockRegenerateCampaign(campaignId)
  const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/regenerate`)
  return response.data
}

export async function regenerateCaption(captionId: string, tone?: string): Promise<CaptionUpdateResult> {
  if (isMockMode) {
    const asset = await mockGenerateAlternativeCaption(captionId, tone)
    return { captionId: asset.id, caption: asset.caption, hashtags: asset.hashtags, callToAction: asset.callToAction }
  }
  const response = await apiClient.post<{ id: string; caption: string; hashtags: string[]; callToAction?: string }>(
    `/captions/${captionId}/alternatives`,
    { tone },
  )
  return {
    captionId: response.data.id,
    caption: response.data.caption,
    hashtags: response.data.hashtags,
    callToAction: response.data.callToAction,
  }
}
