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
    // 详细的错误信息
    let errorMessage = '请求失败'
    
    if (error.response) {
      // 服务器返回了错误状态码
      errorMessage = `服务器错误: ${error.response.status} - ${error.response.statusText}`
      if (error.response.data?.message) {
        errorMessage = error.response.data.message
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = '无法连接到服务器，请检查后端服务是否运行'
      console.error('网络请求详情:', {
        request: error.request,
        code: error.code,
        message: error.message,
        config: error.config
      })
    } else {
      // 请求配置出错
      errorMessage = error.message || '请求配置错误'
    }
    
    console.error('API请求失败:', {
      message: errorMessage,
      url: error.config?.url,
      method: error.config?.method,
      baseURL: error.config?.baseURL,
      fullURL: error.config?.baseURL + error.config?.url,
      hasResponse: !!error.response,
      hasRequest: !!error.request,
      errorCode: error.code,
      errorMessage: error.message,
      error: error
    })
    
    // 创建一个包含详细信息的错误对象
    const enhancedError = new Error(errorMessage)
    enhancedError.originalError = error
    enhancedError.status = error.response?.status
    enhancedError.data = error.response?.data
    enhancedError.code = error.code
    
    return Promise.reject(enhancedError)
  }
)

export default apiClient

