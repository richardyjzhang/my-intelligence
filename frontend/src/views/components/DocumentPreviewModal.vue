<script setup lang="ts">
import { NModal } from 'naive-ui'

defineProps<{
  show: boolean
  title: string
  url: string
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
}>()
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="title"
    style="width: 90vw; height: 90vh"
    @update:show="emit('update:show', $event)"
  >
    <iframe
      :src="url"
      style="width: 100%; height: calc(90vh - 120px); border: none; border-radius: 4px"
    />
  </NModal>
</template>
