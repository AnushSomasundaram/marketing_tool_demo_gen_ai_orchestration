<script setup lang="ts">
import ProductImageUploader from '@/components/campaign/ProductImageUploader.vue'
import ProductDetailsForm from '@/components/campaign/ProductDetailsForm.vue'
import GenerateCampaignButton from '@/components/campaign/GenerateCampaignButton.vue'
import CampaignChat from '@/components/chat/CampaignChat.vue'
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-[var(--color-panel)]">
    <div class="max-h-[48%] shrink-0 overflow-y-auto border-b border-[var(--color-border-subtle)] p-4">
      <div class="flex flex-col gap-4">
        <ProductImageUploader />
        <ProductDetailsForm />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col">
      <CampaignChat />
    </div>

    <div class="shrink-0 border-t border-[var(--color-border-subtle)] p-3">
      <GenerateCampaignButton />
    </div>
  </div>
</template>
