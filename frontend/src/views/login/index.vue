<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { hashPassword } from '@/utils/crypto'
import SliderCaptcha from './SliderCaptcha.vue'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const verified = ref(false)
const captchaRef = ref<InstanceType<typeof SliderCaptcha> | null>(null)

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码')
    return
  }
  if (!verified.value) {
    message.warning('请先完成滑块验证')
    return
  }
  loading.value = true
  try {
    const hashed = await hashPassword(username.value, password.value)
    await authStore.login({ username: username.value, password: hashed })
    await themeStore.applyFromServer()
    void router.push('/')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '登录失败'
    message.error(msg)
    captchaRef.value?.reset()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative flex items-center justify-center min-h-screen overflow-hidden bg-[#e8ecf0]">
    <img src="/login-bg.png" alt="" class="absolute inset-0 w-full h-full object-cover z-0" />

    <div class="absolute z-1 top-1/2 left-[72%] -translate-x-1/2 -translate-y-1/2 max-md:left-1/2">
      <div
        class="w-[360px] max-md:w-[320px] p-8 pt-10 rounded-2xl border border-white/60"
        style="background: rgba(255,255,255,0.55); backdrop-filter: blur(20px) saturate(1.4); -webkit-backdrop-filter: blur(20px) saturate(1.4); box-shadow: 0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)"
      >
        <div class="flex flex-col items-center gap-2 mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" class="w-12 h-12">
            <rect width="32" height="32" rx="7" fill="#dceef5"/>
            <path d="M16 7.5a5.5 5.5 0 0 1 5.5 5.5c0 2-1.1 3.5-2.7 4.4V18.5a2.8 2.8 0 0 1-5.6 0v-1.1C11.6 16.5 10.5 15 10.5 13A5.5 5.5 0 0 1 16 7.5Z" fill="#7ebad6" opacity="0.7"/>
            <circle cx="16" cy="23.5" r="1.4" fill="#7ebad6" opacity="0.7"/>
          </svg>
          <h2 class="m-0 text-lg font-semibold text-gray-900">拾知 · 个人知识管理系统</h2>
        </div>
        <NForm @submit.prevent="handleLogin">
          <NFormItem label="用户名">
            <NInput v-model:value="username" placeholder="请输入用户名" @keydown.enter="handleLogin" />
          </NFormItem>
          <NFormItem label="密码">
            <NInput
              v-model:value="password"
              type="password"
              placeholder="请输入密码"
              show-password-on="click"
              @keydown.enter="handleLogin"
            />
          </NFormItem>
          <NFormItem :show-label="false">
            <SliderCaptcha ref="captchaRef" v-model="verified" />
          </NFormItem>
          <NButton type="primary" block attr-type="submit" :loading="loading">登录</NButton>
        </NForm>
      </div>
    </div>
  </div>
</template>
