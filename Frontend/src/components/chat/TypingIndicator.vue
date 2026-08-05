<script setup lang="ts">
import { Sparkles } from '@lucide/vue'
</script>

<template>
  <div class="flex items-center gap-2" role="status" aria-label="Assistant is typing">
    <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-ink)] text-white">
      <Sparkles class="size-3.5" />
    </div>
    <div class="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-[var(--color-accent-soft)] px-3.5 py-3">
      <span
        v-for="i in 3"
        :key="i"
        class="size-1.5 rounded-full bg-[var(--color-ink-faint)] animate-bounce"
        :style="{ animationDelay: `${(i - 1) * 0.15}s` }"
      />
    </div>
  </div>
</template>
