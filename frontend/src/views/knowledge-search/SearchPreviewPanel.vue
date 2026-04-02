<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NButton,
  NIcon,
  NTag,
  NSpin,
  NScrollbar,
  useMessage,
} from 'naive-ui'
import {
  DocumentTextOutline,
  CutOutline,
  CloseOutline,
  EyeOutline,
  DownloadOutline,
  LinkOutline,
  ChatbubblesOutline,
} from '@vicons/ionicons5'
import { getDocument, getPreviewUrl, getDownloadUrl } from '@/api/document'
import type { DocumentInfo } from '@/api/document'
import { getFragment } from '@/api/fragment'
import type { FragmentInfo } from '@/api/fragment'
import type { DocumentSearchResult, FragmentSearchResult } from '@/api/search'
import DocumentPreviewModal from '@/views/components/DocumentPreviewModal.vue'
import { useAiChatStore } from '@/stores/aiChat'

type SearchItem =
  | { type: 'document'; data: DocumentSearchResult }
  | { type: 'fragment'; data: FragmentSearchResult }

const props = defineProps<{
  item: SearchItem
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const message = useMessage()
const aiChatStore = useAiChatStore()
const loading = ref(false)
const doc = ref<DocumentInfo | null>(null)
const fragment = ref<FragmentInfo | null>(null)

const showFilePreview = ref(false)
const filePreviewTitle = ref('')
const filePreviewUrl = ref('')

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr: string) {
  return dateStr ? dateStr.replace('T', ' ').slice(0, 16) : ''
}

function openFilePreview(d: DocumentInfo) {
  filePreviewTitle.value = d.title
  filePreviewUrl.value = getPreviewUrl(d.id)
  showFilePreview.value = true
}

function openDiscuss(d: DocumentInfo) {
  aiChatStore.openDiscussDocument(d.id, d.title)
}

async function loadPreview() {
  loading.value = true
  doc.value = null
  fragment.value = null

  try {
    if (props.item.type === 'document') {
      const res = await getDocument((props.item.data as DocumentSearchResult).documentId)
      if (res.code === 200) doc.value = res.data
    } else {
      const res = await getFragment((props.item.data as FragmentSearchResult).fragmentId)
      if (res.code === 200) fragment.value = res.data
    }
  } catch {
    message.error('加载预览失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.item, () => {
  loadPreview()
}, { immediate: true })
</script>

<template>
  <div class="preview-panel">
    <div class="preview-header">
      <div class="preview-header__info">
        <NIcon
          :component="item.type === 'document' ? DocumentTextOutline : CutOutline"
          :size="16"
        />
        <span>{{ item.type === 'document' ? '文档知识' : '碎片知识' }}</span>
      </div>
      <NButton text size="small" @click="emit('close')">
        <template #icon>
          <NIcon :component="CloseOutline" />
        </template>
      </NButton>
    </div>

    <NSpin :show="loading" style="flex: 1; min-height: 100px">
      <template v-if="doc">
        <NScrollbar style="max-height: calc(100vh - 220px)">
          <div class="preview-content">
            <h2 class="preview-content__title">{{ doc.title }}</h2>

            <div v-if="doc.tags.length > 0" class="preview-tags">
              <NTag
                v-for="tag in doc.tags"
                :key="tag.id"
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

            <div class="preview-meta">
              <div class="preview-meta__row">
                <span class="preview-meta__label">文件</span>
                <span>{{ doc.fileName }}</span>
              </div>
              <div v-if="doc.code" class="preview-meta__row">
                <span class="preview-meta__label">文号</span>
                <span>{{ doc.code }}</span>
              </div>
              <div v-if="doc.publishDate" class="preview-meta__row">
                <span class="preview-meta__label">发布日期</span>
                <span>{{ doc.publishDate }}</span>
              </div>
              <div class="preview-meta__row">
                <span class="preview-meta__label">大小</span>
                <span>{{ formatFileSize(doc.fileSize) }}</span>
              </div>
              <div class="preview-meta__row">
                <span class="preview-meta__label">上传者</span>
                <span>{{ doc.creator.nickname }}</span>
              </div>
              <div class="preview-meta__row">
                <span class="preview-meta__label">创建时间</span>
                <span>{{ formatDate(doc.createTime) }}</span>
              </div>
            </div>

            <div v-if="doc.remark" class="preview-remark">
              <span class="preview-remark__label">备注</span>
              <p>{{ doc.remark }}</p>
            </div>

            <div class="preview-actions preview-actions--tint">
              <NButton size="small" @click="openDiscuss(doc)">
                <template #icon>
                  <NIcon :component="ChatbubblesOutline" />
                </template>
                文档讨论
              </NButton>
              <NButton
                size="small"
                :disabled="!doc.filePath"
                @click="openFilePreview(doc)"
              >
                <template #icon>
                  <NIcon :component="EyeOutline" />
                </template>
                在线预览
              </NButton>
              <NButton
                size="small"
                :disabled="!doc.filePath"
                tag="a"
                :href="doc.filePath ? getDownloadUrl(doc.id) : undefined"
              >
                <template #icon>
                  <NIcon :component="DownloadOutline" />
                </template>
                文档下载
              </NButton>
              <NButton
                size="small"
                :disabled="!doc.url"
                tag="a"
                :href="doc.url || undefined"
                target="_blank"
              >
                <template #icon>
                  <NIcon :component="LinkOutline" />
                </template>
                原文链接
              </NButton>
            </div>
          </div>
        </NScrollbar>
      </template>

      <template v-if="fragment">
        <NScrollbar style="max-height: calc(100vh - 220px)">
          <div class="preview-content">
            <h2 class="preview-content__title">{{ fragment.title }}</h2>

            <div v-if="fragment.tags.length > 0" class="preview-tags">
              <NTag
                v-for="tag in fragment.tags"
                :key="tag.id"
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

            <div class="preview-meta">
              <div class="preview-meta__row">
                <span class="preview-meta__label">创建者</span>
                <span>{{ fragment.creator.nickname }}</span>
              </div>
              <div class="preview-meta__row">
                <span class="preview-meta__label">创建时间</span>
                <span>{{ formatDate(fragment.createTime) }}</span>
              </div>
              <div class="preview-meta__row">
                <span class="preview-meta__label">更新时间</span>
                <span>{{ formatDate(fragment.updateTime) }}</span>
              </div>
            </div>

            <div class="preview-fragment-content">
              {{ fragment.content }}
            </div>
          </div>
        </NScrollbar>
      </template>
    </NSpin>

    <DocumentPreviewModal
      v-model:show="showFilePreview"
      :title="filePreviewTitle"
      :url="filePreviewUrl"
    />
  </div>
</template>

<style scoped>
.preview-panel {
  width: 560px;
  flex-shrink: 0;
  border-left: 1px solid #e5e6eb;
  background: #fafbfc;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eef0f3;
  background: #fff;
  flex-shrink: 0;
}

.preview-header__info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4e5969;
  font-weight: 500;
}

