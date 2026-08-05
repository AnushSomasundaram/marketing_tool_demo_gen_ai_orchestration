<script setup lang="ts">
import { Sparkles } from '@lucide/vue'
import { useCampaignStore } from '@/stores/campaignStore'
import AppButton from '@/components/shared/AppButton.vue'

const campaignStore = useCampaignStore()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <AppButton
      variant="primary"
      size="lg"
      full-width
      :disabled="!campaignStore.canGenerate"
      :loading="campaignStore.isGeneratingCampaign"
      @click="campaignStore.generateCampaign"
    >
      <template #icon>
        <Sparkles class="size-4" />
      </template>
      {{ campaignStore.isGeneratingCampaign ? 'Generating campaign…' : 'Generate Campaign' }}
    </AppButton>
    <p v-if="!campaignStore.productImage" class="text-center text-xs text-[var(--color-ink-faint)]">
      Upload a product image to get started
    </p>
    <p v-else-if="!campaignStore.productForm.productDescription.trim()" class="text-center text-xs text-[var(--color-ink-faint)]">
      Add a product description to continue
    </p>
  </div>
</template>
