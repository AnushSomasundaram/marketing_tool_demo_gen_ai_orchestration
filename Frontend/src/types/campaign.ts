export type AssetType = 'image' | 'video'

export type AssetStatus = 'queued' | 'processing' | 'completed' | 'failed'

export type CampaignStatus =
  | 'draft'
  | 'planning'
  | 'generating'
  | 'ready'
  | 'partially_failed'
  | 'failed'
  | 'publishing'
  | 'published'

export type BrandTone = 'professional' | 'playful' | 'minimal' | 'luxury' | 'energetic'

export interface BrandToneOption {
  value: BrandTone
  label: string
  description: string
}

export const BRAND_TONE_OPTIONS: BrandToneOption[] = [
  { value: 'professional', label: 'Professional', description: 'Polished, trustworthy, corporate-safe' },
  { value: 'playful', label: 'Playful', description: 'Fun, casual, a little cheeky' },
  { value: 'minimal', label: 'Minimal', description: 'Clean, understated, lots of white space' },
  { value: 'luxury', label: 'Luxury', description: 'Premium, refined, aspirational' },
  { value: 'energetic', label: 'Energetic', description: 'Bold, vibrant, high-motion' },
]

export interface CaptionVersion {
  id: string
  caption: string
  hashtags: string[]
  callToAction?: string
  tone: string
  createdAt: string
}

export interface CampaignAsset {
  id: string
  type: AssetType
  title: string
  previewUrl: string | null
  downloadUrl?: string | null
  caption: string
  hashtags: string[]
  callToAction?: string
  aspectRatio: string
  duration?: number
  version: number
  status: AssetStatus
  progress?: number
  errorMessage?: string
  captionHistory?: CaptionVersion[]
  /** Only present when connected to a real backend, where captions are a
   * separate versioned resource. Falls back to the asset id (mock mode, or
   * before the backend has assigned one) wherever it's consumed. */
  captionId?: string
}

export interface Campaign {
  id: string
  title: string
  productName: string
  productDescription: string
  targetAudience?: string
  tone: string
  status: string
  assets: CampaignAsset[]
  createdAt: string
  /** Only present when connected to a real backend. */
  productImageUrl?: string | null
}

export interface UploadedImage {
  id: string
  url: string
  fileName: string
  size: number
  type: string
}

export interface CreateCampaignPayload {
  productName: string
  productDescription: string
  targetAudience?: string
  tone: BrandTone
  price?: string
  websiteUrl?: string
  productImageId: string
}
