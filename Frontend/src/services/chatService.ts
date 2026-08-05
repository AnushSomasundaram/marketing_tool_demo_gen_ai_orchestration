import { apiClient, isMockMode } from './api'
import { mockSendChatMessage } from './mock'
import type { CampaignChatPayload, ChatMessage } from '@/types/chat'

export async function sendCampaignMessage(payload: CampaignChatPayload): Promise<ChatMessage> {
  if (isMockMode) return mockSendChatMessage(payload)
  const response = await apiClient.post<ChatMessage>(`/campaigns/${payload.campaignId}/chat`, payload)
  return response.data
}
