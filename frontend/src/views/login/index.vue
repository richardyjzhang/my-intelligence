<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { hashPassword } from '@/utils/crypto'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const hashed = await hashPassword(username.value, password.value)
    await authStore.login({ username: username.value, password: hashed })
    void router.push('/')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '登录失败'
    message.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <NCard class="login-card">
      <template #header>
        <div class="login-header">
          <img src="/favicon.svg" alt="logo" class="login-badge" />
          <h2 class="login-title">拾知 · 个人知识管理系统</h2>
        </div>
      </template>
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
        <NButton type="primary" block attr-type="submit" :loading="loading">登录</NButton>
      </NForm>
    </NCard>
  </div>
</template>
