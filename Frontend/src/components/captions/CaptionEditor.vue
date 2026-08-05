<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AlertCircle, Copy, Sparkles } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import { useUiStore } from '@/stores/uiStore'
import { BRAND_TONE_OPTIONS, type BrandTone, type CaptionVersion } from '@/types/campaign'
import AppButton from '@/components/shared/AppButton.vue'
import AppTextarea from '@/components/shared/AppTextarea.vue'
import AppSelect from '@/components/shared/AppSelect.vue'
import HashtagEditor from './HashtagEditor.vue'
import CaptionVersionSelector from './CaptionVersionSelector.vue'

const campaignStore = useCampaignStore()
const uiStore = useUiStore()

const captionDraft = ref('')
const hashtagsDraft = ref<string[]>([])
const ctaDraft = ref('')
const toneDraft = ref<BrandTone>('professional')
const isSaving = ref(false)
const isGeneratingAlternative = ref(false)

const toneOptions = BRAND_TONE_OPTIONS.map((tone) => ({ value: tone.value, label: tone.label }))

const CAPTION_MAX_LENGTH = 2200

function loadDraftFromAsset() {
  const asset = campaignStore.selectedAsset
  captionDraft.value = asset?.caption ?? ''
  hashtagsDraft.value = asset ? [...asset.hashtags] : []
  ctaDraft.value = asset?.callToAction ?? ''
  toneDraft.value = (campaignStore.campaign?.tone as BrandTone) ?? 'professional'
}

watch(() => campaignStore.selectedAssetId, loadDraftFromAsset, { immediate: true })

const isDirty = computed(() => {
  const asset = campaignStore.selectedAsset
  if (!asset) return false
  return (
    captionDraft.value !== asset.caption ||
    ctaDraft.value !== (asset.callToAction ?? '') ||
    JSON.stringify(hashtagsDraft.value) !== JSON.stringify(asset.hashtags)
  )
})

async function handleCopy() {
  const asset = campaignStore.selectedAsset
  if (!asset) return
  const parts = [captionDraft.value, hashtagsDraft.value.join(' ')]
  if (ctaDraft.value) parts.push(ctaDraft.value)
  await navigator.clipboard.writeText(parts.filter(Boolean).join('\n\n'))
  uiStore.pushToast('Caption copied to clipboard', 'success')
}

async function handleSave() {
  const asset = campaignStore.selectedAsset
  if (!asset) return
  isSaving.value = true
  try {
    await campaignStore.saveCaption(asset.id, {
      caption: captionDraft.value,
      hashtags: hashtagsDraft.value,
      callToAction: ctaDraft.value || undefined,
    })
  } finally {
    isSaving.value = false
  }
}

async function handleGenerateAlternative() {
  const asset = campaignStore.selectedAsset
  if (!asset) return
  isGeneratingAlternative.value = true
  try {
    await campaignStore.generateAlternativeCaption(asset.id, toneDraft.value)
    loadDraftFromAsset()
  } finally {
    isGeneratingAlternative.value = false
  }
}

function handleRestoreVersion(version: CaptionVersion) {
  captionDraft.value = version.caption
  hashtagsDraft.value = [...version.hashtags]
  ctaDraft.value = version.callToAction ?? ''
  uiStore.pushToast('Version restored — remember to save your changes', 'info')
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-white">
    <div v-if="!campaignStore.selectedAsset" class="flex flex-1 items-center justify-center px-5 py-8">
      <p class="text-xs text-[var(--color-ink-faint)]">Select an asset to edit its caption</p>
    </div>

    <div v-else class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p class="text-xs font-medium text-[var(--color-ink-muted)]">Editing caption for</p>
          <p class="text-sm font-semibold text-[var(--color-ink)]">{{ campaignStore.selectedAsset.title }}</p>
        </div>
        <CaptionVersionSelector :versions="campaignStore.selectedAsset.captionHistory ?? []" @restore="handleRestoreVersion" />
      </div>

      <div v-if="isDirty" class="flex items-center gap-1.5 rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs text-amber-700">
        <AlertCircle class="size-3.5 shrink-0" />
        You have unsaved changes to this caption.
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="flex flex-col gap-1.5 md:col-span-2">
          <AppTextarea v-model="captionDraft" label="Caption" :rows="4" :maxlength="CAPTION_MAX_LENGTH" />
          <p class="text-right text-[11px] text-[var(--color-ink-faint)]">{{ captionDraft.length }} / {{ CAPTION_MAX_LENGTH }}</p>
        </div>

        <HashtagEditor v-model="hashtagsDraft" />

        <div class="flex flex-col gap-3">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-[var(--color-ink-muted)]">Call to action</label>
            <input
              v-model="ctaDraft"
              type="text"
              placeholder="e.g. Shop now"
              class="h-9 rounded-lg border border-[var(--color-border-subtle)] bg-white px-3 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)] focus:border-[var(--color-ink)]"
            />
          </div>
          <AppSelect v-model="toneDraft" :options="toneOptions" label="Tone for alternatives" />
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--color-border-subtle)] pt-3">
        <AppButton variant="ghost" size="sm" @click="handleCopy">
          <template #icon><Copy class="size-3.5" /></template>
          Copy caption
        </AppButton>
        <div class="flex items-center gap-2">
          <AppButton variant="secondary" size="sm" :loading="isGeneratingAlternative" @click="handleGenerateAlternative">
            <template #icon><Sparkles class="size-3.5" /></template>
            Generate alternative
          </AppButton>
          <AppButton variant="primary" size="sm" :disabled="!isDirty" :loading="isSaving" @click="handleSave">
            Save changes
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>
