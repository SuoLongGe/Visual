import apiClient from './apiClient'

/**
 * 获取代表性城市列表
 */
export const getRepresentativeCities = async () => {
  const response = await apiClient.get('/q1/cities')
  return response.data
}

/**
 * 获取散点气泡图数据
 * @param {string} city - 城市名称
 */
export const getScatterData = async (city) => {
  const response = await apiClient.get('/q1/scatter', {
    params: { city }
  })
  return response.data
}

/**
 * 获取职位层级列表
 */
export const getJobLevels = async () => {
  const response = await apiClient.get('/q1/job-levels')
  return response.data
}

/**
 * 获取行业类别列表
 * @param {string} city - 城市名称（可选）
 */
export const getIndustries = async (city = null) => {
  const response = await apiClient.get('/q1/industries', {
    params: city ? { city } : {}
  })
  return response.data
}

