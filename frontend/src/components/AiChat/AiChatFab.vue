<script setup lang="ts">
import { ref, computed } from 'vue'
import { NIcon, NButton } from 'naive-ui'
import {
  ChatbubbleEllipsesOutline,
  CloseOutline,
  ExpandOutline,
  ContractOutline,
  TrashOutline,
} from '@vicons/ionicons5'
import AiChatWindow from './AiChatWindow.vue'

const isOpen = ref(false)
const expanded = ref(false)
const chatWindowRef = ref<InstanceType<typeof AiChatWindow> | null>(null)

const hasMessages = computed(() => (chatWindowRef.value?.messages?.length ?? 0) > 0)

function toggleOpen() {
  isOpen.value = !isOpen.value
  if (!isOpen.value) expanded.value = false
}

function toggleExpand() {
  if (document.startViewTransition) {
    document.startViewTransition(() => {
      expanded.value = !expanded.value
    })
  } else {
    expanded.value = !expanded.value
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="gchat-fab">
      <button
        v-if="!isOpen"
        class="gchat-fab"
        aria-label="打开 AI 助手"
        @click="toggleOpen"
      >
        <NIcon :component="ChatbubbleEllipsesOutline" :size="24" />
      </button>
    </Transition>

    <Transition name="gchat-panel">
      <div
        v-if="isOpen"
        class="gchat-panel"
        :class="{ 'gchat-panel--expanded': expanded }"
        :style="{ viewTransitionName: 'gchat-panel' }"
      >
        <div class="gchat-header">
          <div class="gchat-header__left">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="gchat-header__logo">
              <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.15" />
              <path d="M12 6a4 4 0 0 1 4 4c0 1.5-.8 2.5-2 3.2V14a2 2 0 0 1-4 0v-.8C8.8 12.5 8 11.5 8 10a4 4 0 0 1 4-4Z" fill="currentColor" opacity="0.6" />
              <circle cx="12" cy="17.5" r="1" fill="currentColor" />
            </svg>
            <span class="gchat-header__title">AI 助手</span>
          </div>
          <div class="gchat-header__actions">
            <NButton quaternary size="tiny" :disabled="!hasMessages" @click="chatWindowRef?.handleClear()">
              <template #icon>
                <NIcon :component="TrashOutline" :size="16" />
              </template>
            </NButton>
            <NButton quaternary size="tiny" @click="toggleExpand">
              <template #icon>
                <NIcon :component="expanded ? ContractOutline : ExpandOutline" :size="16" />
              </template>
            </NButton>
            <NButton quaternary size="tiny" @click="toggleOpen">
              <template #icon>
                <NIcon :component="CloseOutline" :size="16" />
              </template>
            </NButton>
          </div>
        </div>

        <AiChatWindow ref="chatWindowRef" :visible="isOpen" :expanded="expanded" />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── FAB ── */
.gchat-fab {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  z-index: 2000;
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--theme-primary, #0084ff);
  box-shadow:
    0 4px 14px color-mix(in srgb, var(--theme-primary, #0084ff) 35%, transparent),
    0 2px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.gchat-fab:hover {
  transform: scale(1.08);
  box-shadow:
    0 6px 20px color-mix(in srgb, var(--theme-primary, #0084ff) 40%, transparent),
    0 3px 10px rgba(0, 0, 0, 0.12);
}

.gchat-fab:active {
  transform: scale(0.96);
}

/* ── 面板 ── */
.gchat-panel {
  position: fixed;
  z-index: 1999;
  right: 1.25rem;
  bottom: 1.25rem;
  width: calc((100vw - 220px) * 0.42);
  min-width: 24rem;
  max-width: 40rem;
  height: calc((100vh - 3.5rem) * 0.8);
  min-height: 24rem;
  max-height: calc(100vh - 6rem);
  display: flex;
  flex-direction: column;
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--n-color-modal, #fafafc);
  border: 1px solid var(--n-border-color, #e5e6eb);
  font-size: var(--n-font-size, 0.875rem);
  line-height: var(--n-line-height, 1.5715);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.1),
    0 4px 12px rgba(0, 0, 0, 0.06);
  view-transition-name: gchat-panel;
  transition:
    width 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    height 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    top 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    left 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    right 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    bottom 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    border-radius 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.4s ease;
}

/* 全屏：铺满 topbar 以下 + sidebar 以右 */
.gchat-panel--expanded {
  top: 3.5rem;
  left: 220px;
  right: 0;
  bottom: 0;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  min-width: 0;
  min-height: 0;
  border-radius: 0;
  box-shadow: none;
  border-top: none;
  border-right: none;
  border-bottom: none;
  background: color-mix(in srgb, var(--n-color-modal, #fafafc) 52%, transparent);
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  font-size: calc(var(--n-font-size, 1rem) + 1px);
  /* 与正文一致，避免输入行内文字与图标因行高不同而错位 */
  line-height: 1.5;
}

/* ── 顶栏 ── */
.gchat-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.625rem 0.5rem 0.75rem;
  border-bottom: 1px solid color-mix(in srgb, var(--theme-primary, #0084ff) 18%, transparent);
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 8%, #fff);
}

.gchat-panel--expanded .gchat-header {
  background: color-mix(in srgb, var(--theme-primary, #0084ff) 6%, rgba(255, 255, 255, 0.45));
  border-bottom-color: color-mix(in srgb, var(--theme-primary, #0084ff) 14%, transparent);
}

.gchat-header__left {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.gchat-header__logo {
  width: 1.125rem;
  height: 1.125rem;
  color: var(--theme-primary, #0084ff);
}

.gchat-header__title {
  font-weight: 600;
  font-size: inherit;
  color: var(--n-text-color, #1d2129);
}

.gchat-header__actions {
  display: flex;
  align-items: center;
  gap: 0.125rem;
}

/* ── 动画 ── */
.gchat-fab-enter-active,
.gchat-fab-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.gchat-fab-enter-from {
  opacity: 0;
  transform: scale(0.5);
}
.gchat-fab-leave-to {
  opacity: 0;
  transform: scale(0.5);
}

.gchat-panel-enter-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.gchat-panel-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.gchat-panel-enter-from {
  opacity: 0;
  transform: translateY(1.5rem) scale(0.95);
}
.gchat-panel-leave-to {
  opacity: 0;
  transform: translateY(1rem) scale(0.97);
}
</style>

<style>
::view-transition-old(gchat-panel),
::view-transition-new(gchat-panel) {
  animation-duration: 0.4s !important;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
