<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NInput, NButton, NIcon, NSpin, useMessage } from 'naive-ui'
import { SaveOutline } from '@vicons/ionicons5'
import {
  getThemeOptions,
  getAiPersonaOptions,
  getPersonalization,
  saveTheme,
  saveAiAssistant,
} from '@/api/personalization'
import type { ThemeOption, AiPersonaOption } from '@/api/personalization'
import { useThemeStore } from '@/stores/theme'
import { themePresetFromPrimaryHex } from '@/theme/derive'

const message = useMessage()
const themeStore = useThemeStore()

function applyThemeFromTitle(title: string) {
  const opt = themeOptions.value.find((o) => o.title === title)
  if (opt) {
    themeStore.applyServerPreset(themePresetFromPrimaryHex(title, opt.primaryHex))
  }
}

const loading = ref(false)
const savingTheme = ref(false)
const savingAi = ref(false)

const themeOptions = ref<ThemeOption[]>([])
const personaOptions = ref<AiPersonaOption[]>([])

/** 当前选中（与后端存的中文标题一致） */
const selectedThemeTitle = ref('')
const selectedPersonaTitle = ref('')
const aiCustomInstruction = ref('')

async function loadAll() {
  loading.value = true
  try {
    const [themesRes, personasRes, mineRes] = await Promise.all([
      getThemeOptions(),
      getAiPersonaOptions(),
      getPersonalization(),
    ])
    if (themesRes.code !== 200) throw new Error(themesRes.message)
    if (personasRes.code !== 200) throw new Error(personasRes.message)
    if (mineRes.code !== 200) throw new Error(mineRes.message)
    themeOptions.value = themesRes.data
    personaOptions.value = personasRes.data
    const m = mineRes.data
    selectedThemeTitle.value = m.themeTitle
    selectedPersonaTitle.value = m.aiPersonaTitle
    aiCustomInstruction.value = m.aiCustomInstruction ?? ''
    applyThemeFromTitle(m.themeTitle)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function selectTheme(t: ThemeOption) {
  selectedThemeTitle.value = t.title
}

function selectPersona(p: AiPersonaOption) {
  selectedPersonaTitle.value = p.title
}

async function handleSaveTheme() {
  if (!selectedThemeTitle.value) {
    message.warning('请选择主题色')
    return
  }
  savingTheme.value = true
  try {
    const res = await saveTheme(selectedThemeTitle.value)
    if (res.code !== 200) {
      message.error(res.message || '保存失败')
      return
    }
    message.success('主题色已保存')
    selectedThemeTitle.value = res.data.themeTitle
    applyThemeFromTitle(res.data.themeTitle)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    savingTheme.value = false
  }
}

async function handleSaveAi() {
  if (!selectedPersonaTitle.value) {
    message.warning('请选择人设')
    return
  }
  savingAi.value = true
  try {
    const res = await saveAiAssistant({
      aiPersonaTitle: selectedPersonaTitle.value,
      aiCustomInstruction: aiCustomInstruction.value.trim() || null,
    })
    if (res.code !== 200) {
      message.error(res.message || '保存失败')
      return
    }
    message.success('AI 助手设定已保存')
    selectedPersonaTitle.value = res.data.aiPersonaTitle
    aiCustomInstruction.value = res.data.aiCustomInstruction ?? ''
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    savingAi.value = false
  }
}

onMounted(() => {
  void loadAll()
})
</script>

<template>
  <NCard class="page-card">
    <div class="page-card__content personalization-page">
      <NSpin :show="loading">
        <!-- 风格个性化 -->
        <section class="personalization-section">
          <div class="personalization-section__head">
            <h3 class="personalization-section__title">风格个性化</h3>
            <NButton type="primary" class="personalization-section__save" :loading="savingTheme" @click="handleSaveTheme">
              <template #icon>
                <NIcon :component="SaveOutline" />
              </template>
              保存
            </NButton>
          </div>
          <p class="personalization-section__label">主题色</p>
          <div class="theme-grid">
            <button
              v-for="t in themeOptions"
              :key="t.title"
              type="button"
              class="theme-card"
              :class="{ 'theme-card--active': selectedThemeTitle === t.title }"
              @click="selectTheme(t)"
            >
              <span class="theme-card__swatch" :style="{ backgroundColor: t.primaryHex }" />
              <div class="theme-card__row">
                <span class="theme-card__name">{{ t.title }}</span>
                <span class="theme-card__hex">{{ t.primaryHex }}</span>
              </div>
            </button>
          </div>
        </section>

        <!-- AI 助手个性化 -->
        <section class="personalization-section personalization-section--ai">
          <div class="personalization-section__head">
            <h3 class="personalization-section__title">AI 助手个性化</h3>
            <NButton type="primary" class="personalization-section__save" :loading="savingAi" @click="handleSaveAi">
              <template #icon>
                <NIcon :component="SaveOutline" />
              </template>
              保存
            </NButton>
          </div>
          <p class="personalization-section__label">人设</p>
          <div class="persona-grid">
            <button
              v-for="p in personaOptions"
              :key="p.title"
              type="button"
              class="persona-card"
              :class="{ 'persona-card--active': selectedPersonaTitle === p.title }"
              @click="selectPersona(p)"
            >
              <span class="persona-card__title">{{ p.title }}</span>
              <span class="persona-card__desc">{{ p.description }}</span>
            </button>
          </div>
          <p class="personalization-section__label personalization-section__label--mt">补充说明</p>
          <NInput
            v-model:value="aiCustomInstruction"
            type="textarea"
            class="persona-textarea"
            placeholder="例如：称呼我为「总监」；回答里少用网络梗；涉及金额一律带万元单位……"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 1 }"
            :maxlength="4000"
            show-count
          />
        </section>
      </NSpin>
    </div>
  </NCard>
</template>

<style scoped>
.personalization-page {
  max-width: 1200px;
}

.personalization-section {
  margin-top: 1.5rem;
  padding: 1.25rem 1.5rem;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
}

.personalization-section--ai {
  margin-top: 1.25rem;
}

.personalization-section__head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.personalization-section__save {
  flex-shrink: 0;
  margin-left: auto;
}

.personalization-section__title {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 1.0625rem;
  font-weight: 600;
  color: #1d2129;
}

.personalization-section__label {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4e5969;
}

.personalization-section__label--mt {
  margin-top: 1.25rem;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem 1rem;
}

@media (max-width: 1100px) {
  .theme-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.theme-card {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
  padding: 0.75rem 0.875rem;
  text-align: left;
  cursor: pointer;
  background: #fafafa;
  border: 2px solid #e5e6eb;
  border-radius: 8px;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.theme-card:hover {
  border-color: #c9cdd4;
}

.theme-card--active {
  border-color: var(--theme-primary, #0084ff);
  box-shadow: 0 0 0 1px var(--theme-primary, #0084ff);
  background: #fff;
}

.theme-card__swatch {
  width: 100%;
  height: 2.5rem;
  border-radius: 6px;
  flex-shrink: 0;
}

.theme-card__row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.5rem;
  flex-wrap: nowrap;
  min-width: 0;
}

.theme-card__name {
  flex: 0 1 auto;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1d2129;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.theme-card__hex {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-family: ui-monospace, monospace;
  color: #86909c;
}

.persona-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
}

@media (max-width: 1100px) {
  .persona-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.persona-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.375rem;
  padding: 0.75rem 0.875rem;
  min-height: 4.5rem;
  text-align: left;
  cursor: pointer;
  background: #fafafa;
  border: 2px solid #e5e6eb;
  border-radius: 8px;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.persona-card:hover {
  border-color: #c9cdd4;
}

.persona-card--active {
  border-color: var(--theme-primary, #0084ff);
  box-shadow: 0 0 0 1px var(--theme-primary, #0084ff);
  background: #fff;
}

.persona-card__title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.3;
}

.persona-card__desc {
  font-size: 0.75rem;
  color: #86909c;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.persona-textarea {
  display: block;
  width: 100%;
}

.persona-textarea :deep(.n-input-wrapper) {
  width: 100%;
}

.persona-textarea :deep(textarea) {
  width: 100%;
  box-sizing: border-box;
  resize: none;
  overflow-x: hidden;
  overflow-y: auto;
}
</style>
