<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import {
  NButton,
  NIcon,
  NTag,
  NEmpty,
  NSpin,
  NDivider,
  NPopover,
  NCheckbox,
  NBadge,
  useMessage,
  useThemeVars,
} from 'naive-ui'
import {
  SearchOutline,
  DocumentTextOutline,
  CutOutline,
  PricetagsOutline,
} from '@vicons/ionicons5'
import { search } from '@/api/search'
import type { DocumentSearchResult, FragmentSearchResult } from '@/api/search'
import { useTagData } from '@/composables/useTagData'

const message = useMessage()
const themeVars = useThemeVars()
const { allTags } = useTagData()

const keyword = ref('')
const filterTagIds = ref<number[]>([])
const loading = ref(false)
const searched = ref(false)
const documents = ref<DocumentSearchResult[]>([])
const fragments = ref<FragmentSearchResult[]>([])
const resultRef = ref<HTMLElement>()
const heroInputRef = ref<HTMLInputElement>()
const topbarInputRef = ref<HTMLInputElement>()

const hasResults = computed(() => documents.value.length > 0 || fragments.value.length > 0)
const totalCount = computed(() => documents.value.length + fragments.value.length)
const selectedTagCount = computed(() => filterTagIds.value.length)

function getTagColor(tagName: string) {
  const tag = allTags.value.find((t) => t.name === tagName)
  return tag ? tag.color : '#86909c'
}

function toggleTag(id: number) {
  const idx = filterTagIds.value.indexOf(id)
  if (idx >= 0) {
    filterTagIds.value.splice(idx, 1)
  } else {
    filterTagIds.value.push(id)
  }
}

function clearTags() {
  filterTagIds.value = []
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
    await nextTick()
    resultRef.value?.scrollTo({ top: 0 })
  }
}

function handleReset() {
  keyword.value = ''
  filterTagIds.value = []
  searched.value = false
  documents.value = []
  fragments.value = []
}

function handleInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    handleSearch()
  }
}
</script>

