<script setup lang="ts">
import { computed, h, ref, watch, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLayoutContent,
  NMenu,
  NIcon,
  NDropdown,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NButton,
  useMessage,
  type MenuOption,
  type FormRules,
  type FormInst,
} from 'naive-ui'
import { LogOutOutline, PersonOutline, CloseOutline, LockClosedOutline } from '@vicons/ionicons5'
import { menuConfig, type MenuItemConfig } from '@/router/menu'
import { useTabsStore } from '@/stores/tabs'
import { useAuthStore } from '@/stores/auth'
import { changeMyPassword } from '@/api/auth'
import { hashPassword } from '@/utils/crypto'

const message = useMessage()

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
    label: '修改密码',
    key: 'changePassword',
    icon: renderIcon(LockClosedOutline),
  },
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
  } else if (key === 'changePassword') {
    showPasswordModal.value = true
  }
}

const displayName = computed(() => authStore.user?.nickname || authStore.user?.username || '用户')

const showPasswordModal = ref(false)
const passwordFormRef = ref<FormInst | null>(null)
const passwordLoading = ref(false)
const passwordForm = ref({
  newPassword: '',
  confirmPassword: '',
})

const passwordRules: FormRules = {
  newPassword: { required: true, message: '请输入新密码', trigger: 'blur' },
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value: string) => {
        if (value !== passwordForm.value.newPassword) {
          return new Error('两次输入的密码不一致')
        }
        return true
      },
      trigger: 'blur',
    },
  ],
}

function resetPasswordForm() {
  passwordForm.value = { newPassword: '', confirmPassword: '' }
  showPasswordModal.value = false
}

async function handleChangePassword() {
  try {
    await passwordFormRef.value?.validate()
  } catch {
    return
  }

  const username = authStore.user?.username
  if (!username) return

  passwordLoading.value = true
  try {
    const hashedNew = await hashPassword(username, passwordForm.value.newPassword)
    const res = await changeMyPassword(hashedNew)
    if (res.code === 200) {
      message.success('密码修改成功')
      resetPasswordForm()
    } else {
      message.error(res.message || '密码修改失败')
    }
  } catch {
    message.error('密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <NLayout class="app-root">
    <NLayoutHeader bordered class="app-topbar">
      <div class="app-topbar__left">
        <div class="app-topbar__logo">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="app-topbar__badge" style="color: var(--theme-primary, #008eaa)">
            <rect width="32" height="32" rx="6" fill="currentColor"/>
            <path d="M16 8C13 7 10 6.5 7 7v16c3-0.5 6 0 9 1V8Z" fill="rgba(255,255,255,0.9)"/>
            <path d="M16 8c3-1 6-1.5 9-1v16c-3-0.5-6 0-9 1V8Z" fill="rgba(255,255,255,0.65)"/>
            <path d="M16 8v16" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
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

  <NModal
    v-model:show="showPasswordModal"
    preset="card"
    title="修改密码"
    :style="{ width: '420px' }"
    :mask-closable="false"
    @after-leave="resetPasswordForm"
  >
    <NForm ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-placement="left" label-width="100">
      <NFormItem label="新密码" path="newPassword">
        <NInput v-model:value="passwordForm.newPassword" type="password" show-password-on="click" placeholder="请输入新密码" />
      </NFormItem>
      <NFormItem label="确认新密码" path="confirmPassword">
        <NInput v-model:value="passwordForm.confirmPassword" type="password" show-password-on="click" placeholder="请再次输入新密码" />
      </NFormItem>
      <div style="display: flex; justify-content: flex-end; gap: 12px">
        <NButton @click="resetPasswordForm">取消</NButton>
        <NButton type="primary" :loading="passwordLoading" @click="handleChangePassword">确认</NButton>
      </div>
    </NForm>
  </NModal>
</template>
