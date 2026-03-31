import request from '@/utils/request'
import type { TagInfo } from '@/api/tag'

export interface DocumentInfo {
  id: number
  title: string
  code: string | null
  publishDate: string | null
  status: number
  url: string | null
  remark: string | null
  fileName: string
  filePath: string
  fileSize: number
  creator: {
    id: number
    username: string
    nickname: string
  }
  tags: TagInfo[]
  createTime: string
  updateTime: string
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export const STATUS_OPTIONS = [
  { label: '待识别', value: 1 },
  { label: '识别完成', value: 2 },
  { label: '处理完成', value: 3 },
  { label: '处理失败', value: -1 },
]

export const STATUS_MAP: Record<number, { label: string; type: 'warning' | 'info' | 'success' | 'error' }> = {
  1: { label: '待识别', type: 'warning' },
  2: { label: '识别完成', type: 'info' },
  3: { label: '处理完成', type: 'success' },
  [-1]: { label: '处理失败', type: 'error' },
}

export function getDocuments(keyword?: string, tagIds?: number[]): Promise<Result<DocumentInfo[]>> {
  const params: Record<string, any> = {}
  if (keyword) params.keyword = keyword
  if (tagIds && tagIds.length > 0) params.tagIds = tagIds.join(',')
  return request.get('/documents', { params })
}

export function getDocument(id: number): Promise<Result<DocumentInfo>> {
  return request.get(`/documents/${id}`)
}

export function createDocument(formData: FormData): Promise<Result<DocumentInfo>> {
  return request.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function updateDocument(id: number, formData: FormData): Promise<Result<DocumentInfo>> {
  return request.put(`/documents/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteDocument(id: number): Promise<Result<void>> {
  return request.delete(`/documents/${id}`)
}

export function getPreviewUrl(id: number): string {
  return `/api/documents/${id}/preview`
}

export function getDownloadUrl(id: number): string {
  return `/api/documents/${id}/download`
}
