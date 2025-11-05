/**
 * 经验分析API
 */
import apiClient from './apiClient.js'

/**
 * 获取经验分析数据
 * @param {number} limit - 返回经验级别数量限制
 * @param {number} minJobs - 最小职位数量过滤
 * @returns {Promise<Object>} 经验分析数据
 */
export async function getExperienceAnalysis(limit = 10, minJobs = 0) {
  return await apiClient.get('/charts/experience', {
    params: { limit, min_jobs: minJobs }
  })
}

/**
 * 获取经验薪资分析
 * @returns {Promise<Object>} 经验薪资数据
 */
export async function getExperienceSalary() {
  return await apiClient.get('/charts/experience/salary')
}

/**
 * 获取经验概览数据
 * @returns {Promise<Object>} 经验概览数据
 */
export async function getExperienceOverview() {
  return await apiClient.get('/charts/experience/overview')
}

