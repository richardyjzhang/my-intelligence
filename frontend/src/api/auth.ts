import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  id: number
  username: string
  nickname: string
  admin: boolean
}

export interface UserInfo {
  id: number
  username: string
  nickname: string
  phone: string | null
  email: string | null
  admin: boolean
  createTime: string
  updateTime: string
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function login(params: LoginParams): Promise<Result<LoginResult>> {
  return request.post('/auth/login', params)
}

export function logout(): Promise<Result<void>> {
  return request.post('/auth/logout')
}

export function getMe(): Promise<Result<UserInfo>> {
  return request.get('/auth/me')
}
