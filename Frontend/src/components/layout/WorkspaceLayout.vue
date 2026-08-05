<script setup lang="ts">
import { useUiStore } from '@/stores/uiStore'
import AppHeader from './AppHeader.vue'
import LeftPanel from './LeftPanel.vue'
import RightPanel from './RightPanel.vue'

const uiStore = useUiStore()
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden">
    <AppHeader />

    <div class="flex shrink-0 border-b border-[var(--color-border-subtle)] bg-white md:hidden">
      <button
        type="button"
        class="flex-1 border-b-2 py-2.5 text-sm font-medium transition-colors"
        :class="uiStore.mobileTab === 'create' ? 'border-[var(--color-ink)] text-[var(--color-ink)]' : 'border-transparent text-[var(--color-ink-faint)]'"
        @click="uiStore.setMobileTab('create')"
      >
        Create
      </button>
      <button
        type="button"
        class="flex-1 border-b-2 py-2.5 text-sm font-medium transition-colors"
        :class="uiStore.mobileTab === 'results' ? 'border-[var(--color-ink)] text-[var(--color-ink)]' : 'border-transparent text-[var(--color-ink-faint)]'"
        @click="uiStore.setMobileTab('results')"
      >
        Results
      </button>
    </div>

    <div class="flex min-h-0 flex-1 flex-col lg:flex-row">
      <div
        class="min-h-0 flex-col md:flex md:flex-1 lg:flex-none lg:w-[38%]"
        :class="uiStore.mobileTab === 'create' ? 'flex' : 'hidden'"
      >
        <LeftPanel />
      </div>
      <div class="hidden w-px shrink-0 bg-[var(--color-border-subtle)] lg:block" />
      <div
        class="min-h-0 flex-col md:flex md:flex-1 lg:flex-none lg:w-[62%]"
        :class="uiStore.mobileTab === 'results' ? 'flex' : 'hidden'"
      >
        <RightPanel />
      </div>
    </div>
  </div>
</template>
