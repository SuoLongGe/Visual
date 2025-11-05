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

