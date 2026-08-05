<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ChevronDown, History } from '@lucide/vue'
import type { CaptionVersion } from '@/types/campaign'

const props = defineProps<{ versions: CaptionVersion[] }>()
const emit = defineEmits<{ restore: [version: CaptionVersion] }>()

const isOpen = ref(false)
const rootRef = ref<HTMLDivElement | null>(null)

function handleClickOutside(event: MouseEvent) {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

function restore(version: CaptionVersion) {
  emit('restore', version)
  isOpen.value = false
}
</script>

<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      :disabled="props.versions.length === 0"
      class="flex items-center gap-1.5 rounded-lg border border-[var(--color-border-subtle)] bg-white px-2.5 py-1.5 text-xs font-medium text-[var(--color-ink-muted)] hover:text-[var(--color-ink)] disabled:cursor-not-allowed disabled:opacity-50"
      @click="isOpen = !isOpen"
    >
      <History class="size-3.5" />
      Version history
      <span v-if="props.versions.length" class="rounded-full bg-[var(--color-accent-soft)] px-1.5 text-[10px]">{{ props.versions.length }}</span>
      <ChevronDown class="size-3.5" />
    </button>

    <div
      v-if="isOpen"
      class="absolute right-0 z-20 mt-1 max-h-64 w-72 overflow-y-auto rounded-xl border border-[var(--color-border-subtle)] bg-white py-1 shadow-[var(--shadow-float)]"
    >
      <button
        v-for="version in [...props.versions].reverse()"
        :key="version.id"
        type="button"
        class="flex w-full flex-col gap-0.5 border-b border-[var(--color-border-subtle)] px-3 py-2 text-left last:border-b-0 hover:bg-[var(--color-accent-soft)]"
        @click="restore(version)"
      >
        <span class="text-[11px] text-[var(--color-ink-faint)]">{{ formatTime(version.createdAt) }}</span>
        <span class="line-clamp-2 text-xs text-[var(--color-ink)]">{{ version.caption }}</span>
      </button>
    </div>
  </div>
</template>
