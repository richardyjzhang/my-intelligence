import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { menuConfig, type MenuItemConfig } from './menu'

function flattenRoutes(items: MenuItemConfig[]): RouteRecordRaw[] {
  const routes: RouteRecordRaw[] = []
  for (const item of items) {
    if (item.path && item.component) {
      routes.push({
        path: item.path,
        name: item.path.replace(/\//g, '-'),
        meta: { title: item.label },
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

export default router
