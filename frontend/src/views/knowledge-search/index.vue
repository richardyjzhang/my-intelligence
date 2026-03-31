<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NCard,
  NButton,
  NIcon,
  NInput,
  NSpace,
  NTag,
  NEmpty,
  NSpin,
  NDivider,
  useMessage,
} from 'naive-ui'
import { SearchOutline, DocumentTextOutline, CutOutline } from '@vicons/ionicons5'
import { search } from '@/api/search'
import type { DocumentSearchResult, FragmentSearchResult } from '@/api/search'
import { useTagData } from '@/composables/useTagData'
import TagSelect from '../knowledge/components/TagSelect.vue'

const message = useMessage()
const { allTags } = useTagData()

const keyword = ref('')
const filterTagIds = ref<number[]>([])
const loading = ref(false)
const searched = ref(false)
const documents = ref<DocumentSearchResult[]>([])
const fragments = ref<FragmentSearchResult[]>([])

const hasResults = computed(() => documents.value.length > 0 || fragments.value.length > 0)

function getTagColor(tagName: string) {
  const tag = allTags.value.find((t) => t.name === tagName)
  return tag ? tag.color : '#86909c'
}

async function handleSearch() {
  const kw = keyword.value.trim()
  if (!kw) {
    message.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  searched.value = true
  try {
    const res = await search(
      kw,
      filterTagIds.value.length > 0 ? filterTagIds.value : undefined,
    )
    if (res.code === 200) {
      documents.value = res.data.documents || []
      fragments.value = res.data.fragments || []
    }
  } catch {
    message.error('检索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <NCard class="page-card">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <NSpace align="center" :wrap="false">
        <NInput
          v-model:value="keyword"
          placeholder="输入关键词检索知识..."
          clearable
          style="width: 360px"
          @keydown.enter="handleSearch"
        />
        <TagSelect
          v-model="filterTagIds"
          placeholder="按标签筛选"
          style="min-width: 200px; max-width: 400px"
        />
        <NButton type="primary" @click="handleSearch" :loading="loading">
          <template #icon><NIcon :component="SearchOutline" /></template>
          搜索
        </NButton>
      </NSpace>
    </div>

    <NSpin :show="loading">
      <!-- 未搜索状态 -->
      <div v-if="!searched" class="search-guide">
        <NIcon :component="SearchOutline" :size="48" style="color: #c9cdd4" />
        <p class="search-guide__title">知识检索</p>
        <p class="search-guide__desc">输入关键词，从文档和碎片知识中快速查找相关内容</p>
      </div>

      <!-- 搜索无结果 -->
      <div v-else-if="!loading && !hasResults" style="padding: 80px 0">
        <NEmpty description="未找到匹配内容，试试其他关键词" />
      </div>

      <!-- 搜索结果 -->
      <div v-else-if="!loading" class="search-results">
        <!-- 文档结果 -->
        <div v-if="documents.length > 0" class="result-section">
          <div class="result-section__header">
            <NIcon :component="DocumentTextOutline" :size="18" />
            <span>文档知识</span>
            <NTag size="small" round>{{ documents.length }}</NTag>
          </div>
          <div class="result-list">
            <div v-for="doc in documents" :key="doc.documentId" class="result-card">
              <div class="result-card__header">
                <span
                  v-if="doc.titleHighlight"
                  class="result-card__title"
                  v-html="doc.titleHighlight"
                />
                <span v-else class="result-card__title">{{ doc.title }}</span>
                <span class="result-card__file">{{ doc.fileName }}</span>
              </div>
              <div
                v-if="doc.contentHighlights && doc.contentHighlights.length > 0"
                class="result-card__highlights"
              >
                <div
                  v-for="(hl, idx) in doc.contentHighlights"
                  :key="idx"
                  class="result-card__highlight-item"
                  v-html="'...' + hl + '...'"
                />
              </div>
              <NSpace v-if="doc.tags && doc.tags.length > 0" size="small" style="margin-top: 8px">
                <NTag
                  v-for="tagName in doc.tags"
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
              </NSpace>
            </div>
          </div>
        </div>

        <NDivider v-if="documents.length > 0 && fragments.length > 0" />

        <!-- 碎片结果 -->
        <div v-if="fragments.length > 0" class="result-section">
          <div class="result-section__header">
            <NIcon :component="CutOutline" :size="18" />
            <span>碎片知识</span>
            <NTag size="small" round>{{ fragments.length }}</NTag>
          </div>
          <div class="result-list">
            <div v-for="frag in fragments" :key="frag.fragmentId" class="result-card">
              <div class="result-card__header">
                <span class="result-card__title">{{ frag.title }}</span>
              </div>
              <div v-if="frag.content" class="result-card__content">
                {{ frag.content }}
              </div>
              <NSpace
                v-if="frag.tags && frag.tags.length > 0"
                size="small"
                style="margin-top: 8px"
              >
                <NTag
                  v-for="tagName in frag.tags"
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
              </NSpace>
            </div>
          </div>
        </div>
      </div>
    </NSpin>
  </NCard>
</template>

<style scoped>
.search-bar {
  margin-bottom: 24px;
}

.search-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  gap: 8px;
}

.search-guide__title {
  margin: 8px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
}

.search-guide__desc {
  margin: 0;
  font-size: 14px;
  color: #86909c;
}

.search-results {
  padding-top: 8px;
}

.result-section__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
  transition: background 0.2s;
}

.result-card:hover {
  background: #f2f3f5;
}

.result-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-card__title {
  font-size: 15px;
  font-weight: 500;
  color: #1d2129;
}

.result-card__title :deep(mark) {
  background: #fff3b0;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.result-card__file {
  font-size: 12px;
  color: #86909c;
  flex-shrink: 0;
}

.result-card__highlights {
  margin-top: 8px;
}

.result-card__highlight-item {
  font-size: 13px;
  line-height: 1.8;
  color: #4e5969;
  padding: 4px 0;
}

.result-card__highlight-item + .result-card__highlight-item {
  border-top: 1px dashed #e5e6eb;
}

.result-card__highlight-item :deep(mark) {
  background: #fff3b0;
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

.result-card__content {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.8;
  color: #4e5969;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
