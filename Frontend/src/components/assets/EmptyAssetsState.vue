<script setup lang="ts">
import { ImageIcon } from '@lucide/vue'
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-16 text-center">
    <div class="flex size-12 items-center justify-center rounded-full bg-[var(--color-accent-soft)]">
      <ImageIcon class="size-6 text-[var(--color-ink-faint)]" />
    </div>
    <div>
      <p class="text-sm font-medium text-[var(--color-ink)]">No campaign generated yet</p>
      <p class="mt-1 max-w-xs text-xs text-[var(--color-ink-faint)]">
        Upload a product image and describe your product on the left, then generate a campaign to see posts, videos, and captions here.
      </p>
    </div>
  </div>
</template>
