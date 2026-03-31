import request from '@/utils/request'
import type { TagInfo } from '@/api/tag'

export interface FragmentInfo {
  id: number
  title: string
  content: string
  creator: {
    id: number
    username: string
    nickname: string
  }
  tags: TagInfo[]
  createTime: string
  updateTime: string
}

export interface FragmentParams {
  title: string
  content: string
  tagIds: number[]
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function getFragments(keyword?: string, tagId?: number): Promise<Result<FragmentInfo[]>> {
  const params: Record<string, string | number> = {}
  if (keyword) params.keyword = keyword
  if (tagId) params.tagId = tagId
  return request.get('/fragments', { params })
}

export function getFragment(id: number): Promise<Result<FragmentInfo>> {
  return request.get(`/fragments/${id}`)
}

export function createFragment(data: FragmentParams): Promise<Result<FragmentInfo>> {
  return request.post('/fragments', data)
}

export function updateFragment(id: number, data: FragmentParams): Promise<Result<FragmentInfo>> {
  return request.put(`/fragments/${id}`, data)
}

export function deleteFragment(id: number): Promise<Result<void>> {
  return request.delete(`/fragments/${id}`)
}
