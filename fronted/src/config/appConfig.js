/**
 * 应用全局配置
 */
export const appConfig = {
  // API配置
  api: {
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
    timeout: 10000
  },
  
  // 主题配置
  theme: {
    primaryColor: '#667eea',
    secondaryColor: '#764ba2',
    backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  
  // 图表配置
  chart: {
    defaultHeight: 600,
    defaultWidth: '100%',
    animationDuration: 750
  },
  
  // 分页配置
  pagination: {
    defaultPageSize: 10,
    pageSizeOptions: [10, 20, 50, 100]
  }
}

