<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NIcon } from 'naive-ui'
import { LibraryOutline } from '@vicons/ionicons5'

const router = useRouter()
const username = ref('')
const password = ref('')

function handleLogin() {
  router.push('/')
}
</script>

<template>
  <div class="login-container">
    <NCard class="login-card">
      <template #header>
        <div class="login-header">
          <span class="login-badge">
            <NIcon :component="LibraryOutline" :size="28" />
          </span>
          <h2 class="login-title">个人知识库</h2>
        </div>
      </template>
      <NForm @submit.prevent="handleLogin">
        <NFormItem label="用户名">
          <NInput v-model:value="username" placeholder="请输入用户名" />
        </NFormItem>
        <NFormItem label="密码">
          <NInput v-model:value="password" type="password" placeholder="请输入密码" />
        </NFormItem>
        <NButton type="primary" block attr-type="submit">登录</NButton>
      </NForm>
    </NCard>
  </div>
</template>
