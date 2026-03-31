import request from '@/utils/request'

export interface TagInfo {
  id: number
  name: string
  color: string
  createTime: string
  updateTime: string
}

export interface TagParams {
  name: string
  color: string
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function getTags(keyword?: string): Promise<Result<TagInfo[]>> {
  return request.get('/tags', { params: keyword ? { keyword } : {} })
}

export function getTag(id: number): Promise<Result<TagInfo>> {
  return request.get(`/tags/${id}`)
}

export function createTag(data: TagParams): Promise<Result<TagInfo>> {
  return request.post('/tags', data)
}

export function updateTag(id: number, data: TagParams): Promise<Result<TagInfo>> {
  return request.put(`/tags/${id}`, data)
}

export function deleteTag(id: number): Promise<Result<void>> {
  return request.delete(`/tags/${id}`)
}
