/**
 * 数据概览API
 */
import apiClient from './apiClient.js'

/**
 * 获取数据概览
 * @returns {Promise<Object>} 概览数据
 */
export async function getOverview() {
  return await apiClient.get('/overview')
}

/**
 * 获取多维度词云数据（职位、教育、经验、薪资）
 * @returns {Promise<Object>} 词云数据
 */
export async function getMultiWordCloud() {
  return await apiClient.get('/wordcloud/multi')
}

