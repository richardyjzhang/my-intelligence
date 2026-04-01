<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import {
  NButton,
  NIcon,
  NTag,
  NEmpty,
  NSpin,
  NPopover,
  NCheckbox,
  NBadge,
  useMessage,
  useThemeVars,
} from 'naive-ui'
import { SearchOutline, PricetagsOutline } from '@vicons/ionicons5'
import { search } from '@/api/search'
import type { DocumentSearchResult, FragmentSearchResult } from '@/api/search'
import { useTagData } from '@/composables/useTagData'
import SearchResultItem from './SearchResultItem.vue'
import SearchPreviewPanel from './SearchPreviewPanel.vue'

type SearchItem =
  | { type: 'document'; data: DocumentSearchResult }
  | { type: 'fragment'; data: FragmentSearchResult }

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
const selectedItem = ref<SearchItem | null>(null)

const mergedResults = computed<SearchItem[]>(() => {
  const items: SearchItem[] = []
  for (const doc of documents.value) {
    items.push({ type: 'document', data: doc })
  }
  for (const frag of fragments.value) {
    items.push({ type: 'fragment', data: frag })
  }
  return items
})

const hasResults = computed(() => mergedResults.value.length > 0)
const totalCount = computed(() => mergedResults.value.length)
const selectedTagCount = computed(() => filterTagIds.value.length)

function getItemId(item: SearchItem) {
  return item.type === 'document'
    ? `doc-${(item.data as DocumentSearchResult).documentId}`
    : `frag-${(item.data as FragmentSearchResult).fragmentId}`
}

function isSelected(item: SearchItem) {
  if (!selectedItem.value) return false
  return getItemId(item) === getItemId(selectedItem.value)
}

function toggleTag(id: number) {
  const idx = filterTagIds.value.indexOf(id)
  if (idx >= 0) filterTagIds.value.splice(idx, 1)
  else filterTagIds.value.push(id)
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
  selectedItem.value = null
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
  selectedItem.value = null
}

function handleInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleSearch()
}

function selectItem(item: SearchItem) {
  selectedItem.value = item
}

function closePreview() {
  selectedItem.value = null
}

watch(searched, (val) => {
  if (!val) closePreview()
})
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

    <!-- 结果态 -->
    <div v-if="searched" class="search-card">
      <div class="topbar">
        <span class="topbar__brand" :style="{ color: themeVars.primaryColor }" @click="handleReset">
          拾知
        </span>
        <div class="search-box search-box--sm">
          <NIcon :component="SearchOutline" :size="16" class="search-box__prefix" />
          <input
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

      <div class="results-body">
        <div ref="resultRef" class="results-panel">
          <NSpin :show="loading" style="min-height: 200px">
            <div v-if="!loading && !hasResults" class="no-results">
              <NEmpty description="未找到匹配内容，试试其他关键词" />
            </div>
            <div v-else-if="!loading" class="results">
              <p class="results__summary">
                找到 <strong>{{ totalCount }}</strong> 条相关结果
              </p>
              <div class="result-list">
                <SearchResultItem
                  v-for="item in mergedResults"
                  :key="getItemId(item)"
                  :item="item"
                  :selected="isSelected(item)"
                  :style="{
                    '--primary-color': themeVars.primaryColor,
                    '--primary-color-60': themeVars.primaryColor + '60',
                    '--primary-bg': themeVars.primaryColor + '0D',
                    '--primary-bg-hover': themeVars.primaryColor + '14',
                  }"
                  @select="selectItem(item)"
                />
              </div>
            </div>
          </NSpin>
        </div>

        <SearchPreviewPanel
          v-if="selectedItem"
          :item="selectedItem"
          @close="closePreview"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: calc(100vh - 10rem);
  display: flex;
  flex-direction: column;
}

.search-page--has-results {
  height: calc(100vh - 10rem);
  max-height: calc(100vh - 10rem);
  overflow: hidden;
}

.search-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--n-border-color, #e5e6eb);
  border-radius: 0 0.5rem 0.5rem 0.5rem;
}

/* ===== Hero ===== */
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

/* ===== 搜索框 ===== */
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

/* ===== 顶部搜索栏 ===== */
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

/* ===== 结果主体 ===== */
.results-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.results-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 20px 24px 40px;
}

.no-results {
  padding: 80px 0;
}

.results {
  max-width: 680px;
}

.results__summary {
  margin: 0 0 16px;
  font-size: 13px;
  color: #86909c;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
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
