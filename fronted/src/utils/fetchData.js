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

/**
 * 创建支持缓存的数据获取组合式函数
 * @param {Function} apiFunction - API调用函数
 * @param {string} cacheKey - 缓存键名
 * @param {number} cacheDuration - 缓存持续时间（毫秒），默认24小时
 * @returns {Object} 包含data, loading, error, execute的对象
 */
export function useCachedFetchData(apiFunction, cacheKey, cacheDuration = 24 * 60 * 60 * 1000) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 从缓存加载数据
  const loadFromCache = () => {
    try {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const parsed = JSON.parse(cached)
        const now = Date.now()

        // 检查缓存是否过期
        if (parsed.timestamp && (now - parsed.timestamp) < cacheDuration) {
          console.log(`从缓存加载数据: ${cacheKey}`)
          data.value = parsed.data
          return true
        } else {
          // 缓存过期，清除
          localStorage.removeItem(cacheKey)
          console.log(`缓存过期，清除: ${cacheKey}`)
        }
      }
    } catch (err) {
      console.error('读取缓存失败:', err)
      localStorage.removeItem(cacheKey) // 清除损坏的缓存
    }
    return false
  }

  // 保存数据到缓存
  const saveToCache = (dataToCache) => {
    try {
      const cacheData = {
        data: dataToCache,
        timestamp: Date.now()
      }
      localStorage.setItem(cacheKey, JSON.stringify(cacheData))
      console.log(`数据已保存到缓存: ${cacheKey}`)
    } catch (err) {
      console.error('保存缓存失败:', err)
    }
  }

  const execute = async (...args) => {
    // 首先尝试从缓存加载
    if (loadFromCache()) {
      return data.value
    }

    // 缓存不存在或过期，从API加载
    loading.value = true
    error.value = null

    try {
      console.log(`从API加载数据: ${cacheKey}`)
      const response = await apiFunction(...args)
      data.value = response

      // 保存到缓存
      saveToCache(response)

      return response
    } catch (err) {
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

