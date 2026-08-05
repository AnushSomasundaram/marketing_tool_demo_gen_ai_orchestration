<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useUiStore } from '@/stores/uiStore'
import AppButton from './AppButton.vue'

const uiStore = useUiStore()
const isConfirming = ref(false)

async function handleConfirm() {
  isConfirming.value = true
  try {
    await uiStore.confirmDialogAccept()
  } finally {
    isConfirming.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && uiStore.confirmDialog?.isOpen) {
    uiStore.closeConfirmDialog()
  }
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <Transition name="dialog">
    <div
      v-if="uiStore.confirmDialog?.isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      role="dialog"
      aria-modal="true"
      :aria-label="uiStore.confirmDialog.title"
      @click.self="uiStore.closeConfirmDialog()"
    >
      <div class="w-full max-w-sm rounded-2xl border border-[var(--color-border-subtle)] bg-white p-5 shadow-[var(--shadow-float)] animate-slide-up">
        <h2 class="text-base font-semibold text-[var(--color-ink)]">{{ uiStore.confirmDialog.title }}</h2>
        <p class="mt-1.5 text-sm text-[var(--color-ink-muted)]">{{ uiStore.confirmDialog.message }}</p>
        <div class="mt-5 flex justify-end gap-2">
          <AppButton variant="ghost" @click="uiStore.closeConfirmDialog()">
            {{ uiStore.confirmDialog.cancelLabel ?? 'Cancel' }}
          </AppButton>
          <AppButton
            :variant="uiStore.confirmDialog.danger ? 'danger' : 'primary'"
            :loading="isConfirming"
            @click="handleConfirm"
          >
            {{ uiStore.confirmDialog.confirmLabel ?? 'Confirm' }}
          </AppButton>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}
</style>
