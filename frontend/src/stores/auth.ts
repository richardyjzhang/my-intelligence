import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi, getMe } from '@/api/auth'
import type { LoginParams } from '@/api/auth'
import { TOKEN_KEY } from '@/utils/request'

export interface AuthUser {
  id: number
  username: string
  nickname: string
  admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<AuthUser | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.admin === true)

  async function login(params: LoginParams) {
    const res = await loginApi(params)
    if (res.code === 200) {
      token.value = res.data.token
      localStorage.setItem(TOKEN_KEY, res.data.token)
      user.value = {
        id: res.data.id,
        username: res.data.username,
        nickname: res.data.nickname,
        admin: res.data.admin,
      }
    } else {
      throw new Error(res.message)
    }
  }

  async function logout() {
    try {
      await logoutApi()
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function fetchMe() {
    const res = await getMe()
    if (res.code === 200) {
      user.value = {
        id: res.data.id,
        username: res.data.username,
        nickname: res.data.nickname,
        admin: res.data.admin,
      }
    }
  }

  return { token, user, isLoggedIn, isAdmin, login, logout, fetchMe }
})