<template>
  <div class="search-page" :class="{ 'search-page--has-results': searched }">
    <!-- 初始态：居中的搜索首页 -->
    <Transition name="hero-fade">
      <div v-if="!searched" class="hero">
        <h1 class="hero__title" :style="{ color: themeVars.primaryColor }">拾知</h1>
        <p class="hero__subtitle">从文档与碎片知识中，快速检索你需要的内容</p>
        <div class="search-box search-box--lg">
          <NIcon :component="SearchOutline" :size="20" class="search-box__prefix" />
          <input
            ref="heroInputRef"
            v-model="keyword"
            class="search-box__input"
            placeholder="输入关键词开始检索..."
            @keydown="handleInputKeydown"
          />
          <div class="search-box__actions">
            <NPopover trigger="click" placement="bottom-end" :width="240">
              <template #trigger>
                <NBadge :value="selectedTagCount" :show="selectedTagCount > 0" :offset="[-4, 2]">
                  <button class="search-box__icon-btn" title="按标签筛选">
                    <NIcon :component="PricetagsOutline" :size="18" />
                  </button>
                </NBadge>
              </template>
              <div class="tag-popover">
                <div class="tag-popover__header">
                  <span>按标签筛选</span>
                  <NButton text size="tiny" :disabled="selectedTagCount === 0" @click="clearTags">
                    清除
                  </NButton>
                </div>
                <div class="tag-popover__list">
                  <div
                    v-for="tag in allTags"
                    :key="tag.id"
                    class="tag-popover__item"
                    @click="toggleTag(tag.id)"
                  >
                    <NCheckbox :checked="filterTagIds.includes(tag.id)" style="pointer-events: none" />
                    <NTag
                      size="small"
                      round
                      :color="{
                        color: tag.color + '1A',
                        textColor: tag.color,
                        borderColor: tag.color,
                      }"
                    >
                      {{ tag.name }}
                    </NTag>
                  </div>
                  <div v-if="allTags.length === 0" class="tag-popover__empty">暂无标签</div>
                </div>
              </div>
            </NPopover>
            <div class="search-box__divider" />
            <button
              class="search-box__search-btn"
              :style="{ background: themeVars.primaryColor }"
              :disabled="loading"
              @click="handleSearch"
            >
              <NIcon :component="SearchOutline" :size="18" color="#fff" />
            </button>
          </div>
        </div>
        <div v-if="selectedTagCount > 0" class="hero__selected-tags">
          <NTag
            v-for="tagId in filterTagIds"
            :key="tagId"
            size="small"
            round
            closable
            :color="(() => {
              const t = allTags.find(t => t.id === tagId)
              return t ? { color: t.color + '1A', textColor: t.color, borderColor: t.color } : undefined
            })()"
            @close="toggleTag(tagId)"
          >
            {{ allTags.find(t => t.id === tagId)?.name }}
          </NTag>
        </div>
      </div>
    </Transition>

    <!-- 结果态：顶部搜索栏 + 结果列表 -->
    <template v-if="searched">
      <div class="topbar">
        <span class="topbar__brand" :style="{ color: themeVars.primaryColor }" @click="handleReset">
          拾知
        </span>
        <div class="search-box search-box--sm">
          <NIcon :component="SearchOutline" :size="16" class="search-box__prefix" />
          <input
            ref="topbarInputRef"
            v-model="keyword"
            class="search-box__input"
            placeholder="输入关键词检索..."
            @keydown="handleInputKeydown"
          />
          <div class="search-box__actions">
            <NPopover trigger="click" placement="bottom-end" :width="240">
              <template #trigger>
                <NBadge :value="selectedTagCount" :show="selectedTagCount > 0" :offset="[-4, 2]">
                  <button class="search-box__icon-btn" title="按标签筛选">
                    <NIcon :component="PricetagsOutline" :size="16" />
                  </button>
                </NBadge>
              </template>
              <div class="tag-popover">
                <div class="tag-popover__header">
                  <span>按标签筛选</span>
                  <NButton text size="tiny" :disabled="selectedTagCount === 0" @click="clearTags">
                    清除
                  </NButton>
                </div>
                <div class="tag-popover__list">
                  <div
                    v-for="tag in allTags"
                    :key="tag.id"
                    class="tag-popover__item"
                    @click="toggleTag(tag.id)"
                  >
                    <NCheckbox :checked="filterTagIds.includes(tag.id)" style="pointer-events: none" />
                    <NTag
                      size="small"
                      round
                      :color="{
                        color: tag.color + '1A',
                        textColor: tag.color,
                        borderColor: tag.color,
                      }"
                    >
                      {{ tag.name }}
                    </NTag>
                  </div>
                  <div v-if="allTags.length === 0" class="tag-popover__empty">暂无标签</div>
                </div>
              </div>
            </NPopover>
            <div class="search-box__divider" />
            <button
              class="search-box__search-btn search-box__search-btn--sm"
              :style="{ background: themeVars.primaryColor }"
              :disabled="loading"
              @click="handleSearch"
            >
              <NIcon :component="SearchOutline" :size="16" color="#fff" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="selectedTagCount > 0" class="topbar-tags">
        <span class="topbar-tags__label">标签：</span>
        <NTag
          v-for="tagId in filterTagIds"
          :key="tagId"
          size="small"
          round
          closable
          :color="(() => {
            const t = allTags.find(t => t.id === tagId)
            return t ? { color: t.color + '1A', textColor: t.color, borderColor: t.color } : undefined
          })()"
          @close="toggleTag(tagId)"
        >
          {{ allTags.find(t => t.id === tagId)?.name }}
        </NTag>
      </div>

      <div ref="resultRef" class="results-container">
        <NSpin :show="loading" style="min-height: 200px">
          <div v-if="!loading && !hasResults" class="no-results">
            <NEmpty description="未找到匹配内容，试试其他关键词" />
          </div>

          <div v-else-if="!loading" class="results">
            <p class="results__summary">
              找到 <strong>{{ totalCount }}</strong> 条相关结果
            </p>

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
                  <div v-if="doc.tags && doc.tags.length > 0" class="result-card__tags">
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
                  </div>
                </div>
              </div>
            </div>

            <NDivider v-if="documents.length > 0 && fragments.length > 0" />

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
                  <div v-if="frag.tags && frag.tags.length > 0" class="result-card__tags">
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
                  </div>
                </div>
              </div>
            </div>
          </div>
        </NSpin>
      </div>
    </template>
  </div>
