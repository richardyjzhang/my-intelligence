<script setup lang="ts">
import { h } from 'vue'
import { NSelect, NTag } from 'naive-ui'
import { useTagData } from '@/composables/useTagData'

const model = defineModel<number[]>({ required: true })

defineProps<{
  placeholder?: string
  clearable?: boolean
  multiple?: boolean
  style?: string | Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'update:value', value: number[]): void
}>()

const { allTags, tagOptions } = useTagData()

function renderTag({ option, handleClose }: any) {
  const tag = allTags.value.find((t) => t.id === option.value)
  return h(
    NTag,
    {
      closable: true,
      onClose: handleClose,
      size: 'tiny',
      round: true,
      style: { fontSize: '12px' },
      color: tag
        ? { color: tag.color + '1A', textColor: tag.color, borderColor: tag.color }
        : undefined,
    },
    { default: () => option.label },
  )
}

function renderLabel(option: any) {
  const tag = allTags.value.find((t) => t.id === option.value)
  return h(
    NTag,
    {
      size: 'small',
      round: true,
      style: { fontSize: '12px' },
      color: tag
        ? { color: tag.color + '1A', textColor: tag.color, borderColor: tag.color }
        : undefined,
    },
    { default: () => option.label },
  )
}

function handleUpdate(val: number[]) {
  model.value = val
  emit('update:value', val)
}
</script>

<template>
  <NSelect
    :value="model"
    :options="tagOptions"
    :placeholder="placeholder ?? '选择标签'"
    :multiple="multiple ?? true"
    :clearable="clearable ?? true"
    :render-tag="renderTag"
    :render-label="renderLabel"
    :style="style"
    @update:value="handleUpdate"
  />
</template>
