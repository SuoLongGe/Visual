# 前端项目说明

这是职数洞见平台的前端项目，使用 Vue 3 + Vite + D3.js 构建。

## 项目结构

```
frontend/
├── package.json          # 项目依赖与脚本
├── vite.config.js        # Vite 构建配置
├── index.html            # 入口 HTML
├── public/               # 静态资源（不参与构建）
│   └── vite.svg
└── src/                  # 源代码目录
    ├── main.js           # Vue 应用入口
    ├── App.vue           # 顶层组件
    │
    ├── assets/           # 静态资源（图片、字体等）
    │   ├── styles/
    │   │   ├── base.css  # 全局基础样式
    │   │   └── chart.css # 图表通用样式
    │   └── images/
    │
    ├── components/        # Vue 组件目录
    │   ├── tabs/         # 标签页组件
    │   │   ├── OverviewTab.vue
    │   │   ├── CityTab.vue
    │   │   ├── IndustryTab.vue
    │   │   ├── ExperienceTab.vue
    │   │   └── Chart3DTab.vue
    │   ├── charts/       # 可视化图表组件（D3.js）
    │   │   ├── BarChart.vue
    │   │   ├── LineChart.vue (待实现)
    │   │   └── ScatterChart.vue (待实现)
    │   ├── Dashboard.vue # 仪表盘（组合多个图表）
    │   └── Header.vue    # 页面头部组件
    │
    ├── composables/      # 组合式函数（Vue 3）
    │   └── useResizeObserver.js  # 自适应大小监听
    │
    ├── utils/            # 通用工具函数
    │   ├── colorScale.js # D3颜色比例
    │   ├── format.js     # 数据格式化函数
    │   └── fetchData.js  # 数据获取封装
    │
    ├── api/              # 后端接口模块
    │   ├── apiClient.js  # Axios基础实例
    │   ├── cityApi.js    # 城市分析API
    │   ├── industryApi.js # 行业分析API
    │   ├── experienceApi.js # 经验分析API
    │   ├── overviewApi.js # 总览API
    │   └── salary3dApi.js # 三维薪资API
    │
    └── config/           # 项目配置
        └── appConfig.js  # 全局配置（API地址、主题色等）
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录

### 预览生产版本

```bash
npm run preview
```

## 技术栈

- **Vue 3**: 使用组合式API (Composition API)
- **Vite**: 快速的前端构建工具
- **D3.js**: 数据可视化库
- **ECharts & ECharts GL**: 用于3D图表可视化
- **Axios**: HTTP客户端
- **ES6+**: 现代JavaScript语法

## 开发说明

### 添加新的图表组件

1. 在 `src/components/charts/` 目录下创建新的Vue组件
2. 使用D3.js进行数据可视化
3. 参考 `BarChart.vue` 的实现方式

### 添加新的API接口

1. 在 `src/api/` 目录下创建或修改API文件
2. 使用 `apiClient` 进行HTTP请求
3. 在组件中使用 `useFetchData` 组合式函数

### 样式规范

- 全局样式放在 `src/assets/styles/base.css`
- 图表样式放在 `src/assets/styles/chart.css`
- 组件样式使用 `<style scoped>` 进行作用域隔离

## 注意事项

- 确保后端API服务已启动（默认端口5000）
- 前端开发服务器默认端口为3000
- 使用 `@` 别名引用 `src` 目录下的文件

