<script setup lang="ts">
import { computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { NAvatar, NIcon, NSpin, NTag } from 'naive-ui'
import { DocumentTextOutline, FolderOpenOutline, ReloadOutline } from '@vicons/ionicons5'
import type { ChatIntent } from '@/api/qa'
import { renderMarkdown } from '@/utils/markdown'
import { useAuthStore } from '@/stores/auth'
import * as echarts from 'echarts'

const authStore = useAuthStore()

const userAvatarInitial = computed(() => {
  const n = authStore.user?.nickname?.trim()
  const u = authStore.user?.username?.trim()
  const s = (n || u || '我').slice(0, 1)
  return s || '我'
})

interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  intent?: ChatIntent
  sources?: { title: string; documentId: number; fileName?: string }[]
  streaming?: boolean
  reasoningPanelOpen?: boolean
}

const props = defineProps<{ message: DisplayMessage; expanded: boolean }>()

const ECHARTS_REGEX = /```echarts\s*\n([\s\S]*?)```/g
const chartInstanceMap = new Map<HTMLElement, echarts.ECharts>()

function extractCharts(content: string): { cleaned: string; charts: string[] } {
  const charts: string[] = []
  const cleaned = content.replace(ECHARTS_REGEX, (_match, json) => {
    const index = charts.length
    charts.push(json.trim())
    return `<div class="echarts-placeholder" data-chart-index="${index}"></div>`
  })
  return { cleaned, charts }
}

const rendered = computed(() => {
  if (!props.message.content) return { html: '', charts: [] as string[] }
  if (props.message.role === 'user') {
    return { html: '', charts: [] as string[] }
  }
  const { cleaned, charts } = extractCharts(props.message.content)
  return { html: renderMarkdown(cleaned), charts }
})

const reasoningHtml = computed(() => {
  if (!props.message.reasoning) return ''
  return renderMarkdown(props.message.reasoning)
})

function onThinkingToggle(e: Event) {
  const el = e.target as HTMLDetailsElement | null
  if (el && 'open' in el) {
    ;(props.message as DisplayMessage).reasoningPanelOpen = el.open
  }
}

function renderCharts() {
  nextTick(() => {
    const placeholders = document.querySelectorAll(
      `[data-msg-id="${props.message.id}"] .echarts-placeholder`,
    )
    placeholders.forEach((el) => {
      const idx = parseInt(el.getAttribute('data-chart-index') || '0')
      const chartJson = rendered.value.charts[idx]
      if (!chartJson) return

      const container = el as HTMLElement
      if (chartInstanceMap.has(container)) return

      container.style.width = '100%'
      container.style.height = '300px'

      try {
        const option = JSON.parse(chartJson)
        const instance = echarts.init(container)
        instance.setOption(option)
        chartInstanceMap.set(container, instance)
      } catch {
        container.innerHTML =
          '<p style="color:#e03e3e;font-size:12px;">图表配置解析失败</p>'
      }
    })
  })
}

watch(() => rendered.value, () => renderCharts(), { flush: 'post' })