.preview-content {
  padding: 20px 20px 32px;
}

.preview-content__title {
  font-size: 18px;
  font-weight: 600;
  color: #1d2129;
  margin: 0 0 16px;
  line-height: 1.4;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
  padding-left: 4px;
}

.preview-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eef0f3;
}

.preview-meta__row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #4e5969;
}

.preview-meta__label {
  color: #86909c;
  flex-shrink: 0;
  min-width: 56px;
}

.preview-remark {
  margin-bottom: 16px;
}

.preview-remark__label {
  display: block;
  font-size: 12px;
  color: #86909c;
  margin-bottom: 4px;
}

.preview-remark p {
  margin: 0;
  font-size: 13px;
  color: #4e5969;
  line-height: 1.6;
  white-space: pre-wrap;
}

.preview-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.preview-actions :deep(.n-button) {
  flex: 0 0 auto;
}

/* 淡主题色：浅底 + 细边框 + 主色字与图标 */
.preview-actions--tint :deep(.n-button:not(:disabled)) {
  border: 1px solid color-mix(in srgb, var(--theme-primary, #0084ff) 38%, transparent);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 9%, #fff);
  color: var(--theme-primary, #0084ff);
}

.preview-actions--tint :deep(.n-button:not(:disabled):hover) {
  border-color: color-mix(in srgb, var(--theme-primary, #0084ff) 52%, transparent);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 15%, #fff);
}

.preview-actions--tint :deep(.n-button:not(:disabled):focus-visible) {
  outline: 2px solid color-mix(in srgb, var(--theme-primary, #0084ff) 35%, transparent);
  outline-offset: 1px;
}

.preview-actions--tint :deep(.n-button:not(:disabled) .n-icon) {
  color: var(--theme-primary, #0084ff);
}

.preview-fragment-content {
  font-size: 14px;
  line-height: 1.8;
  color: #1d2129;
  white-space: pre-wrap;
  word-break: break-all;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eef0f3;
}
</style>
