/**
 * 应用全局配置
 */
export const appConfig = {
  // API配置
  api: {
    // 使用相对路径，通过 Vite 代理访问后端
    // 如果需要直接访问，可以设置为 'http://localhost:5000/api'
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 70000  // 增加到50秒，因为读取Excel文件可能需要较长时间
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

