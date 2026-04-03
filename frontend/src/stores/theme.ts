import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { buildNaiveThemeOverrides } from '@/theme/naive'
import { THEME_PRESETS, type ThemePreset } from '@/theme/presets'
import { themePresetFromPrimaryHex } from '@/theme/derive'
import { getPersonalization, getThemeOptions } from '@/api/personalization'

const STORAGE_KEY = 'my-intelligence-theme'
const DEFAULT_THEME_ID = 'zhihu-blue'
const DEFAULT_BORDER_RADIUS = '0.375rem'

interface ThemeStorage {
  themeId: string
  borderRadius: string
}

function loadStorage(): ThemeStorage {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) as ThemeStorage
  } catch {
    // ignore
  }
  return { themeId: DEFAULT_THEME_ID, borderRadius: DEFAULT_BORDER_RADIUS }
}

function saveStorage(data: ThemeStorage) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

function applyPresetToDocument(preset: ThemePreset) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.style.setProperty('--theme-primary', preset.primary)
  root.style.setProperty('--theme-primary-hover', preset.primaryHover)
  root.style.setProperty('--theme-primary-pressed', preset.primaryPressed)
  root.style.setProperty('--theme-primary-suppl', preset.primarySuppl)
}

export const useThemeStore = defineStore('theme', () => {
  const stored = loadStorage()

  const currentThemeId = ref(stored.themeId)
  const borderRadius = ref(stored.borderRadius)
  /** 已登录时由服务端个性化覆盖本地预设 */
  const serverPreset = ref<ThemePreset | null>(null)

  const fallbackPreset: ThemePreset = THEME_PRESETS.find((p) => p.id === DEFAULT_THEME_ID)!

  const currentPreset = computed<ThemePreset>(() => {
    if (serverPreset.value) return serverPreset.value
    return THEME_PRESETS.find((p) => p.id === currentThemeId.value) ?? fallbackPreset
  })

  const themeOverrides = computed(() =>
    buildNaiveThemeOverrides(currentPreset.value, borderRadius.value),
  )

  function persist() {
    saveStorage({ themeId: currentThemeId.value, borderRadius: borderRadius.value })
  }

  function setTheme(id: string) {
    const preset = THEME_PRESETS.find((p) => p.id === id)
    if (!preset) return
    serverPreset.value = null
    currentThemeId.value = id
    applyPresetToDocument(preset)
    persist()
  }

  function setBorderRadius(radius: string) {
    borderRadius.value = radius
    persist()
  }

  function applyToDocument() {
    applyPresetToDocument(currentPreset.value)
  }

  /** 使用已算好的服务端主题（如个性化页保存后避免重复请求） */
  function applyServerPreset(preset: ThemePreset) {
    serverPreset.value = preset
    applyPresetToDocument(preset)
  }

  function clearServerTheme() {
    serverPreset.value = null
    applyPresetToDocument(currentPreset.value)
  }

  /** 拉取当前用户个性化与主题选项并应用主题色 */
  async function applyFromServer() {
    try {
      const [mineRes, optsRes] = await Promise.all([getPersonalization(), getThemeOptions()])
      if (mineRes.code !== 200 || optsRes.code !== 200) return
      const title = mineRes.data.themeTitle
      const opt = optsRes.data.find((o) => o.title === title)
      if (!opt) return
      applyServerPreset(themePresetFromPrimaryHex(title, opt.primaryHex))
    } catch {
      // 未登录或网络错误时忽略
    }
  }

  // 初始化时立刻应用一次 CSS 变量
  applyPresetToDocument(currentPreset.value)

  return {
    themePresets: THEME_PRESETS,
    currentThemeId,
    currentPreset,
    borderRadius,
    themeOverrides,
    setTheme,
    setBorderRadius,
    applyToDocument,
    applyServerPreset,
    clearServerTheme,
    applyFromServer,
  }
})
