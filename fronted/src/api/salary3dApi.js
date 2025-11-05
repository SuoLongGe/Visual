/**
 * 三维薪资分析API
 */
import apiClient from './apiClient.js'

/**
 * 获取三维薪资数据（经验-学历-薪资）
 * @returns {Promise<Object>} 三维薪资数据
 */
export async function get3DSalaryData() {
  return await apiClient.get('/charts/3d/experience-education-salary')
}

/**
 * 获取箱线图数据
 * @param {Object} filters - 筛选条件
 * @param {string} filters.experience - 工作经验
 * @param {string} filters.education - 学历
 * @param {string} [filters.city] - 城市（可选）
 * @param {string} [filters.company_type] - 公司类型（可选）
 * @returns {Promise<Object>} 箱线图数据
 */
export async function getBoxplotData(filters = {}) {
  const params = new URLSearchParams()
  
  if (filters.experience) {
    params.append('experience', filters.experience)
  }
  if (filters.education) {
    params.append('education', filters.education)
  }
  if (filters.city) {
    params.append('city', filters.city)
  }
  if (filters.company_type) {
    params.append('company_type', filters.company_type)
  }
  
  const queryString = params.toString()
  const url = `/charts/boxplot/salary-distribution${queryString ? '?' + queryString : ''}`
  
  return await apiClient.get(url)
}

