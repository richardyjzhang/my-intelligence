<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { NIcon } from 'naive-ui'
import { SendOutline, StopCircleOutline } from '@vicons/ionicons5'
import { chatStream, type ChatMessage } from '@/api/qa'
import ChatMessageItem from './ChatMessageItem.vue'

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  sources?: { title: string; documentId: number }[]
  streaming?: boolean
  reasoningPanelOpen?: boolean
}

const props = defineProps<{ visible: boolean; expanded: boolean }>()

const inputText = ref('')
const messages = ref<DisplayMessage[]>([])
const isStreaming = ref(false)
const abortController = ref<AbortController | null>(null)
const messagesEl = ref<HTMLElement | null>(null)

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
    onMeta: () => {
      /* meta received */
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
      msg.sources = data.sources
      msg.streaming = false
      if (msg.reasoning) msg.reasoningPanelOpen = false
      isStreaming.value = false
      abortController.value = null
      scrollToBottom()
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
  })
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
        <p class="gchat-empty__sub">有什么可以帮你的吗？</p>
      </div>

      <ChatMessageItem
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        :expanded="expanded"
      />
    </div>

    <!-- 输入区 -->
    <div class="gchat-composer">
      <div class="gchat-composer__inner">
        <textarea
          v-model="inputText"
          class="gchat-composer__textarea"
          placeholder="输入问题…（Shift+Enter 换行）"
          rows="2"
          @keydown="handleKeydown"
        />
        <button
          v-if="!isStreaming"
          class="gchat-composer__send"
          :class="{ 'gchat-composer__send--active': inputText.trim() }"
          :disabled="!inputText.trim()"
          @click="handleSend"
        >
          <NIcon :component="SendOutline" :size="14" />
        </button>
        <button
          v-else
          class="gchat-composer__send gchat-composer__send--stop"
          @click="handleStop"
        >
          <NIcon :component="StopCircleOutline" :size="14" />
        </button>
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
  gap: 0.25rem;
  color: var(--n-text-color-3, #86909c);
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
  position: relative;
  border: 1px solid var(--n-border-color, #e5e6eb);
  border-radius: 0.5rem;
  background: var(--n-color, #fff);
  overflow: hidden;
}

.gchat-body--expanded .gchat-composer__inner {
  background: color-mix(in srgb, var(--n-color, #fff) 55%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.gchat-composer__textarea {
  display: block;
  width: 100%;
  min-height: 2.5rem;
  max-height: 8rem;
  padding: 0.5rem 2.5rem 0.5rem 0.625rem;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font: inherit;
  font-size: inherit;
  line-height: 1.5;
  color: var(--n-text-color, #1d2129);
  field-sizing: content;
}

.gchat-composer__textarea::placeholder {
  color: var(--n-placeholder-color, #c0c4cc);
}

.gchat-composer__send {
  position: absolute;
  right: 0.375rem;
  bottom: 0.375rem;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-color-3, #c0c4cc);
  background: transparent;
  transition: color 0.15s, background 0.15s;
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
