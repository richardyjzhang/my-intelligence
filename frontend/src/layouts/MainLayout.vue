<script setup lang="ts">
import { computed, h, type Component } from 'vue'
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
import { LogOutOutline, PersonOutline, BookOutline } from '@vicons/ionicons5'
import { menuConfig, type MenuItemConfig } from '@/router/menu'

const router = useRouter()
const route = useRoute()

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

function buildMenuOptions(items: MenuItemConfig[]): MenuOption[] {
  return items.map((item) => ({
    label: item.label,
    key: item.key,
    icon: renderIcon(item.icon),
    children: item.children ? buildMenuOptions(item.children) : undefined,
  }))
}

const menuOptions = computed<MenuOption[]>(() => buildMenuOptions(menuConfig))

const menuGroupKeys = menuConfig
  .filter((item) => item.children)
  .map((item) => item.key)

const activeMenuKey = computed(() => {
  const meta = route.meta
  return typeof meta.activeMenu === 'string' ? meta.activeMenu : route.path
})

const currentPageTitle = computed(() => {
  return typeof route.meta.title === 'string' ? route.meta.title : ''
})

function handleMenuUpdate(key: string) {
  void router.push(key)
}

const userDropdownOptions = [
  {
    label: '退出登录',
    key: 'logout',
    icon: renderIcon(LogOutOutline),
  },
]

function handleUserDropdown(key: string) {
  if (key === 'logout') {
    void router.push('/login')
  }
}
</script>

<template>
  <NLayout class="app-root">
    <NLayoutHeader bordered class="app-topbar">
      <div class="app-topbar__left">
        <div class="app-topbar__logo">
          <span class="app-topbar__badge">
            <NIcon :component="BookOutline" :size="20" />
          </span>
          <span class="app-topbar__name">个人知识库</span>
        </div>
      </div>
      <div class="app-topbar__right">
        <span class="app-topbar__hint">My Intelligence</span>
        <NDropdown :options="userDropdownOptions" trigger="click" @select="handleUserDropdown">
          <div class="app-topbar__user">
            <NIcon :component="PersonOutline" :size="18" />
            <span>管理员</span>
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
        <NLayoutHeader v-if="currentPageTitle" class="app-page-header">
          <h1 class="app-page-header__title">{{ currentPageTitle }}</h1>
        </NLayoutHeader>

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
