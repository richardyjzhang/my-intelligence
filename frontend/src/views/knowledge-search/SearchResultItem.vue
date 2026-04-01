<script setup lang="ts">
import { NIcon, NTag } from 'naive-ui'
import { DocumentTextOutline, CutOutline } from '@vicons/ionicons5'
import type { DocumentSearchResult, FragmentSearchResult } from '@/api/search'
import { useTagData } from '@/composables/useTagData'

type SearchItem =
  | { type: 'document'; data: DocumentSearchResult }
  | { type: 'fragment'; data: FragmentSearchResult }

defineProps<{
  item: SearchItem
  selected: boolean
}>()

defineEmits<{
  (e: 'select'): void
}>()

const { allTags } = useTagData()

function getTagColor(tagName: string) {
  const tag = allTags.value.find((t) => t.name === tagName)
  return tag ? tag.color : '#86909c'
}
</script>

<template>
  <div
    class="result-item"
    :class="{ 'result-item--selected': selected }"
    @click="$emit('select')"
  >
    <div class="result-item__title-row">
      <span
        v-if="item.type === 'document' && (item.data as DocumentSearchResult).titleHighlight"
        class="result-item__title"
        v-html="(item.data as DocumentSearchResult).titleHighlight"
      />
      <span
        v-else-if="item.type === 'fragment' && (item.data as FragmentSearchResult).titleHighlight"
        class="result-item__title"
        v-html="(item.data as FragmentSearchResult).titleHighlight"
      />
      <span v-else class="result-item__title">
        {{ item.type === 'document' ? (item.data as DocumentSearchResult).title : (item.data as FragmentSearchResult).title }}
      </span>
    </div>

    <div class="result-item__breadcrumb">
      <NIcon
        :component="item.type === 'document' ? DocumentTextOutline : CutOutline"
        :size="14"
      />
      <span>{{ item.type === 'document' ? '文档知识' : '碎片知识' }}</span>
      <template v-if="item.type === 'document' && (item.data as DocumentSearchResult).fileName">
        <span class="result-item__sep">›</span>
        <span class="result-item__filename">{{ (item.data as DocumentSearchResult).fileName }}</span>
      </template>
    </div>

    <div
      v-if="item.type === 'document' && (item.data as DocumentSearchResult).contentHighlights?.length"
      class="result-item__snippet"
      v-html="(item.data as DocumentSearchResult).contentHighlights![0]"
    />
    <div
      v-else-if="item.type === 'fragment' && (item.data as FragmentSearchResult).contentHighlight"
      class="result-item__snippet"
      v-html="(item.data as FragmentSearchResult).contentHighlight"
    />

    <div
      v-if="(item.type === 'document' ? (item.data as DocumentSearchResult).tags : (item.data as FragmentSearchResult).tags)?.length"
      class="result-item__tags"
    >
      <NTag
        v-for="tagName in (item.type === 'document' ? (item.data as DocumentSearchResult).tags : (item.data as FragmentSearchResult).tags)"
        :key="tagName"
        size="tiny"
        round
        :color="{
          color: getTagColor(tagName) + '1A',
          textColor: getTagColor(tagName),
          borderColor: getTagColor(tagName),
        }"
      >
        {{ tagName }}
      </NTag>
    </div>
  </div>
</template>

<style scoped>
.result-item {
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.result-item:hover {
  background: #f7f8fa;
}

.result-item--selected {
  background: var(--primary-bg, rgba(0, 142, 170, 0.05));
}

.result-item--selected:hover {
  background: var(--primary-bg-hover, rgba(0, 142, 170, 0.08));
}

.result-item__breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909c;
  margin-bottom: 2px;
}

.result-item__sep {
  margin: 0 2px;
  color: #c0c4cc;
}

.result-item__filename {
  color: #86909c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-item__title-row {
  margin-bottom: 2px;
}

.result-item__title {
  font-size: 18px;
  font-weight: 500;
  color: var(--primary-color, #008eaa);
  line-height: 1.4;
}

.result-item__title :deep(mark) {
  background: none;
  color: inherit;
  font-weight: 700;
  text-decoration: underline;
  text-decoration-color: var(--primary-color-60, rgba(0, 142, 170, 0.38));
  text-underline-offset: 2px;
}

.result-item__snippet {
  font-size: 13px;
  line-height: 1.6;
  color: #4e5969;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.result-item__snippet :deep(mark) {
  background: transparent;
  color: #1d2129;
  font-weight: 600;
}

.result-item__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}
</style>
