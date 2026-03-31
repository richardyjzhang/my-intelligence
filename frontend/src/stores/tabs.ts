import { ref, type Component } from 'vue'
import { defineStore } from 'pinia'
import { menuConfig, type MenuItemConfig } from '@/router/menu'

export interface TabItem {
  path: string
  title: string
  icon?: Component
}

function findIconByPath(path: string): Component | undefined {
  function search(items: MenuItemConfig[]): Component | undefined {
    for (const item of items) {
      if (item.key === path) return item.icon
      if (item.children) {
        const found = search(item.children)
        if (found) return found
      }
    }
    return undefined
  }
  return search(menuConfig)
}

const HOME_TAB: TabItem = {
  path: '/knowledge-search',
  title: '知识检索',
  icon: findIconByPath('/knowledge-search'),
}

export const useTabsStore = defineStore('tabs', () => {
  const tabs = ref<TabItem[]>([{ ...HOME_TAB }])
  const activeTab = ref(HOME_TAB.path)

  function addTab(path: string, title: string) {
    if (!tabs.value.some((t) => t.path === path)) {
      tabs.value.push({ path, title, icon: findIconByPath(path) })
    }
    activeTab.value = path
  }

  function removeTab(path: string) {
    const idx = tabs.value.findIndex((t) => t.path === path)
    if (idx === -1) return
    if (tabs.value.length === 1) return

    tabs.value.splice(idx, 1)
    if (activeTab.value === path) {
      const nextIdx = Math.min(idx, tabs.value.length - 1)
      activeTab.value = tabs.value[nextIdx]?.path ?? HOME_TAB.path
    }
  }

  function setActive(path: string) {
    activeTab.value = path
  }

  return { tabs, activeTab, addTab, removeTab, setActive }
})
