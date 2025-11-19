import apiClient from './apiClient'

/**
 * 获取平行坐标图数据
 * @param {string[]} jobTitles - 职位名称数组，最多3个
 */
export const getParallelCoordinatesData = async (jobTitles) => {
  const params = new URLSearchParams()
  jobTitles.forEach(title => {
    params.append('job_titles', title)
  })
  
  // apiClient的响应拦截器已经返回了response.data，所以这里直接返回即可
  const response = await apiClient.get(`/positions/parallel?${params.toString()}`)
  // response已经是 { code: 200, data: {...}, message: "..." } 格式
  return response
}

/**
 * 获取桑基图数据
 * @param {string} mode - 显示模式：all(整体)/compare(对比)
 * @param {string[]} jobTitles - 对比模式下指定的职位名称数组（可选）
 * @param {string[]} dimensions - 选择的维度数组（可选）
 */
export const getSankeyData = async (mode = 'all', jobTitles = [], dimensions = []) => {
  const params = new URLSearchParams()
  params.append('mode', mode)
  
  if (mode === 'compare' && jobTitles.length > 0) {
    jobTitles.forEach(title => {
      params.append('job_titles', title)
    })
  }
  
  if (dimensions.length > 0) {
    dimensions.forEach(dim => {
      params.append('dimensions', dim)
    })
  }
  
  // apiClient的响应拦截器已经返回了response.data，所以这里直接返回即可
  const response = await apiClient.get(`/positions/sankey?${params.toString()}`)
  // response已经是 { code: 200, data: {...}, message: "..." } 格式
  return response
}

/**
 * 获取嵌套柱状图数据
 * @param {string[]} jobTitles - 职位名称数组，最多3个
 * @param {string} detailJob - 详细分析的单个职位名称（可选）
 */
export const getNestedBarData = async (jobTitles, detailJob = null) => {
  const params = new URLSearchParams()
  jobTitles.forEach(title => {
    params.append('job_titles', title)
  })
  
  if (detailJob) {
    params.append('detail_job', detailJob)
  }
  
  const response = await apiClient.get(`/positions/nested_bar?${params.toString()}`)
  // response已经是 { code: 200, data: {...}, message: "..." } 格式
  return response
}

