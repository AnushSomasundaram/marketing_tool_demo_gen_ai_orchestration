import { apiClient, isMockMode } from './api'
import { mockPublishCampaign } from './mock'

export type PublishJobStatus =
  | 'queued'
  | 'container_created'
  | 'processing'
  | 'publishing'
  | 'completed'
  | 'failed'

export interface PublishJob {
  id: string
  campaignId: string
  assetId: string
  captionId?: string
  status: PublishJobStatus
  isAiGenerated: boolean
  isSimulated: boolean
  instagramMediaId?: string
  permalink?: string
  errorCode?: string
  errorMessage?: string
}

export interface PublishRequestPayload {
  campaignId: string
  assetId: string
  captionId?: string
  isAiGenerated?: boolean
}

export const TERMINAL_PUBLISH_STATUSES: PublishJobStatus[] = ['completed', 'failed']

export async function publishAsset(payload: PublishRequestPayload): Promise<PublishJob> {
  if (isMockMode) {
    // The bundled mock has no separate publish-job concept; it resolves the
    // whole flow synchronously and clearly marks the result as simulated.
    await mockPublishCampaign(payload.campaignId)
    return {
      id: crypto.randomUUID(),
      campaignId: payload.campaignId,
      assetId: payload.assetId,
      captionId: payload.captionId,
      status: 'completed',
      isAiGenerated: payload.isAiGenerated ?? true,
      isSimulated: true,
      instagramMediaId: `mock_media_${crypto.randomUUID().slice(0, 8)}`,
      permalink: 'https://www.instagram.com/p/mock-simulated/',
    }
  }

  const response = await apiClient.post<PublishJob>('/instagram/publish', payload)
  return response.data
}

export async function getPublishStatus(jobId: string): Promise<PublishJob> {
  const response = await apiClient.get<PublishJob>(`/instagram/publish/${jobId}`)
  return response.data
}
