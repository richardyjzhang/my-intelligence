<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { NIcon, NSpin, NTag } from 'naive-ui'
import {
  PersonOutline,
  SparklesOutline,
  ChevronDownOutline,
  DocumentTextOutline,
} from '@vicons/ionicons5'
import MarkdownIt from 'markdown-it'
import * as echarts from 'echarts'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  sources?: { title: string; documentId: number }[]
  loading?: boolean
}

const props = defineProps<{ message: DisplayMessage }>()

const showReasoning = ref(false)
const chartContainers = ref<HTMLElement[]>([])
const chartInstanceMap = new Map<HTMLElement, echarts.ECharts>()

const ECHARTS_REGEX = /```echarts\s*\n([\s\S]*?)```/g

function extractCharts(content: string): { html: string; charts: string[] } {
  const charts: string[] = []
  const html = content.replace(ECHARTS_REGEX, (_match, json) => {
    const index = charts.length
    charts.push(json.trim())
    return `<div class="echarts-placeholder" data-chart-index="${index}"></div>`
  })
  return { html, charts }
}

const rendered = computed(() => {
  if (props.message.role === 'user') {
    return { html: md.render(props.message.content), charts: [] as string[] }
  }
  const { html, charts } = extractCharts(props.message.content)
  return { html: md.render(html), charts }
})

const reasoningHtml = computed(() => {
  if (!props.message.reasoning) return ''
  return md.render(props.message.reasoning)
})

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
      } catch (e) {
        container.innerHTML = '<p style="color:#e03e3e;font-size:12px;">图表配置解析失败</p>'
      }
    })
  })
}

watch(
  () => rendered.value,
  () => renderCharts(),
  { flush: 'post' },
)

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
    class="chat-message"
    :class="[`chat-message--${message.role}`]"
    :data-msg-id="message.id"
  >
    <div class="chat-message__avatar">
      <NIcon
        :component="message.role === 'user' ? PersonOutline : SparklesOutline"
        :size="20"
      />
    </div>
    <div class="chat-message__body">
      <!-- 思考过程 -->
      <div v-if="message.reasoning" class="chat-message__reasoning">
        <div
          class="chat-message__reasoning-toggle"
          @click="showReasoning = !showReasoning"
        >
          <NIcon :component="ChevronDownOutline" :size="14"
            :style="{ transform: showReasoning ? 'rotate(0deg)' : 'rotate(-90deg)', transition: 'transform 0.2s' }"
          />
          <span>思考过程</span>
        </div>
        <div v-show="showReasoning" class="chat-message__reasoning-content" v-html="reasoningHtml" />
      </div>

      <!-- 加载中 -->
      <NSpin v-if="message.loading && !message.content && !message.reasoning" :size="16" />

      <!-- 正文 -->
      <div
        v-if="message.content"
        class="chat-message__content markdown-body"
        v-html="rendered.html"
      />

      <!-- 来源引用 -->
      <div v-if="message.sources?.length" class="chat-message__sources">
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
  </div>
</template>

<style scoped>
.chat-message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.chat-message--user {
  flex-direction: row-reverse;
}

.chat-message__avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.chat-message--user .chat-message__avatar {
  background: var(--theme-primary, #008eaa);
  color: #fff;
}

.chat-message--assistant .chat-message__avatar {
  background: #f0f0f0;
  color: #666;
}

.chat-message__body {
  max-width: 80%;
  min-width: 40px;
}

.chat-message--user .chat-message__body {
  background: var(--theme-primary, #008eaa);
  color: #fff;
  border-radius: 12px 2px 12px 12px;
  padding: 10px 14px;
}

.chat-message--assistant .chat-message__body {
  background: #f7f7f8;
  color: #333;
  border-radius: 2px 12px 12px 12px;
  padding: 10px 14px;
}

.chat-message__reasoning {
  margin-bottom: 8px;
  font-size: 12px;
  color: #999;
}

.chat-message__reasoning-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
}

.chat-message__reasoning-toggle:hover {
  color: #666;
}

.chat-message__reasoning-content {
  margin-top: 6px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: #888;
}

.chat-message__content :deep(p) {
  margin: 0 0 0.5em;
  line-height: 1.6;
}

.chat-message__content :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-message__content :deep(pre) {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  padding: 10px;
  overflow-x: auto;
  font-size: 13px;
}

.chat-message__content :deep(code) {
  font-size: 13px;
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 4px;
  border-radius: 3px;
}

.chat-message__content :deep(pre code) {
  background: none;
  padding: 0;
}

.chat-message__content :deep(ul),
.chat-message__content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.chat-message__content :deep(table) {
  border-collapse: collapse;
  margin: 0.5em 0;
  font-size: 13px;
}

.chat-message__content :deep(th),
.chat-message__content :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 10px;
}

.chat-message__sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
</style>
