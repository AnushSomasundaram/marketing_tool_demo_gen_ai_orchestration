export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

export type ChatScope = 'campaign' | 'selected_asset' | 'caption_only' | 'visual_only'

export interface ChatScopeOption {
  value: ChatScope
  label: string
  description: string
}

export const CHAT_SCOPE_OPTIONS: ChatScopeOption[] = [
  { value: 'campaign', label: 'Entire campaign', description: 'Apply to every asset' },
  { value: 'selected_asset', label: 'Selected asset', description: 'Apply to the selected card only' },
  { value: 'caption_only', label: 'Caption only', description: 'Rewrite text, keep visuals' },
  { value: 'visual_only', label: 'Visual only', description: 'Rework the image or video only' },
]

export const SUGGESTED_PROMPTS: string[] = [
  'Create a premium campaign for this product',
  'Make the visual style more energetic',
  'Generate captions aimed at college students',
  'Make the video feel more luxurious',
]

export interface CampaignChatPayload {
  campaignId: string
  message: string
  scope: ChatScope
  selectedAssetId?: string
}

export interface CampaignChatResponse {
  message: ChatMessage
  campaignId: string
}
