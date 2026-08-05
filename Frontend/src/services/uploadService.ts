import { isMockMode } from './api'
import { mockUploadProductImage } from './mock'
import type { UploadedImage } from '@/types/campaign'

export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024 // 10MB
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function validateProductImage(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return 'Please upload a JPG, PNG, or WebP image.'
  }
  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return 'Image must be smaller than 10MB.'
  }
  return null
}

/**
 * The real backend has no standalone "upload just the image" endpoint — the
 * product image is sent as part of the multipart POST /campaigns request
 * (see campaignService.createCampaign). So in real mode this just gives the
 * UI an id/local preview URL to work with immediately; the actual bytes are
 * only sent to the backend once the user clicks "Generate Campaign".
 */
export async function uploadProductImage(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadedImage> {
  if (isMockMode) {
    return mockUploadProductImage(file, onProgress)
  }

  onProgress?.(100)
  return {
    id: crypto.randomUUID(),
    url: URL.createObjectURL(file),
    fileName: file.name,
    size: file.size,
    type: file.type,
  }
}