onMounted(() => {
  renderCharts()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  chartInstanceMap.forEach((instance) => instance.dispose())
  chartInstanceMap.clear()
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  chartInstanceMap.forEach((instance) => instance.resize())
}
</script>

<template>
  <div
    class="gchat-msg"
    :class="{
      'gchat-msg--user': message.role === 'user',
      'gchat-msg--assistant': message.role === 'assistant',
      'gchat-msg--expanded': expanded,
    }"
    :data-msg-id="message.id"
  >
    <div
      v-if="expanded && message.role === 'assistant'"
      class="gchat-msg__avatar gchat-msg__avatar--assistant"
      aria-hidden="true"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="gchat-msg__avatar-ai">
        <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.15" />
        <path
          d="M12 6a4 4 0 0 1 4 4c0 1.5-.8 2.5-2 3.2V14a2 2 0 0 1-4 0v-.8C8.8 12.5 8 11.5 8 10a4 4 0 0 1 4-4Z"
          fill="currentColor"
          opacity="0.75"
        />
        <circle cx="12" cy="17.5" r="1" fill="currentColor" />
      </svg>
    </div>

    <div class="gchat-msg__body">
      <!-- 思考过程 -->
      <details
        v-if="message.reasoning"
        class="gchat-msg__thinking-details"
        :open="message.reasoningPanelOpen !== false"
        @toggle="onThinkingToggle"
      >
        <summary class="gchat-msg__thinking-summary">
          <NIcon
            v-if="message.streaming && !message.content"
            :component="ReloadOutline"
            :size="12"
            class="gchat-msg__thinking-spinner"
          />
          <span>{{ message.streaming && !message.content ? '思考中…' : '思考过程' }}</span>
        </summary>
        <div class="gchat-msg__thinking-text gchat-md" v-html="reasoningHtml" />
      </details>

      <!-- 主内容 -->
      <div
        class="gchat-msg__bubble"
        :class="{ 'gchat-msg__bubble--md': message.role === 'assistant' }"
      >
        <template v-if="message.content">
          <template v-if="message.role === 'user'">{{ message.content }}</template>
          <div v-else class="gchat-md" v-html="rendered.html" />
        </template>
        <NSpin v-else-if="message.streaming && !message.reasoning" :size="16" />
        <span v-else-if="message.streaming" class="gchat-cursor" />
      </div>

      <!-- 文档检索：卡片列表 -->
      <div
        v-if="message.intent === 'doc_search' && message.sources?.length"
        class="gchat-msg__doc-cards"
      >
        <div
          v-for="(src, i) in message.sources"
          :key="i"
          class="gchat-msg__doc-card"
        >
          <div class="gchat-msg__doc-card-icon">
            <NIcon :component="FolderOpenOutline" :size="16" />
          </div>
          <div class="gchat-msg__doc-card-body">
            <div class="gchat-msg__doc-card-title">
              {{ src.title || `文档 #${src.documentId}` }}
            </div>
            <div v-if="src.fileName" class="gchat-msg__doc-card-file">
              {{ src.fileName }}
            </div>
            <div class="gchat-msg__doc-card-id">ID: {{ src.documentId }}</div>
          </div>
        </div>
      </div>

      <!-- 知识问答：标签来源 -->
      <div
        v-else-if="message.intent === 'knowledge_qa' && message.sources?.length"
        class="gchat-msg__sources"
      >
        <NTag
          v-for="(src, i) in message.sources"
          :key="i"
          size="small"
          round
          :bordered="false"
        >
          <template #icon><NIcon :component="DocumentTextOutline" :size="12" /></template>
          {{ src.title || `文档#${src.documentId}` }}
        </NTag>
      </div>

      <!-- 未带 intent 的旧消息或未分类：有来源仍用标签 -->
      <div
        v-else-if="!message.intent && message.sources?.length"
        class="gchat-msg__sources"
      >
        <NTag
          v-for="(src, i) in message.sources"
          :key="i"
          size="small"
          round
          :bordered="false"
        >
          <template #icon><NIcon :component="DocumentTextOutline" :size="12" /></template>
          {{ src.title || `文档#${src.documentId}` }}
        </NTag>
      </div>
    </div>

    <div v-if="expanded && message.role === 'user'" class="gchat-msg__avatar gchat-msg__avatar--user">
      <NAvatar
        round
        :size="34"
        :style="{
          backgroundColor: 'color-mix(in srgb, var(--theme-primary, #0084ff) 88%, #fff)',
          color: '#fff',
          fontSize: '0.875rem',
          fontWeight: 600,
        }"
      >
        {{ userAvatarInitial }}
      </NAvatar>
    </div>
  </div>
</template>

