import type { Campaign, CampaignAsset, CreateCampaignPayload, UploadedImage } from '@/types/campaign'
import type { CampaignChatPayload, ChatMessage, ChatScope } from '@/types/chat'

// ---------------------------------------------------------------------------
// In-memory "backend" used when VITE_USE_MOCK_API=true. Simulates network
// delay, async asset generation, and occasional recoverable failures so the
// UI can be built and tested against realistic conditions before a real
// backend exists.
// ---------------------------------------------------------------------------

const campaigns = new Map<string, Campaign>()
const assetToCampaign = new Map<string, string>()

export function uid(prefix: string): string {
  return `${prefix}_${crypto.randomUUID().slice(0, 8)}`
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function randomBetween(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function chance(probability: number): boolean {
  return Math.random() < probability
}

const CAPTION_TEMPLATES: Record<string, string[]> = {
  professional: [
    '{product} — engineered for results you can measure. Built for people who expect more from their tools.',
    'Introducing {product}. Reliable performance, refined design, made for professionals.',
  ],
  playful: [
    'Okay but {product} is kind of a whole vibe 😄 you need this in your life.',
    "We made {product} and honestly? We're obsessed. You will be too.",
  ],
  minimal: [
    '{product}. Nothing extra.',
    'Less noise. Just {product}.',
  ],
  luxury: [
    '{product} — a quiet statement of taste. Crafted for those who notice the details.',
    'Some things are not for everyone. {product} is one of them.',
  ],
  energetic: [
    "{product} is HERE and it's about to change everything ⚡ let's go!",
    'Stop scrolling. {product} just dropped and it is unreal 🔥',
  ],
}

const HASHTAG_POOL: Record<string, string[]> = {
  professional: ['#Business', '#Quality', '#Innovation', '#Trusted', '#Craftsmanship'],
  playful: ['#ObsessedAlready', '#TreatYourself', '#NewFavorite', '#DailyEssential'],
  minimal: ['#LessIsMore', '#SimplyBetter', '#Considered', '#Essentials'],
  luxury: ['#Luxury', '#Refined', '#Exclusive', '#TimelessDesign', '#Curated'],
  energetic: ['#GameChanger', '#DropAlert', '#MustHave', '#TrendingNow', '#LevelUp'],
}

function buildCaption(tone: string, productName: string): string {
  const templates = CAPTION_TEMPLATES[tone] ?? CAPTION_TEMPLATES.professional!
  const template = templates[randomBetween(0, templates.length - 1)]!
  return template.replace('{product}', productName)
}

function buildHashtags(tone: string, productName: string): string[] {
  const pool = HASHTAG_POOL[tone] ?? HASHTAG_POOL.professional!
  const productTag = `#${productName.replace(/[^a-zA-Z0-9]/g, '')}`
  return [productTag, ...pool.slice(0, 4)]
}

function placeholderImageUrl(seed: string, width: number, height: number): string {
  return `https://picsum.photos/seed/${seed}/${width}/${height}`
}

const ASSET_BLUEPRINTS: Array<{ type: 'image' | 'video'; aspectRatio: string; width: number; height: number; label: string }> = [
  { type: 'image', aspectRatio: '1:1', width: 800, height: 800, label: 'Feed Post' },
  { type: 'image', aspectRatio: '4:5', width: 800, height: 1000, label: 'Feed Post' },
  { type: 'image', aspectRatio: '1:1', width: 800, height: 800, label: 'Feed Post' },
  { type: 'video', aspectRatio: '9:16', width: 720, height: 1280, label: 'Reel' },
]

function createInitialAssets(payload: CreateCampaignPayload, campaignSeed: string): CampaignAsset[] {
  return ASSET_BLUEPRINTS.map((blueprint, index) => {
    const seed = `${campaignSeed}-${index}`
    const caption = buildCaption(payload.tone, payload.productName)
    const hashtags = buildHashtags(payload.tone, payload.productName)
    const asset: CampaignAsset = {
      id: uid('asset'),
      type: blueprint.type,
      title: `${blueprint.label} ${index + 1}`,
      previewUrl: placeholderImageUrl(seed, blueprint.width, blueprint.height),
      downloadUrl: placeholderImageUrl(seed, blueprint.width, blueprint.height),
      caption,
      hashtags,
      callToAction: payload.websiteUrl ? 'Shop now' : 'Learn more',
      aspectRatio: blueprint.aspectRatio,
      duration: blueprint.type === 'video' ? randomBetween(8, 24) : undefined,
      version: 1,
      status: 'queued',
      progress: 0,
      captionHistory: [],
    }
    return asset
  })
}

function runGenerationSimulation(campaignId: string, isRegeneration = false): void {
  const campaign = campaigns.get(campaignId)
  if (!campaign) return

  campaign.assets.forEach((asset, index) => {
    const startDelay = 400 + index * 350
    setTimeout(() => {
      asset.status = 'processing'
      asset.progress = 5

      const totalDuration = asset.type === 'video' ? randomBetween(3500, 6000) : randomBetween(1200, 2600)
      const tickMs = 300
      const ticks = Math.floor(totalDuration / tickMs)
      let tick = 0

      const interval = setInterval(() => {
        tick += 1
        asset.progress = Math.min(96, Math.round((tick / ticks) * 100))

        if (tick >= ticks) {
          clearInterval(interval)
          const failureRate = asset.type === 'video' ? 0.15 : 0.06
          if (chance(failureRate)) {
            asset.status = 'failed'
            asset.progress = undefined
            asset.errorMessage =
              asset.type === 'video'
                ? 'Video rendering failed unexpectedly. This is usually recoverable — try again.'
                : 'Image generation failed. Retry to attempt again.'
          } else {
            asset.status = 'completed'
            asset.progress = 100
            if (isRegeneration) {
              asset.version += 1
              const seed = `${asset.id}-v${asset.version}-${Date.now()}`
              const [w, h] = asset.aspectRatio === '9:16' ? [720, 1280] : asset.aspectRatio === '4:5' ? [800, 1000] : [800, 800]
              asset.previewUrl = placeholderImageUrl(seed, w, h)
              asset.downloadUrl = asset.previewUrl
              if (asset.type === 'video') asset.duration = randomBetween(8, 24)
            }
          }
          maybeCompleteCampaign(campaignId)
        }
      }, tickMs)
    }, startDelay)
  })
}

function maybeCompleteCampaign(campaignId: string): void {
  const campaign = campaigns.get(campaignId)
  if (!campaign) return
  const allSettled = campaign.assets.every((a) => a.status === 'completed' || a.status === 'failed')
  if (allSettled) {
    campaign.status = 'completed'
  }
}

export async function mockUploadProductImage(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadedImage> {
  const steps = [10, 28, 47, 65, 82, 100]
  for (const step of steps) {
    await delay(120 + Math.random() * 120)
    onProgress?.(step)
  }
  return {
    id: uid('img'),
    url: URL.createObjectURL(file),
    fileName: file.name,
    size: file.size,
    type: file.type,
  }
}

export async function mockCreateCampaign(payload: CreateCampaignPayload): Promise<Campaign> {
  await delay(900)
  const id = uid('campaign')
  const campaign: Campaign = {
    id,
    title: `${payload.productName} Campaign`,
    productName: payload.productName,
    productDescription: payload.productDescription,
    targetAudience: payload.targetAudience,
    tone: payload.tone,
    status: 'generating',
    assets: createInitialAssets(payload, id),
    createdAt: new Date().toISOString(),
  }
  campaigns.set(id, campaign)
  campaign.assets.forEach((asset) => assetToCampaign.set(asset.id, id))
  runGenerationSimulation(id)
  return structuredClone(campaign)
}

export async function mockGetCampaign(campaignId: string): Promise<Campaign> {
  await delay(150)
  const campaign = campaigns.get(campaignId)
  if (!campaign) throw new Error('Campaign not found')
  return structuredClone(campaign)
}

export async function mockRegenerateAsset(assetId: string, instruction?: string): Promise<CampaignAsset> {
  const campaignId = assetToCampaign.get(assetId)
  const campaign = campaignId ? campaigns.get(campaignId) : undefined
  const asset = campaign?.assets.find((a) => a.id === assetId)
  if (!campaign || !asset) throw new Error('Asset not found')

  asset.status = 'processing'
  asset.progress = 10
  asset.errorMessage = undefined
  await delay(1400 + Math.random() * 1200)

  const failureRate = asset.type === 'video' ? 0.15 : 0.08
  if (chance(failureRate)) {
    asset.status = 'failed'
    asset.progress = undefined
    asset.errorMessage = instruction
      ? `Could not apply "${instruction}". Try again or rephrase your instruction.`
      : 'Regeneration failed. This is usually recoverable — try again.'
    return structuredClone(asset)
  }

  asset.version += 1
  asset.status = 'completed'
  asset.progress = 100
  const seed = `${assetId}-v${asset.version}-${Date.now()}`
  const [w, h] = asset.aspectRatio === '9:16' ? [720, 1280] : asset.aspectRatio === '4:5' ? [800, 1000] : [800, 800]
  asset.previewUrl = placeholderImageUrl(seed, w, h)
  asset.downloadUrl = asset.previewUrl
  if (asset.type === 'video') {
    asset.duration = randomBetween(8, 24)
  }
  return structuredClone(asset)
}

export async function mockUpdateCaption(assetId: string, caption: string): Promise<CampaignAsset> {
  const campaignId = assetToCampaign.get(assetId)
  const campaign = campaignId ? campaigns.get(campaignId) : undefined
  const asset = campaign?.assets.find((a) => a.id === assetId)
  if (!campaign || !asset) throw new Error('Asset not found')

  await delay(350)
  asset.captionHistory = asset.captionHistory ?? []
  asset.captionHistory.push({
    id: uid('caption'),
    caption: asset.caption,
    hashtags: [...asset.hashtags],
    callToAction: asset.callToAction,
    tone: campaign.tone,
    createdAt: new Date().toISOString(),
  })
  asset.caption = caption
  return structuredClone(asset)
}

export async function mockDeleteAsset(assetId: string): Promise<void> {
  const campaignId = assetToCampaign.get(assetId)
  const campaign = campaignId ? campaigns.get(campaignId) : undefined
  if (!campaign) throw new Error('Asset not found')

  await delay(400)
  campaign.assets = campaign.assets.filter((a) => a.id !== assetId)
  assetToCampaign.delete(assetId)
}

export async function mockDownloadAsset(assetId: string): Promise<{ url: string; fileName: string }> {
  const campaignId = assetToCampaign.get(assetId)
  const campaign = campaignId ? campaigns.get(campaignId) : undefined
  const asset = campaign?.assets.find((a) => a.id === assetId)
  if (!asset) throw new Error('Asset not found')

  await delay(300)
  return {
    url: asset.downloadUrl ?? asset.previewUrl ?? '',
    fileName: `${asset.title.replace(/\s+/g, '-').toLowerCase()}.png`,
  }
}

function resetAndRegenerateCampaign(campaignId: string): void {
  const campaign = campaigns.get(campaignId)
  if (!campaign) return
  campaign.status = 'generating'
  campaign.assets.forEach((asset) => {
    asset.status = 'queued'
    asset.progress = 0
    asset.errorMessage = undefined
  })
  runGenerationSimulation(campaignId, true)
}

export async function mockRegenerateCampaign(campaignId: string): Promise<Campaign> {
  await delay(300)
  resetAndRegenerateCampaign(campaignId)
  const campaign = campaigns.get(campaignId)
  if (!campaign) throw new Error('Campaign not found')
  return structuredClone(campaign)
}

export async function mockGenerateAlternativeCaption(assetId: string, tone?: string): Promise<CampaignAsset> {
  const campaignId = assetToCampaign.get(assetId)
  const campaign = campaignId ? campaigns.get(campaignId) : undefined
  const asset = campaign?.assets.find((a) => a.id === assetId)
  if (!campaign || !asset) throw new Error('Asset not found')

  const effectiveTone = tone ?? campaign.tone
  await delay(600 + Math.random() * 400)
  asset.captionHistory = asset.captionHistory ?? []
  asset.captionHistory.push({
    id: uid('caption'),
    caption: asset.caption,
    hashtags: [...asset.hashtags],
    callToAction: asset.callToAction,
    tone: campaign.tone,
    createdAt: new Date().toISOString(),
  })
  asset.caption = buildCaption(effectiveTone, campaign.productName)
  asset.hashtags = buildHashtags(effectiveTone, campaign.productName)
  return structuredClone(asset)
}

export async function mockPublishCampaign(campaignId: string): Promise<Campaign> {
  const campaign = campaigns.get(campaignId)
  if (!campaign) throw new Error('Campaign not found')

  await delay(1100)
  campaign.status = 'published'
  return structuredClone(campaign)
}

const SCOPE_REPLIES: Record<ChatScope, string[]> = {
  campaign: [
    "Got it — I'm reworking the entire campaign now. Give me a moment to regenerate every asset.",
    "On it. I'll apply that across all posts, captions, and the video.",
  ],
  selected_asset: [
    "Updating the selected asset now — you'll see a new version shortly.",
    "Applying that to the asset you've got selected.",
  ],
  caption_only: [
    "Rewriting the caption to match — visuals stay untouched.",
    'Got it, updating just the copy now.',
  ],
  visual_only: [
    "Reworking the visual now, keeping the caption as-is.",
    "On it — regenerating the image/video, no changes to your copy.",
  ],
}

export async function mockSendChatMessage(payload: CampaignChatPayload): Promise<ChatMessage> {
  await delay(700 + Math.random() * 500)

  const replies = SCOPE_REPLIES[payload.scope] ?? SCOPE_REPLIES.campaign
  const content = replies[randomBetween(0, replies.length - 1)]!

  const campaign = campaigns.get(payload.campaignId)
  if (campaign) {
    if (payload.scope === 'campaign') {
      resetAndRegenerateCampaign(payload.campaignId)
    } else if (
      (payload.scope === 'selected_asset' || payload.scope === 'visual_only') &&
      payload.selectedAssetId
    ) {
      void mockRegenerateAsset(payload.selectedAssetId, payload.message)
    } else if (payload.scope === 'caption_only' && payload.selectedAssetId) {
      const asset = campaign.assets.find((a) => a.id === payload.selectedAssetId)
      if (asset) {
        void mockUpdateCaption(asset.id, buildCaption(campaign.tone, campaign.productName))
      }
    }
  }

  return {
    id: uid('msg'),
    role: 'assistant',
    content,
    createdAt: new Date().toISOString(),
  }
}
