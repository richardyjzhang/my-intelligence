import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { menuConfig, type MenuItemConfig } from './menu'
import { useAuthStore } from '@/stores/auth'
import { TOKEN_KEY } from '@/utils/request'

function flattenRoutes(items: MenuItemConfig[]): RouteRecordRaw[] {
  const routes: RouteRecordRaw[] = []
  for (const item of items) {
    if (item.path && item.component) {
      routes.push({
        path: item.path,
        name: item.path.replace(/\//g, '-'),
        meta: { title: item.label, adminOnly: item.adminOnly === true },
        component: item.component,
      })
    }
    if (item.children) {
      routes.push(...flattenRoutes(item.children))
    }
  }
  return routes
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/login/index.vue'),
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/knowledge-search',
      children: flattenRoutes(menuConfig),
    },
  ],
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem(TOKEN_KEY)

  if (to.path === '/login') {
    if (token) return '/'
    return true
  }

  if (!token) {
    return '/login'
  }

  const authStore = useAuthStore()
  if (!authStore.user) {
    try {
      await authStore.fetchMe()
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      return '/login'
    }
  }

  if (to.meta.adminOnly && !authStore.isAdmin) {
    return '/'
  }

  return true
})

export default router
