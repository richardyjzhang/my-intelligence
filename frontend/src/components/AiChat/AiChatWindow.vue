<script setup lang="ts">
import { computed, h, ref, nextTick, watch, type Component } from 'vue'
import { storeToRefs } from 'pinia'
import { NIcon, NDropdown, NButton } from 'naive-ui'
import {
  BookOutline,
  ChatbubbleEllipsesOutline,
  FolderOpenOutline,
  SendOutline,
  SparklesOutline,
  StopCircleOutline,
} from '@vicons/ionicons5'
import {
  chatStream,
  type ChatMessage,
  type ChatIntent,
  type ChatMode,
  type ChatSourceItem,
} from '@/api/qa'
import { useAiChatStore } from '@/stores/aiChat'
import ChatMessageItem from './ChatMessageItem.vue'

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  intent?: ChatIntent
  /** 文档检索等 */
  sources?: ChatSourceItem[]
  /** 知识问答：实际引用 / 其他检索结果 */
  citedSources?: ChatSourceItem[]
  relatedSources?: ChatSourceItem[]
  streaming?: boolean
  reasoningPanelOpen?: boolean
  /** 后端提示（如已忽略历史、建议清空对话） */
  hint?: string
}

const props = defineProps<{ visible: boolean; expanded: boolean }>()

const aiChat = useAiChatStore()
const { scopeDocument } = storeToRefs(aiChat)

const inputText = ref('')
const messages = ref<DisplayMessage[]>([])
const isStreaming = ref(false)
const abortController = ref<AbortController | null>(null)
const messagesEl = ref<HTMLElement | null>(null)
const chatMode = ref<ChatMode>('auto')

const MODE_LABELS: Record<ChatMode, string> = {
  auto: '自动模式',
  casual: '划水闲聊',
  doc_search: '文档检索',
  knowledge_qa: '知识问答',
}

const modeIconByMode: Record<ChatMode, Component> = {
  auto: SparklesOutline,
  casual: ChatbubbleEllipsesOutline,
  doc_search: FolderOpenOutline,
  knowledge_qa: BookOutline,
}

const modeTriggerIcon = computed(() => modeIconByMode[chatMode.value])

const modeTriggerTitle = computed(
  () => `当前：${MODE_LABELS[chatMode.value]}，点击切换`,
)

const streamMode = computed<ChatMode>(() =>
  scopeDocument.value ? 'knowledge_qa' : chatMode.value,
)

const modeDropdownOptions = [
  {
    key: 'auto',
    label: '自动模式',
    icon: () => h(NIcon, { size: 16, component: SparklesOutline }),
  },
  {
    key: 'casual',
    label: '划水闲聊',
    icon: () => h(NIcon, { size: 16, component: ChatbubbleEllipsesOutline }),
  },
  {
    key: 'doc_search',
    label: '文档检索',
    icon: () => h(NIcon, { size: 16, component: FolderOpenOutline }),
  },
  {
    key: 'knowledge_qa',
    label: '知识问答',
    icon: () => h(NIcon, { size: 16, component: BookOutline }),
  },
]

function onModeDropdownSelect(key: string) {
  chatMode.value = key as ChatMode
}

let messageIdCounter = 0

function generateId() {
  return `msg_${++messageIdCounter}_${Date.now()}`
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function buildHistory(): ChatMessage[] {
  const hist: ChatMessage[] = []
  for (const msg of messages.value) {
    if (msg.role === 'user') {
      hist.push({ role: 'user', content: msg.content })
    } else if (msg.role === 'assistant' && msg.content && !msg.streaming) {
      hist.push({ role: 'assistant', content: msg.content })
    }
  }
  return hist
}

function setQuickMode(mode: ChatMode) {
  chatMode.value = mode
  scrollToBottom()
}

function handleSend() {
  const query = inputText.value.trim()
  if (!query || isStreaming.value) return

  inputText.value = ''

  messages.value.push({
    id: generateId(),
    role: 'user',
    content: query,
    reasoning: '',
  })

  messages.value.push({
    id: generateId(),
    role: 'assistant',
    content: '',
    reasoning: '',
    streaming: true,
    reasoningPanelOpen: true,
  })
  isStreaming.value = true
  scrollToBottom()

  const history = buildHistory().slice(0, -1)
  const assistantIdx = messages.value.length - 1

  abortController.value = chatStream(query, history, {
    onMeta: (data) => {
      const msg = messages.value[assistantIdx]
      if (data.intent) {
        msg.intent = data.intent as ChatIntent
      }
    },
    onReasoningDelta: (content) => {
      const msg = messages.value[assistantIdx]
      msg.reasoning += content
      scrollToBottom()
    },
    onAnswerDelta: (content) => {
      const msg = messages.value[assistantIdx]
      if (msg.reasoning && msg.reasoningPanelOpen !== false) {
        msg.reasoningPanelOpen = false
      }
      msg.content += content
      scrollToBottom()
    },
    onDone: (data) => {
      const msg = messages.value[assistantIdx]
      if (data.trimSuffix) {
        msg.content = msg.content.replace(data.trimSuffix, '').trimEnd()
      }
      if (data.sources !== undefined) {
        msg.sources = data.sources
      }
      if (data.citedSources !== undefined) {
        msg.citedSources = data.citedSources
      }
      if (data.relatedSources !== undefined) {
        msg.relatedSources = data.relatedSources
      }
      msg.streaming = false
      if (msg.reasoning) msg.reasoningPanelOpen = false
      isStreaming.value = false
      abortController.value = null
      scrollToBottom()
    },
    onHint: (data) => {
      const msg = messages.value[assistantIdx]
      if (data?.message) {
        msg.hint = data.message
        scrollToBottom()
      }
    },
    onError: (message) => {
      const msg = messages.value[assistantIdx]
      if (!msg.content) {
        msg.content = `出错了：${message}`
      }
      msg.streaming = false
      isStreaming.value = false
      abortController.value = null
    },
  }, { mode: streamMode.value, documentId: scopeDocument.value?.id })
}

function handleStop() {
  abortController.value?.abort()
  abortController.value = null
  isStreaming.value = false
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg?.role === 'assistant') {
    lastMsg.streaming = false
    if (!lastMsg.content) lastMsg.content = '（已取消）'
  }
}

