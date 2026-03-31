import request from '@/utils/request'
import type { UserInfo } from './auth'

export interface UserCreateParams {
  username: string
  nickname: string
  phone?: string
  email?: string
  password: string
  admin: boolean
}

export interface UserUpdateParams {
  nickname?: string
  phone?: string
  email?: string
  admin?: boolean
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function getUsers(keyword?: string): Promise<Result<UserInfo[]>> {
  return request.get('/users', { params: keyword ? { keyword } : {} })
}

export function getUser(id: number): Promise<Result<UserInfo>> {
  return request.get(`/users/${id}`)
}

export function createUser(data: UserCreateParams): Promise<Result<UserInfo>> {
  return request.post('/users', data)
}

export function updateUser(id: number, data: UserUpdateParams): Promise<Result<UserInfo>> {
  return request.put(`/users/${id}`, data)
}

export function changePassword(id: number, password: string): Promise<Result<void>> {
  return request.put(`/users/${id}/password`, { password })
}

export function deleteUser(id: number): Promise<Result<void>> {
  return request.delete(`/users/${id}`)
}
