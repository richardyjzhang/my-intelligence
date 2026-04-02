import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface ScopeDocument {
  id: number
  title: string
}

export const useAiChatStore = defineStore('aiChat', () => {
  const panelOpen = ref(false)
  const scopeDocument = ref<ScopeDocument | null>(null)

  function openDiscussDocument(id: number, title: string) {
    scopeDocument.value = { id, title }
    panelOpen.value = true
  }

  function clearDocumentScope() {
    scopeDocument.value = null
  }

  function setPanelOpen(open: boolean) {
    panelOpen.value = open
  }

  return {
    panelOpen,
    scopeDocument,
    openDiscussDocument,
    clearDocumentScope,
    setPanelOpen,
  }
})