function handleClear() {
  if (isStreaming.value) handleStop()
  messages.value = []
  aiChat.clearDocumentScope()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

watch(
  () => props.visible,
  (val) => {
    if (val) scrollToBottom()
  },
)

watch(
  () => messages.value.length,
  () => scrollToBottom(),
)

watch(
  scopeDocument,
  (v, prev) => {
    if (v && (!prev || v.id !== prev.id)) {
      chatMode.value = 'knowledge_qa'
    }
  },
)

defineExpose({ handleClear, messages })
</script>

<template>
  <div class="gchat-body" :class="{ 'gchat-body--expanded': expanded }">
    <!-- 消息列表 -->
    <div ref="messagesEl" class="gchat-messages">
      <div v-if="messages.length === 0" class="gchat-empty">
        <div class="gchat-empty__icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
            <circle cx="24" cy="24" r="20" fill="currentColor" opacity="0.08" />
            <path d="M24 14a6 6 0 0 1 6 6c0 2.2-1.2 3.8-3 4.8V26a3 3 0 0 1-6 0v-1.2c-1.8-1-3-2.6-3-4.8a6 6 0 0 1 6-6Z" fill="currentColor" opacity="0.3" />
            <circle cx="24" cy="32" r="1.5" fill="currentColor" opacity="0.3" />
          </svg>
        </div>
        <p class="gchat-empty__text">你好！我是拾知 AI 助手</p>
        <p class="gchat-empty__sub">
          可以<strong>划水闲聊</strong>、<strong>文档检索</strong>、或基于知识库的<strong>知识问答</strong>。
        </p>
      </div>

      <ChatMessageItem
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :expanded="expanded"
      />
    </div>

    <div v-if="scopeDocument" class="gchat-scope-bar">
      <span class="gchat-scope-bar__text">围绕文档：{{ scopeDocument.title }}</span>
      <NButton text type="primary" size="tiny" @click="aiChat.clearDocumentScope()">
        清除限定
      </NButton>
    </div>

    <!-- 输入区 -->
    <div class="gchat-composer">
      <div class="gchat-composer__inner">
        <div class="gchat-composer__side gchat-composer__side--left">
          <NDropdown
            trigger="click"
            placement="top-start"
            :show-arrow="true"
            :options="modeDropdownOptions"
            @select="onModeDropdownSelect"
          >
            <button
              type="button"
              class="gchat-composer__mode-btn"
              :aria-label="modeTriggerTitle"
              :title="modeTriggerTitle"
            >
              <NIcon :component="modeTriggerIcon" :size="expanded ? 20 : 18" />
            </button>
          </NDropdown>
        </div>
        <textarea
          v-model="inputText"
          class="gchat-composer__textarea"
          placeholder="输入消息…（Shift+Enter 换行）"
          rows="1"
          @keydown="handleKeydown"
        />
        <div class="gchat-composer__side gchat-composer__side--right">
          <button
            v-if="!isStreaming"
            class="gchat-composer__send"
            :class="{ 'gchat-composer__send--active': inputText.trim() }"
            :disabled="!inputText.trim()"
            @click="handleSend"
          >
            <NIcon :component="SendOutline" :size="expanded ? 16 : 14" />
          </button>
          <button
            v-else
            class="gchat-composer__send gchat-composer__send--stop"
            @click="handleStop"
          >
            <NIcon :component="StopCircleOutline" :size="expanded ? 16 : 14" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gchat-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ── 消息区 ── */
.gchat-messages {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.gchat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  color: var(--n-text-color-3, #86909c);
  padding: 0 0.75rem;
  text-align: center;
}

.gchat-empty__icon {
  color: var(--theme-primary, #0084ff);
  margin-bottom: 0.5rem;
}

.gchat-empty__text {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--n-text-color, #1d2129);
}

.gchat-empty__sub {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  max-width: 22rem;
}

.gchat-empty__sub strong {
  color: var(--theme-primary, #0084ff);
  font-weight: 600;
}

.gchat-empty__quick {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  justify-content: center;
  margin-top: 0.5rem;
}

.gchat-empty__chip {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid color-mix(in srgb, var(--theme-primary, #0084ff) 35%, transparent);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 8%, transparent);
  color: var(--theme-primary, #0084ff);
  cursor: pointer;
  transition: background 0.15s;
}

.gchat-empty__chip:hover {
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 16%, transparent);
}

.gchat-scope-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
  color: var(--n-text-color-2, #4e5969);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 6%, transparent);
  border-top: 1px solid var(--n-border-color, #e5e6eb);
}

.gchat-scope-bar__text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 输入区 ── */
.gchat-composer {
  flex-shrink: 0;
  padding: 0.375rem 0.75rem 0.75rem;
  border-top: 1px solid var(--n-border-color, #e5e6eb);
  background: var(--n-color, #fff);
}

.gchat-body--expanded .gchat-composer {
  background: color-mix(in srgb, var(--n-color, #fff) 45%, transparent);
  border-top-color: color-mix(in srgb, var(--n-border-color, #e5e6eb) 50%, transparent);
}

.gchat-composer__inner {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  flex: 1 1 auto;
  min-width: 0;
  /* em 随父级字号变化，最大化时与 panel 字体一致 */
  gap: 0.5em;
  padding: 0.5em 0.5em 0.5em 0.35em;
  border: 1px solid var(--n-border-color, #e5e6eb);
  border-radius: 0.5rem;
  background: var(--n-color, #fff);
  overflow: visible;
}

.gchat-composer__side {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gchat-composer__side--left,
.gchat-composer__side--right {
  align-self: flex-end;
  /* 与 textarea 行盒对齐：底部留白与输入区一致 */
  padding-bottom: 0.125em;
}

.gchat-composer__side--left :deep(.n-dropdown) {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
}

.gchat-composer__mode-btn {
  width: 2.25em;
  height: 2.25em;
  min-width: 2.25em;
  min-height: 2.25em;
  padding: 0;
  border: none;
  border-radius: 0.375em;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-color-3, #86909c);
  background: transparent;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
  font-size: inherit;
  box-sizing: border-box;
}

.gchat-composer__mode-btn:hover {
  color: var(--theme-primary, #0084ff);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 10%, transparent);
}

.gchat-body--expanded .gchat-composer__inner {
  background: color-mix(in srgb, var(--n-color, #fff) 55%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* 最大化：略增输入区内边距，与放大字号下的行高匹配 */
.gchat-body--expanded .gchat-composer {
  padding-left: 1rem;
  padding-right: 1rem;
  padding-bottom: 1rem;
}

.gchat-body--expanded .gchat-composer__side--left,
.gchat-body--expanded .gchat-composer__side--right {
  padding-bottom: 0.25em;
}

.gchat-composer__textarea {
  display: block;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 2.5em;
  max-height: 8rem;
  padding: 0.5em 0.375em;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font: inherit;
  font-size: inherit;
  line-height: 1.5;
  color: var(--n-text-color, #1d2129);
  field-sizing: content;
  box-sizing: border-box;
}

.gchat-composer__textarea::placeholder {
  color: var(--n-placeholder-color, #c0c4cc);
}

.gchat-composer__send {
  width: 2.25em;
  height: 2.25em;
  min-width: 2.25em;
  min-height: 2.25em;
  border-radius: 0.375em;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-color-3, #c0c4cc);
  background: transparent;
  transition: color 0.15s, background 0.15s;
  font-size: inherit;
  box-sizing: border-box;
  flex-shrink: 0;
}

.gchat-composer__send:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.gchat-composer__send--active {
  color: #fff;
  background: var(--theme-primary, #0084ff);
}

.gchat-composer__send--active:hover {
  background: var(--theme-primary-hover, #2593ff);
}

.gchat-composer__send--stop {
  color: #fff;
  background: #e03e3e;
  opacity: 1;
}

.gchat-composer__send--stop:hover {
  background: #c53030;
}
</style>
