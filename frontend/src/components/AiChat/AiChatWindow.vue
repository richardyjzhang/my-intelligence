<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { NIcon, NInput, NButton, NScrollbar } from 'naive-ui'
import {
  SendOutline,
  StopCircleOutline,
  TrashOutline,
} from '@vicons/ionicons5'
import { chatStream, type ChatMessage } from '@/api/qa'
import ChatMessageItem from './ChatMessageItem.vue'

interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  reasoning: string
  sources?: { title: string; documentId: number }[]
  loading?: boolean
}

const props = defineProps<{ visible: boolean }>()

const inputText = ref('')
const messages = ref<DisplayMessage[]>([])
const isStreaming = ref(false)
const abortController = ref<AbortController | null>(null)
const scrollbarRef = ref<InstanceType<typeof NScrollbar> | null>(null)

let messageIdCounter = 0

function generateId() {
  return `msg_${++messageIdCounter}_${Date.now()}`
}

function scrollToBottom() {
  nextTick(() => {
    scrollbarRef.value?.scrollTo({ top: 999999, behavior: 'smooth' })
  })
}

function buildHistory(): ChatMessage[] {
  const hist: ChatMessage[] = []
  for (const msg of messages.value) {
    if (msg.role === 'user') {
      hist.push({ role: 'user', content: msg.content })
    } else if (msg.role === 'assistant' && msg.content && !msg.loading) {
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
    loading: true,
  })
  isStreaming.value = true

  scrollToBottom()

  const history = buildHistory().slice(0, -1)
  const assistantIdx = messages.value.length - 1

  abortController.value = chatStream(query, history, {
    onMeta: () => {
      messages.value[assistantIdx].loading = false
    },
    onReasoningDelta: (content) => {
      messages.value[assistantIdx].reasoning += content
      scrollToBottom()
    },
    onAnswerDelta: (content) => {
      messages.value[assistantIdx].loading = false
      messages.value[assistantIdx].content += content
      scrollToBottom()
    },
    onDone: (data) => {
      messages.value[assistantIdx].loading = false
      messages.value[assistantIdx].sources = data.sources
      isStreaming.value = false
      abortController.value = null
      scrollToBottom()
    },
    onError: (message) => {
      messages.value[assistantIdx].loading = false
      if (!messages.value[assistantIdx].content) {
        messages.value[assistantIdx].content = `**错误：** ${message}`
      }
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
    lastMsg.loading = false
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
</script>

<template>
  <div class="ai-chat-window">
    <div class="ai-chat-header">
      <span class="ai-chat-header__title">AI 助手</span>
      <NButton
        quaternary
        circle
        size="small"
        :disabled="messages.length === 0"
        @click="handleClear"
      >
        <template #icon><NIcon :component="TrashOutline" /></template>
      </NButton>
    </div>

    <NScrollbar ref="scrollbarRef" class="ai-chat-body">
      <div v-if="messages.length === 0" class="ai-chat-empty">
        <p>你好！我是拾知 AI 助手，有什么可以帮你的吗？</p>
      </div>
      <ChatMessageItem
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
    </NScrollbar>

    <div class="ai-chat-footer">
      <NInput
        v-model:value="inputText"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="输入你的问题..."
        :disabled="isStreaming"
        @keydown="handleKeydown"
      />
      <NButton
        v-if="!isStreaming"
        type="primary"
        circle
        :disabled="!inputText.trim()"
        @click="handleSend"
      >
        <template #icon><NIcon :component="SendOutline" /></template>
      </NButton>
      <NButton
        v-else
        type="error"
        circle
        @click="handleStop"
      >
        <template #icon><NIcon :component="StopCircleOutline" /></template>
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.ai-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: var(--theme-primary, #008eaa);
  color: #fff;
}

.ai-chat-header__title {
  font-size: 15px;
  font-weight: 600;
}

.ai-chat-header :deep(.n-button) {
  color: rgba(255, 255, 255, 0.8);
}

.ai-chat-header :deep(.n-button:hover) {
  color: #fff;
}

.ai-chat-body {
  flex: 1;
  min-height: 0;
  padding: 16px;
}

.ai-chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 14px;
}

.ai-chat-footer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
}

.ai-chat-footer :deep(.n-input) {
  flex: 1;
}
</style>
