/**
 * 城市分析API
 */
import apiClient from './apiClient.js'

/**
 * 获取城市分析数据
 * @param {number} limit - 返回城市数量限制
 * @param {number} minJobs - 最小职位数量过滤
 * @returns {Promise<Object>} 城市分析数据
 */
export async function getCityAnalysis(limit = 10, minJobs = 0) {
  return await apiClient.get('/charts/city', {
    params: { limit, min_jobs: minJobs }
  })
}

/**
 * 获取城市详细信息
 * @param {string} cityName - 城市名称
 * @returns {Promise<Object>} 城市详细信息
 */
export async function getCityDetail(cityName) {
  return await apiClient.get(`/charts/city/detail/${encodeURIComponent(cityName)}`)
}

/**
 * 比较多个城市
 * @param {string[]} cities - 城市名称数组
 * @returns {Promise<Object>} 城市比较数据
 */
export async function compareCities(cities) {
  return await apiClient.post('/charts/city/compare', { cities })
}

