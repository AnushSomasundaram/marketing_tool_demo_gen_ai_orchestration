<script setup lang="ts">
import { Download, Eye, Loader2, Pencil, Trash2 } from '@lucide/vue'

withDefaults(defineProps<{ downloading?: boolean }>(), {
  downloading: false,
})

defineEmits<{
  preview: []
  edit: []
  download: []
  delete: []
}>()
</script>

<template>
  <div class="flex items-center gap-1 rounded-lg bg-black/60 p-1 backdrop-blur-sm">
    <button type="button" title="Preview" aria-label="Preview asset" class="flex size-7 items-center justify-center rounded-md text-white hover:bg-white/20" @click.stop="$emit('preview')">
      <Eye class="size-3.5" />
    </button>
    <button type="button" title="Edit caption" aria-label="Edit caption" class="flex size-7 items-center justify-center rounded-md text-white hover:bg-white/20" @click.stop="$emit('edit')">
      <Pencil class="size-3.5" />
    </button>
    <button
      type="button"
      title="Download"
      aria-label="Download asset"
      class="flex size-7 items-center justify-center rounded-md text-white hover:bg-white/20 disabled:opacity-60"
      :disabled="downloading"
      @click.stop="$emit('download')"
    >
      <Loader2 v-if="downloading" class="size-3.5 animate-spin" />
      <Download v-else class="size-3.5" />
    </button>
    <button type="button" title="Delete" aria-label="Delete asset" class="flex size-7 items-center justify-center rounded-md text-white hover:bg-red-500/80" @click.stop="$emit('delete')">
      <Trash2 class="size-3.5" />
    </button>
  </div>
</template>
