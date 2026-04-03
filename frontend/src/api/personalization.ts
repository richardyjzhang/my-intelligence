import request from '@/utils/request'

export interface ThemeOption {
  title: string
  primaryHex: string
}

export interface AiPersonaOption {
  title: string
  description: string
}

export interface UserPersonalization {
  userId: number
  themeTitle: string
  aiPersonaTitle: string
  aiCustomInstruction: string | null
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function getThemeOptions(): Promise<Result<ThemeOption[]>> {
  return request.get('/personalization/options/themes')
}

export function getAiPersonaOptions(): Promise<Result<AiPersonaOption[]>> {
  return request.get('/personalization/options/ai-personas')
}

export function getPersonalization(): Promise<Result<UserPersonalization>> {
  return request.get('/personalization')
}

export function saveTheme(themeTitle: string): Promise<Result<UserPersonalization>> {
  return request.put('/personalization/theme', { themeTitle })
}

export function saveAiAssistant(data: {
  aiPersonaTitle: string
  aiCustomInstruction?: string | null
}): Promise<Result<UserPersonalization>> {
  return request.put('/personalization/ai-assistant', data)
}
