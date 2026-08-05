<script setup lang="ts">
import { ref } from 'vue'
import { Image as ImageIcon, RefreshCw, UploadCloud, X } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import { ACCEPTED_IMAGE_TYPES } from '@/services/uploadService'
import ProgressBar from '@/components/shared/ProgressBar.vue'

const campaignStore = useCampaignStore()
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDraggingOver = ref(false)

function openFilePicker() {
  fileInputRef.value?.click()
}

function handleFileInput(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) campaignStore.setProductImage(file)
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function handleDrop(event: DragEvent) {
  isDraggingOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) campaignStore.setProductImage(file)
}
</script>

<template>
  <div>
    <input
      ref="fileInputRef"
      type="file"
      :accept="ACCEPTED_IMAGE_TYPES.join(',')"
      class="hidden"
      aria-hidden="true"
      tabindex="-1"
      @change="handleFileInput"
    />

    <div
      v-if="!campaignStore.productImage"
      role="button"
      tabindex="0"
      aria-label="Upload product image"
      class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors"
      :class="
        isDraggingOver
          ? 'border-[var(--color-ink)] bg-[var(--color-accent-soft)]'
          : 'border-[var(--color-border-strong)] hover:border-[var(--color-ink-faint)] hover:bg-[var(--color-accent-soft)]/50'
      "
      @click="openFilePicker"
      @keydown.enter="openFilePicker"
      @keydown.space.prevent="openFilePicker"
      @dragover.prevent="isDraggingOver = true"
      @dragleave.prevent="isDraggingOver = false"
      @drop.prevent="handleDrop"
    >
      <div class="flex size-10 items-center justify-center rounded-full bg-white shadow-[var(--shadow-panel)]">
        <UploadCloud class="size-5 text-[var(--color-ink-muted)]" />
      </div>
      <p class="text-sm font-medium text-[var(--color-ink)]">Drop your product image here</p>
      <p class="text-xs text-[var(--color-ink-faint)]">or click to browse — JPG, PNG, or WebP, up to 10MB</p>
    </div>

    <div v-else class="relative overflow-hidden rounded-xl border border-[var(--color-border-subtle)] bg-white">
      <img :src="campaignStore.productImage.previewUrl" alt="Product preview" class="h-48 w-full object-cover" />

      <div v-if="campaignStore.isUploadingImage" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/90 px-6">
        <ImageIcon class="size-5 animate-pulse text-[var(--color-ink-muted)]" />
        <ProgressBar :percent="campaignStore.uploadProgress" label="Uploading" class="w-full max-w-[200px]" />
      </div>

      <div v-else class="absolute inset-x-0 bottom-0 flex justify-end gap-1.5 bg-gradient-to-t from-black/50 to-transparent p-2">
        <button
          type="button"
          class="flex items-center gap-1 rounded-lg bg-white/95 px-2.5 py-1.5 text-xs font-medium text-[var(--color-ink)] hover:bg-white"
          @click="openFilePicker"
        >
          <RefreshCw class="size-3.5" /> Replace
        </button>
        <button
          type="button"
          class="flex items-center gap-1 rounded-lg bg-white/95 px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-white"
          @click="campaignStore.removeProductImage"
        >
          <X class="size-3.5" /> Remove
        </button>
      </div>
    </div>

    <p v-if="campaignStore.uploadError" class="mt-1.5 text-xs text-red-600">{{ campaignStore.uploadError }}</p>
  </div>
</template>