<style scoped>
.gchat-msg {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.gchat-msg--user {
  justify-content: flex-end;
}

.gchat-msg--assistant {
  justify-content: flex-start;
}

.gchat-msg__body {
  max-width: min(32rem, 85%);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.gchat-msg--expanded .gchat-msg__body {
  max-width: 70%;
}

.gchat-msg__avatar {
  flex-shrink: 0;
  align-self: flex-start;
  padding-top: 0.125rem;
}

.gchat-msg__avatar--assistant {
  width: 2.125rem;
  height: 2.125rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--theme-primary, #0084ff);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 12%, var(--n-color-modal, #fafafc));
  border: 1px solid color-mix(in srgb, var(--theme-primary, #0084ff) 22%, transparent);
}

.gchat-msg__avatar-ai {
  width: 1.25rem;
  height: 1.25rem;
  display: block;
}

.gchat-msg__avatar--user {
  display: flex;
  align-items: flex-start;
}

/* ── 思考区 ── */
.gchat-msg__thinking-details {
  font-size: inherit;
  color: var(--n-text-color-3, #86909c);
  background: color-mix(in srgb, #6366f1 6%, var(--n-color-modal, #fafafc));
  border: 1px solid color-mix(in srgb, #6366f1 15%, transparent);
  border-radius: 0.375rem;
  padding: 0.25rem 0.5rem 0.375rem;
}

.gchat-msg__thinking-summary {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 500;
  color: #6366f1;
  cursor: pointer;
  list-style: none;
  user-select: none;
  font-size: 0.8125rem;
}

.gchat-msg__thinking-summary::-webkit-details-marker {
  display: none;
}

.gchat-msg__thinking-spinner {
  flex-shrink: 0;
  animation: gchat-spin 1s linear infinite;
}

@keyframes gchat-spin {
  to {
    transform: rotate(360deg);
  }
}

.gchat-msg__thinking-text {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--n-text-color-3, #86909c);
  margin-top: 0.25rem;
}

/* ── 气泡 ── */
.gchat-msg__bubble {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  font-size: inherit;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.gchat-msg__bubble--md {
  white-space: normal;
}

.gchat-msg--user .gchat-msg__bubble {
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 16%, #fff);
  border: 1px solid color-mix(in srgb, var(--theme-primary, #0084ff) 30%, transparent);
  border-radius: 0.75rem 0.125rem 0.75rem 0.75rem;
}

.gchat-msg--assistant .gchat-msg__bubble {
  background: var(--n-color, #fff);
  border: 1px solid var(--n-border-color, #e5e6eb);
  border-radius: 0.125rem 0.75rem 0.75rem 0.75rem;
}

/* ── 流式光标 ── */
.gchat-cursor {
  display: inline-block;
  width: 0.5rem;
  height: 1rem;
  background: var(--theme-primary, #0084ff);
  border-radius: 1px;
  animation: gchat-blink 0.8s step-end infinite;
  vertical-align: text-bottom;
}

@keyframes gchat-blink {
  50% {
    opacity: 0;
  }
}

/* ── 来源 ── */
.gchat-msg__sources {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: 0.25rem;
}

/* ── 文档检索卡片 ── */
.gchat-msg__doc-cards {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.375rem;
  max-width: 100%;
}

.gchat-msg__doc-card {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0.625rem;
  border-radius: 0.375rem;
  border: 1px solid var(--n-border-color, #e5e6eb);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 4%, var(--n-color, #fff));
}

.gchat-msg__doc-card-icon {
  flex-shrink: 0;
  color: var(--theme-primary, #0084ff);
  padding-top: 0.125rem;
}

.gchat-msg__doc-card-body {
  min-width: 0;
  flex: 1;
}

.gchat-msg__doc-card-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--n-text-color, #1d2129);
  line-height: 1.4;
}

.gchat-msg__doc-card-file {
  font-size: 0.75rem;
  color: var(--n-text-color-3, #86909c);
  margin-top: 0.125rem;
  word-break: break-all;
}

.gchat-msg__doc-card-id {
  font-size: 0.6875rem;
  color: var(--n-text-color-3, #86909c);
  margin-top: 0.125rem;
  font-family: ui-monospace, monospace;
}

/* ── Markdown 内容样式（gchat-md） ── */
.gchat-md {
  word-break: break-word;
}

.gchat-md :deep(> :first-child) {
  margin-top: 0;
}

.gchat-md :deep(> :last-child) {
  margin-bottom: 0;
}

.gchat-md :deep(p) {
  margin: 0.35em 0;
}

.gchat-md :deep(h1),
.gchat-md :deep(h2),
.gchat-md :deep(h3),
.gchat-md :deep(h4) {
  margin: 0.5em 0 0.3em;
  font-weight: 600;
  line-height: 1.35;
}

.gchat-md :deep(h1) {
  font-size: 1.2em;
}

.gchat-md :deep(h2) {
  font-size: 1.12em;
}

.gchat-md :deep(h3),
.gchat-md :deep(h4) {
  font-size: 1.05em;
}

.gchat-md :deep(ul),
.gchat-md :deep(ol) {
  margin: 0.35em 0;
  padding-left: 1.35em;
}

.gchat-md :deep(li) {
  margin: 0.15em 0;
}

.gchat-md :deep(li > p) {
  margin: 0.15em 0;
}

.gchat-md :deep(blockquote) {
  margin: 0.35em 0;
  padding-left: 0.75em;
  border-left: 3px solid color-mix(in srgb, var(--n-border-color, #e5e6eb) 85%, transparent);
  color: var(--n-text-color-2, #4e5969);
}

.gchat-md :deep(pre) {
  margin: 0.45em 0;
  padding: 0.5rem 0.65rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  font-size: 0.9em;
  line-height: 1.45;
  background: color-mix(in srgb, var(--n-border-color, #e5e6eb) 32%, transparent);
  border: 1px solid color-mix(in srgb, var(--n-border-color, #e5e6eb) 50%, transparent);
}

.gchat-md :deep(:not(pre) > code) {
  padding: 0.1em 0.35em;
  border-radius: 0.25rem;
  font-size: 0.9em;
  font-family: ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, monospace;
  background: color-mix(in srgb, var(--n-border-color, #e5e6eb) 32%, transparent);
}

.gchat-md :deep(pre code) {
  padding: 0;
  background: none;
  border-radius: 0;
  font-size: inherit;
}

.gchat-md :deep(table) {
  --gchat-md-table-border: #d0d5dd;
  border-collapse: collapse;
  width: 100%;
  max-width: 100%;
  margin: 0.45em 0;
  font-size: 0.95em;
  border: 1px solid var(--gchat-md-table-border);
  background: var(--n-color, #fff);
}

.gchat-md :deep(th),
.gchat-md :deep(td) {
  border: 1px solid var(--gchat-md-table-border);
  padding: 0.35em 0.55em;
  text-align: left;
  vertical-align: top;
}

.gchat-md :deep(th) {
  font-weight: 600;
  background: color-mix(in srgb, #d0d5dd 18%, transparent);
}

.gchat-md :deep(hr) {
  margin: 0.65em 0;
  border: none;
  border-top: 1px solid var(--n-border-color, #e5e6eb);
}

.gchat-md :deep(a) {
  color: var(--theme-primary, #0084ff);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.gchat-md :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.25rem;
  vertical-align: middle;
}

.gchat-md :deep(input[type='checkbox']) {
  margin-right: 0.35em;
  vertical-align: middle;
}
</style>
