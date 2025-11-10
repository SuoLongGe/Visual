/**
 * 应用全局配置
 */
export const appConfig = {
  // API配置
  api: {
    // 优先使用环境变量，否则使用代理模式 '/api'
    // 开发时如果需要直连，可以设置 VITE_API_BASE_URL=http://localhost:5001/api
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 50000  // 增加超时时间，因为读取Excel和Q1散点图可能需要较长时间
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
