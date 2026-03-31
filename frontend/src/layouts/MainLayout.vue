<script setup lang="ts">
import { computed, h, watch, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLayoutContent,
  NMenu,
  NIcon,
  NDropdown,
  type MenuOption,
} from 'naive-ui'
import { LogOutOutline, PersonOutline, CloseOutline } from '@vicons/ionicons5'
import { menuConfig, type MenuItemConfig } from '@/router/menu'
import { useTabsStore } from '@/stores/tabs'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const tabsStore = useTabsStore()
const authStore = useAuthStore()

watch(
  () => route.path,
  (path) => {
    const title = typeof route.meta.title === 'string' ? route.meta.title : path
    tabsStore.addTab(path, title)
  },
  { immediate: true },
)

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

function filterMenuItems(items: MenuItemConfig[]): MenuItemConfig[] {
  return items
    .filter((item) => !item.adminOnly || authStore.isAdmin)
    .map((item) => ({
      ...item,
      children: item.children ? filterMenuItems(item.children) : undefined,
    }))
    .filter((item) => !item.children || item.children.length > 0)
}

function buildMenuOptions(items: MenuItemConfig[]): MenuOption[] {
  return items.map((item) => ({
    label: item.label,
    key: item.key,
    icon: renderIcon(item.icon),
    children: item.children ? buildMenuOptions(item.children) : undefined,
  }))
}

const menuOptions = computed<MenuOption[]>(() => buildMenuOptions(filterMenuItems(menuConfig)))

const menuGroupKeys = menuConfig
  .filter((item) => item.children)
  .map((item) => item.key)

const activeMenuKey = computed(() => {
  const meta = route.meta
  return typeof meta.activeMenu === 'string' ? meta.activeMenu : route.path
})

function handleMenuUpdate(key: string) {
  void router.push(key)
}

function handleTabClick(path: string) {
  tabsStore.setActive(path)
  void router.push(path)
}

function closeTab(path: string) {
  if (tabsStore.tabs.length <= 1) return
  const wasActive = tabsStore.activeTab === path
  tabsStore.removeTab(path)
  if (wasActive) {
    void router.push(tabsStore.activeTab)
  }
}

function handleTabClose(e: Event, path: string) {
  e.stopPropagation()
  closeTab(path)
}

function handleTabMousedown(e: MouseEvent, path: string) {
  if (e.button === 1) {
    e.preventDefault()
    closeTab(path)
  }
}

const userDropdownOptions = [
  {
    label: '退出登录',
    key: 'logout',
    icon: renderIcon(LogOutOutline),
  },
]

async function handleUserDropdown(key: string) {
  if (key === 'logout') {
    await authStore.logout()
    void router.push('/login')
  }
}

const displayName = computed(() => authStore.user?.nickname || authStore.user?.username || '用户')
</script>

<template>
  <NLayout class="app-root">
    <NLayoutHeader bordered class="app-topbar">
      <div class="app-topbar__left">
        <div class="app-topbar__logo">
          <img src="/favicon.svg" alt="logo" class="app-topbar__badge" />
          <span class="app-topbar__name">拾知 · 个人知识管理系统</span>
        </div>
      </div>
      <div class="app-topbar__right">
        <span class="app-topbar__hint">ShiZhi Knowledge Management System</span>
        <NDropdown :options="userDropdownOptions" trigger="click" @select="handleUserDropdown">
          <div class="app-topbar__user">
            <NIcon :component="PersonOutline" :size="18" />
            <span>{{ displayName }}</span>
          </div>
        </NDropdown>
      </div>
    </NLayoutHeader>

    <NLayout has-sider class="app-body">
      <NLayoutSider
        bordered
        :width="220"
        :native-scrollbar="false"
        content-style="padding: 0.5rem;"
        class="app-sidebar"
      >
        <NMenu
          :value="activeMenuKey"
          :options="menuOptions"
          :indent="24"
          accordion
          :default-expanded-keys="menuGroupKeys"
          @update:value="handleMenuUpdate"
        />
      </NLayoutSider>

      <NLayout>
        <div class="tab-bar">
          <div class="tab-bar__scroll">
            <div
              v-for="tab in tabsStore.tabs"
              :key="tab.path"
              class="tab-item"
              :class="{ 'tab-item--active': tabsStore.activeTab === tab.path }"
              @click="handleTabClick(tab.path)"
              @mousedown="handleTabMousedown($event, tab.path)"
            >
              <NIcon v-if="tab.icon" :component="tab.icon" :size="15" class="tab-item__icon" />
              <span class="tab-item__title">{{ tab.title }}</span>
              <span
                v-if="tabsStore.tabs.length > 1"
                class="tab-item__close"
                @click="handleTabClose($event, tab.path)"
              >
                <NIcon :component="CloseOutline" :size="14" />
              </span>
            </div>
          </div>
        </div>

        <NLayoutContent
          content-style="padding: 0 1.25rem 1.25rem;"
          class="app-content"
          :native-scrollbar="false"
        >
          <RouterView />
        </NLayoutContent>
      </NLayout>
    </NLayout>
  </NLayout>
</template>
