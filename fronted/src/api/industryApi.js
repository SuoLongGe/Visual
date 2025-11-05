/**
 * 行业分析API
 */
import apiClient from './apiClient.js'

/**
 * 获取行业分析数据
 * @param {number} limit - 返回行业数量限制
 * @param {number} minJobs - 最小职位数量过滤
 * @returns {Promise<Object>} 行业分析数据
 */
export async function getIndustryAnalysis(limit = 10, minJobs = 0) {
  return await apiClient.get('/charts/industry', {
    params: { limit, min_jobs: minJobs }
  })
}

/**
 * 获取行业薪资分析
 * @returns {Promise<Object>} 行业薪资数据
 */
export async function getIndustrySalary() {
  return await apiClient.get('/charts/industry/salary')
}

/**
 * 获取行业详细信息
 * @param {string} industryName - 行业名称
 * @returns {Promise<Object>} 行业详细信息
 */
export async function getIndustryDetail(industryName) {
  return await apiClient.get(`/charts/industry/detail/${encodeURIComponent(industryName)}`)
}

