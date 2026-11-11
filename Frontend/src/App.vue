<script setup lang="ts">
import AccessGate from '@/components/shared/AccessGate.vue'
</script>

<template>
  <AccessGate>
    <RouterView />
  </AccessGate>
</template>
