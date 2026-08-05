<script setup lang="ts">
import { AlertCircle, CheckCircle2, Info, X } from '@lucide/vue'
import { useUiStore } from '@/stores/uiStore'

const uiStore = useUiStore()

const icons = { success: CheckCircle2, error: AlertCircle, info: Info }
const iconClasses = {
  success: 'text-emerald-600',
  error: 'text-red-600',
  info: 'text-[var(--color-ink-muted)]',
}
</script>

<template>
  <div class="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2" aria-live="polite">
    <TransitionGroup name="toast">
      <div
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-start gap-2.5 rounded-xl border border-[var(--color-border-subtle)] bg-white px-3.5 py-3 shadow-[var(--shadow-float)] animate-slide-up"
      >
        <component :is="icons[toast.type]" class="mt-0.5 size-4 shrink-0" :class="iconClasses[toast.type]" />
        <p class="flex-1 text-sm text-[var(--color-ink)]">{{ toast.message }}</p>
        <button
          type="button"
          class="rounded p-0.5 text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]"
          aria-label="Dismiss notification"
          @click="uiStore.dismissToast(toast.id)"
        >
          <X class="size-3.5" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
</style>
