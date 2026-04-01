<script setup lang="ts">
import { ref } from 'vue'
import { NIcon } from 'naive-ui'
import { ChatbubbleEllipsesOutline, CloseOutline } from '@vicons/ionicons5'
import AiChatWindow from './AiChatWindow.vue'

const isOpen = ref(false)

function toggle() {
  isOpen.value = !isOpen.value
}
</script>

<template>
  <Teleport to="body">
    <Transition name="ai-chat-slide">
      <div v-show="isOpen" class="ai-chat-panel">
        <AiChatWindow :visible="isOpen" />
      </div>
    </Transition>

    <button class="ai-chat-fab" @click="toggle" :class="{ 'ai-chat-fab--open': isOpen }">
      <NIcon :component="isOpen ? CloseOutline : ChatbubbleEllipsesOutline" :size="24" />
    </button>
  </Teleport>
</template>

<style scoped>
.ai-chat-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 2000;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  background: var(--theme-primary, #008eaa);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.ai-chat-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
}

.ai-chat-fab--open {
  background: #666;
}

.ai-chat-panel {
  position: fixed;
  right: 24px;
  bottom: 88px;
  z-index: 1999;
  width: 420px;
  height: 600px;
  max-height: calc(100vh - 120px);
}

.ai-chat-slide-enter-active,
.ai-chat-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.ai-chat-slide-enter-from,
.ai-chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

@media (max-width: 500px) {
  .ai-chat-panel {
    right: 8px;
    left: 8px;
    bottom: 80px;
    width: auto;
    height: calc(100vh - 100px);
  }
}
</style>
