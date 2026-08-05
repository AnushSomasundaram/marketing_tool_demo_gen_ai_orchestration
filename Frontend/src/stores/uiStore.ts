import { ref } from 'vue'
import { defineStore } from 'pinia'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
}

export interface ConfirmDialogOptions {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void | Promise<void>
}

export type MobileTab = 'create' | 'results'

export const useUiStore = defineStore('ui', () => {
  const toasts = ref<Toast[]>([])
  const mobileTab = ref<MobileTab>('create')

  const confirmDialog = ref<(ConfirmDialogOptions & { isOpen: boolean }) | null>(null)
  const previewAssetId = ref<string | null>(null)

  function pushToast(message: string, type: ToastType = 'info', durationMs = 4000) {
    const id = crypto.randomUUID()
    toasts.value.push({ id, type, message })
    if (durationMs > 0) {
      setTimeout(() => dismissToast(id), durationMs)
    }
    return id
  }

  function dismissToast(id: string) {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }

  function openConfirmDialog(options: ConfirmDialogOptions) {
    confirmDialog.value = { ...options, isOpen: true }
  }

  function closeConfirmDialog() {
    confirmDialog.value = null
  }

  async function confirmDialogAccept() {
    if (!confirmDialog.value) return
    await confirmDialog.value.onConfirm()
    closeConfirmDialog()
  }

  function openAssetPreview(assetId: string) {
    previewAssetId.value = assetId
  }

  function closeAssetPreview() {
    previewAssetId.value = null
  }

  function setMobileTab(tab: MobileTab) {
    mobileTab.value = tab
  }

  return {
    toasts,
    mobileTab,
    confirmDialog,
    previewAssetId,
    pushToast,
    dismissToast,
    openConfirmDialog,
    closeConfirmDialog,
    confirmDialogAccept,
    openAssetPreview,
    closeAssetPreview,
    setMobileTab,
  }
})
