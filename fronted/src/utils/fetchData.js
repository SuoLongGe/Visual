/**
 * 数据获取封装
 */
import { ref } from 'vue'

/**
 * 创建数据获取组合式函数
 * @param {Function} apiFunction - API调用函数
 * @returns {Object} 包含data, loading, error, execute的对象
 */
export function useFetchData(apiFunction) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const execute = async (...args) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiFunction(...args)
      data.value = response
      return response
    } catch (err) {
      // 提取更友好的错误信息
      const errorMessage = err.message || err.originalError?.message || '请求失败'
      error.value = errorMessage
      console.error('数据获取失败:', {
        error: err,
        message: errorMessage,
        status: err.status,
        data: err.data
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    execute
  }
}

/**
 * 创建带参数的数据获取组合式函数
 * @param {Function} apiFunction - API调用函数
 * @param {Array} initialParams - 初始参数
 * @returns {Object} 包含data, loading, error, execute的对象
 */
export function useFetchDataWithParams(apiFunction, initialParams = []) {
  const { data, loading, error, execute } = useFetchData(apiFunction)
  
  // 立即执行（如果提供了初始参数）
  if (initialParams.length > 0) {
    execute(...initialParams)
  }

  return {
    data,
    loading,
    error,
    execute
  }
}

