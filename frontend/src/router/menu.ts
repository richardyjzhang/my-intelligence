import type { Component } from 'vue'
import {
  SearchOutline,
  LibraryOutline,
  DocumentTextOutline,
  CutOutline,
  SettingsOutline,
  PeopleOutline,
  PricetagsOutline,
  ColorPaletteOutline,
} from '@vicons/ionicons5'

export interface MenuItemConfig {
  label: string
  key: string
  path?: string
  icon: Component
  component?: () => Promise<{ default: Component }>
  children?: MenuItemConfig[]
  adminOnly?: boolean
}

export const menuConfig: MenuItemConfig[] = [
  {
    label: '知识检索',
    key: 'knowledge-search-group',
    icon: SearchOutline,
    children: [
      {
        label: '知识检索',
        key: '/knowledge-search',
        icon: SearchOutline,
        path: 'knowledge-search',
        component: () => import('@/views/knowledge-search/index.vue'),
      },
    ],
  },
  {
    label: '知识管理',
    key: 'knowledge-group',
    icon: LibraryOutline,
    children: [
      {
        label: '文档知识',
        key: '/knowledge/documents',
        icon: DocumentTextOutline,
        path: 'knowledge/documents',
        component: () => import('@/views/knowledge/documents/index.vue'),
      },
      {
        label: '碎片知识',
        key: '/knowledge/fragments',
        icon: CutOutline,
        path: 'knowledge/fragments',
        component: () => import('@/views/knowledge/fragments/index.vue'),
      },
    ],
  },
  {
    label: '系统管理',
    key: 'settings-group',
    icon: SettingsOutline,
    children: [
      {
        label: '用户管理',
        key: '/settings/users',
        icon: PeopleOutline,
        path: 'settings/users',
        component: () => import('@/views/settings/users/index.vue'),
        adminOnly: true,
      },
      {
        label: '标签管理',
        key: '/settings/tags',
        icon: PricetagsOutline,
        path: 'settings/tags',
        component: () => import('@/views/settings/tags/index.vue'),
      },
      {
        label: '个性化',
        key: '/settings/personalization',
        icon: ColorPaletteOutline,
        path: 'settings/personalization',
        component: () => import('@/views/settings/personalization/index.vue'),
      },
    ],
  },
]
