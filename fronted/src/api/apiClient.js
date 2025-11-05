/**
 * Axios基础实例配置
 */
import axios from 'axios'
import { appConfig } from '@/config/appConfig.js'

// 创建axios实例
const apiClient = axios.create({
  baseURL: appConfig.api.baseURL,
  timeout: appConfig.api.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API请求失败:', error)
    return Promise.reject(error)
  }
)

export default apiClient

