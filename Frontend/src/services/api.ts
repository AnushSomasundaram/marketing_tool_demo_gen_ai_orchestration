import axios from 'axios'
import { clearStoredAccessCode, getStoredAccessCode } from './accessCode'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const isMockMode = import.meta.env.VITE_USE_MOCK_API === 'true'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
})

apiClient.interceptors.request.use((config) => {
  const code = getStoredAccessCode()
  if (code) config.headers['X-Access-Code'] = code
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getStoredAccessCode()) {
      // Code was valid earlier this session but got rejected now (cleared
      // server-side, or never actually matched) — force back to the gate
      // rather than surface a confusing generic error deep in the app.
      clearStoredAccessCode()
      window.location.reload()
    }
    const message = error.response?.data?.message || error.message || 'Something went wrong'
    return Promise.reject(new Error(message))
  },
)
