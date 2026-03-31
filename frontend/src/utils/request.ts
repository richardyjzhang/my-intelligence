import axios from 'axios'
import router from '@/router'

const TOKEN_KEY = 'my-intelligence-token'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = token
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      void router.push('/login')
    }
    return Promise.reject(error)
  },
)

export { TOKEN_KEY }
export default request
