<script setup lang="ts">
import WorkspaceLayout from '@/components/layout/WorkspaceLayout.vue'
import ToastContainer from '@/components/shared/ToastContainer.vue'
import ConfirmDialog from '@/components/shared/ConfirmDialog.vue'
import AssetPreviewModal from '@/components/assets/AssetPreviewModal.vue'
</script>

<template>
  <div class="h-screen bg-[var(--color-canvas)]">
    <WorkspaceLayout />
    <ToastContainer />
    <ConfirmDialog />
    <AssetPreviewModal />
  </div>
</template>
