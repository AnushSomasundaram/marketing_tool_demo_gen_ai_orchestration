<script setup lang="ts">
import { computed, ref } from 'vue'
import { AlertTriangle, Pause, Play, Sparkles } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import type { CampaignAsset } from '@/types/campaign'
import AssetToolbar from './AssetToolbar.vue'
import ProgressBar from '@/components/shared/ProgressBar.vue'

const props = defineProps<{ asset: CampaignAsset; selected: boolean }>()
const campaignStore = useCampaignStore()

const emit = defineEmits<{
  select: []
  preview: []
  regenerate: []
  download: []
  delete: []
  refine: []
}>()

const isBusy = computed(() => props.asset.status === 'processing' || props.asset.status === 'queued')

// Mock mode has no real video file (its downloadUrl is just another image), so
// a <video> element can't play it — fall back to a simple simulated preview
// in that case. Against the real backend, downloadUrl is an actual mp4 and
// plays for real.
const videoRef = ref<HTMLVideoElement | null>(null)
const videoUnplayable = ref(false)
const isPlaying = ref(false)
const elapsed = ref(0)
let simulatedTimer: ReturnType<typeof setInterval> | null = null

const canPlayRealVideo = computed(
  () => Boolean(props.asset.downloadUrl) && !videoUnplayable.value,
)

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function stopSimulatedPlayback() {
  if (simulatedTimer) {
    clearInterval(simulatedTimer)
    simulatedTimer = null
  }
}

function toggleSimulatedPlayback() {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    simulatedTimer = setInterval(() => {
      elapsed.value += 0.25
      if (elapsed.value >= (props.asset.duration ?? 0)) {
        isPlaying.value = false
        elapsed.value = 0
        stopSimulatedPlayback()
      }
    }, 250)
  } else {
    stopSimulatedPlayback()
  }
}

function togglePlayback() {
  if (props.asset.status !== 'completed') return

  if (!canPlayRealVideo.value) {
    toggleSimulatedPlayback()
    return
  }

  const video = videoRef.value
  if (!video) return
  if (isPlaying.value) video.pause()
  else video.play()
}

function handleVideoError() {
  videoUnplayable.value = true
}

function handlePlay() {
  isPlaying.value = true
}

function handlePauseOrEnd() {
  isPlaying.value = false
}

function handleTimeUpdate() {
  if (videoRef.value) elapsed.value = videoRef.value.currentTime
}
</script>

<template>
  <div
    role="button"
    tabindex="0"
    class="group relative flex flex-col overflow-hidden rounded-xl border bg-white transition-shadow"
    :class="selected ? 'border-[var(--color-ink)] shadow-[var(--shadow-float)]' : 'border-[var(--color-border-subtle)] hover:shadow-[var(--shadow-panel)]'"
    @click="emit('select')"
    @keydown.enter="emit('select')"
  >
    <div class="relative aspect-[9/16] w-full overflow-hidden bg-[var(--color-accent-soft)]">
      <video
        v-if="asset.status === 'completed' && canPlayRealVideo"
        ref="videoRef"
        :src="asset.downloadUrl ?? undefined"
        :poster="asset.previewUrl ?? undefined"
        class="h-full w-full object-cover"
        playsinline
        preload="metadata"
        @play="handlePlay"
        @pause="handlePauseOrEnd"
        @ended="handlePauseOrEnd"
        @timeupdate="handleTimeUpdate"
        @error="handleVideoError"
      />
      <img
        v-else
        :src="asset.previewUrl ?? undefined"
        :alt="asset.title"
        class="h-full w-full object-cover"
        :class="isBusy ? 'opacity-40' : ''"
      />

      <div v-if="isBusy" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/60 px-6">
        <span class="text-xs font-medium text-[var(--color-ink-muted)]">Rendering video…</span>
        <ProgressBar :percent="asset.progress ?? 0" class="w-full" />
      </div>

      <div v-else-if="asset.status === 'failed'" class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/85 px-4 text-center">
        <AlertTriangle class="size-5 text-red-500" />
        <p class="text-xs text-[var(--color-ink-muted)]">{{ asset.errorMessage ?? 'Video processing failed' }}</p>
        <button type="button" class="rounded-lg bg-[var(--color-ink)] px-2.5 py-1 text-xs font-medium text-white" @click.stop="emit('regenerate')">
          Retry
        </button>
      </div>

      <template v-else>
        <button
          v-if="!isPlaying"
          type="button"
          class="absolute inset-0 flex items-center justify-center"
          aria-label="Play preview"
          @click.stop="togglePlayback"
        >
          <span class="flex size-11 items-center justify-center rounded-full bg-white/90 text-[var(--color-ink)] shadow-[var(--shadow-panel)] transition-transform group-hover:scale-105">
            <Play class="ml-0.5 size-5" />
          </span>
        </button>
        <button
          v-else
          type="button"
          class="absolute bottom-2 right-2 flex size-8 items-center justify-center rounded-full bg-black/60 text-white"
          aria-label="Pause preview"
          @click.stop="togglePlayback"
        >
          <Pause class="size-4" />
        </button>
        <div class="absolute bottom-2 left-2 rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">
          {{ isPlaying ? formatDuration(elapsed) : '0:00' }} / {{ formatDuration(asset.duration ?? 0) }}
        </div>
      </template>

      <div class="absolute left-2 top-2 flex gap-1.5">
        <span class="rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">{{ asset.aspectRatio }}</span>
        <span class="rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">v{{ asset.version }}</span>
      </div>

      <div class="absolute right-2 top-2 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        <AssetToolbar
          :regenerating="campaignStore.assetIsRegenerating(asset.id)"
          :downloading="campaignStore.assetIsDownloading(asset.id)"
          @preview="emit('preview')"
          @edit="emit('select')"
          @regenerate="emit('regenerate')"
          @download="emit('download')"
          @delete="emit('delete')"
        />
      </div>
    </div>

    <div class="flex items-center justify-between gap-2 p-2.5">
      <p class="truncate text-xs font-medium text-[var(--color-ink)]">{{ asset.title }}</p>
      <button
        type="button"
        class="flex shrink-0 items-center gap-1 rounded-md bg-[var(--color-accent-soft)] px-2 py-1 text-[11px] font-medium text-[var(--color-ink)] hover:bg-[var(--color-border-strong)]/60"
        @click.stop="emit('refine')"
      >
        <Sparkles class="size-3" /> Refine with AI
      </button>
    </div>
  </div>
</template>
