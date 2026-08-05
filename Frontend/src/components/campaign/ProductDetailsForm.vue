<script setup lang="ts">
import { useCampaignStore } from '@/stores/campaignStore'
import { BRAND_TONE_OPTIONS, type BrandTone } from '@/types/campaign'
import AppInput from '@/components/shared/AppInput.vue'
import AppTextarea from '@/components/shared/AppTextarea.vue'
import AppSelect from '@/components/shared/AppSelect.vue'

const campaignStore = useCampaignStore()

const toneOptions = BRAND_TONE_OPTIONS.map((tone) => ({ value: tone.value, label: tone.label }))

function setTone(value: string) {
  campaignStore.productForm.tone = value as BrandTone
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <AppInput v-model="campaignStore.productForm.productName" label="Product name" placeholder="e.g. Aurora Desk Lamp" />

    <AppTextarea
      v-model="campaignStore.productForm.productDescription"
      label="Product description"
      placeholder="Describe the product, its key features, and what makes it stand out…"
      :rows="3"
      required
      hint="Required to generate a campaign"
    />

    <AppInput
      v-model="campaignStore.productForm.targetAudience"
      label="Target audience"
      placeholder="e.g. Design-conscious professionals, ages 25-40"
    />

    <AppSelect
      :model-value="campaignStore.productForm.tone"
      :options="toneOptions"
      label="Brand tone"
      @update:model-value="setTone"
    />

    <div class="grid grid-cols-2 gap-3">
      <AppInput v-model="campaignStore.productForm.price" label="Price" placeholder="$49" />
      <AppInput v-model="campaignStore.productForm.websiteUrl" label="Website URL" placeholder="yourbrand.com" />
    </div>
  </div>
</template>
