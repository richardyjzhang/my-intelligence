<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NConfigProvider, NDialogProvider, NGlobalStyle, NMessageProvider } from 'naive-ui'
import { useThemeStore } from '@/stores/theme'
import AiChatFab from '@/components/AiChat/AiChatFab.vue'

const themeStore = useThemeStore()
const route = useRoute()

const showAiChat = computed(() => route.path !== '/login')
</script>

<template>
  <NConfigProvider :theme-overrides="themeStore.themeOverrides">
    <NGlobalStyle />
    <NMessageProvider>
      <NDialogProvider>
        <RouterView />
        <AiChatFab v-if="showAiChat" />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