</template>

<style scoped>
.search-page {
  min-height: calc(100vh - 10rem);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ===== 初始态：居中 Hero ===== */
.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 24px 140px;
  gap: 4px;
}

.hero__title {
  font-size: 42px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 4px;
  user-select: none;
}

.hero__subtitle {
  margin: 0 0 32px;
  font-size: 15px;
  color: #86909c;
}

.hero__selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  max-width: 580px;
}

/* ===== 搜索框（共用） ===== */
.search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1.5px solid #e5e6eb;
  border-radius: 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box:focus-within {
  border-color: v-bind('themeVars.primaryColor');
  box-shadow: 0 0 0 2px v-bind('themeVars.primaryColor + "20"');
}

.search-box--lg {
  width: 100%;
  max-width: 580px;
  height: 50px;
  padding: 0 6px 0 18px;
  font-size: 16px;
}

.search-box--sm {
  flex: 1;
  max-width: 640px;
  height: 40px;
  padding: 0 4px 0 14px;
  font-size: 14px;
}

.search-box__prefix {
  color: #86909c;
  flex-shrink: 0;
  margin-right: 10px;
}

.search-box__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: inherit;
  color: #1d2129;
  line-height: 1.5;
}

.search-box__input::placeholder {
  color: #c9cdd4;
}

.search-box__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.search-box__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  color: #86909c;
  transition: background 0.15s, color 0.15s;
}

.search-box__icon-btn:hover {
  background: #f2f3f5;
  color: #4e5969;
}

.search-box__divider {
  width: 1px;
  height: 20px;
  background: #e5e6eb;
  margin: 0 2px;
}

.search-box__search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.search-box__search-btn:hover {
  opacity: 0.85;
}

.search-box__search-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-box__search-btn--sm {
  width: 32px;
  height: 32px;
}

/* ===== 标签弹出面板 ===== */
.tag-popover__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #4e5969;
}

.tag-popover__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 240px;
  overflow-y: auto;
}

.tag-popover__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.tag-popover__item:hover {
  background: #f7f8fa;
}

.tag-popover__empty {
  padding: 16px 0;
  text-align: center;
  font-size: 13px;
  color: #c9cdd4;
}

/* ===== 结果态：顶部搜索栏 ===== */
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  border-bottom: 1px solid #e5e6eb;
  background: #fff;
  flex-shrink: 0;
}

.topbar__brand {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
  transition: opacity 0.2s;
}

.topbar__brand:hover {
  opacity: 0.8;
}

.topbar-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
  flex-shrink: 0;
}

.topbar-tags__label {
  font-size: 12px;
  color: #86909c;
  flex-shrink: 0;
}

/* ===== 结果区域 ===== */
.results-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px 40px;
}

.no-results {
  padding: 80px 0;
}

.results {
  max-width: 780px;
}

.results__summary {
  margin: 0 0 20px;
  font-size: 13px;
  color: #86909c;
}

/* ===== 结果区块 ===== */
.result-section__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  padding: 16px 18px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.result-card:hover {
  border-color: #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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

.result-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

/* ===== 过渡动画 ===== */
.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: opacity 0.25s ease;
}

.hero-fade-enter-from,
.hero-fade-leave-to {
  opacity: 0;
}
</style>
