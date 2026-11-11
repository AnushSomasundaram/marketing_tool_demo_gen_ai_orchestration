<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient, isMockMode } from '@/services/api'
import { getStoredAccessCode, setStoredAccessCode } from '@/services/accessCode'

// Probes a real endpoint rather than assuming: if the backend has no
// ACCESS_CODE configured (e.g. local dev), this always succeeds and the
// gate never shows, regardless of whether a code is stored.
const status = ref<'checking' | 'locked' | 'open'>('checking')
const codeInput = ref('')
const error = ref('')
const isSubmitting = ref(false)

async function probe(): Promise<boolean> {
  try {
    await apiClient.get('/campaigns')
    return true
  } catch {
    return false
  }
}

onMounted(async () => {
  if (isMockMode) {
    status.value = 'open'
    return
  }
  status.value = (await probe()) ? 'open' : 'locked'
})

async function handleSubmit() {
  if (!codeInput.value.trim() || isSubmitting.value) return
  isSubmitting.value = true
  error.value = ''
  setStoredAccessCode(codeInput.value.trim())
  const ok = await probe()
  isSubmitting.value = false
  if (ok) {
    status.value = 'open'
  } else {
    error.value = 'That code doesn\'t match. Try again.'
  }
}
</script>

<template>
  <div v-if="status === 'checking'" class="flex h-screen items-center justify-center bg-[var(--color-accent-soft)]" />

  <div v-else-if="status === 'locked'" class="flex h-screen items-center justify-center bg-[var(--color-accent-soft)] px-4">
    <form
      class="w-full max-w-sm rounded-2xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-[var(--shadow-float)]"
      @submit.prevent="handleSubmit"
    >
      <h1 class="text-base font-semibold text-[var(--color-ink)]">Campaign Studio</h1>
      <p class="mt-1 text-sm text-[var(--color-ink-muted)]">Enter the access code to continue.</p>
      <input
        v-model="codeInput"
        type="password"
        autofocus
        placeholder="Access code"
        class="mt-4 h-10 w-full rounded-lg border border-[var(--color-border-subtle)] px-3 text-sm text-[var(--color-ink)] focus:border-[var(--color-ink)] focus:outline-none"
      />
      <p v-if="error" class="mt-2 text-xs text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="isSubmitting || !codeInput.trim()"
        class="mt-4 h-10 w-full rounded-lg bg-[var(--color-ink)] text-sm font-medium text-white disabled:opacity-60"
      >
        {{ isSubmitting ? 'Checking…' : 'Continue' }}
      </button>
    </form>
  </div>

  <slot v-else />
</template>
