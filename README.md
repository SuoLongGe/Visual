# 职数洞见 - 招聘数据可视化平台

基于 Vue 3 + Vite + D3.js 的数据可视化平台

## 项目结构

```
├── app.py                     # Flask后端应用
├── config.py                  # 后端配置
├── database.py                # 数据库配置
├── routes/                    # 后端路由
├── services/                  # 后端业务逻辑
├── models/                    # 数据模型
├── utils/                     # 后端工具函数
├── requirements.txt           # Python依赖
│
└── frontend/                  # 前端项目目录
    ├── package.json           # 项目依赖与脚本
    ├── vite.config.js         # Vite 构建配置
    ├── index.html             # 入口 HTML
    ├── public/                # 静态资源（不参与构建）
    │   └── vite.svg
    └── src/                   # 源代码目录
        ├── main.js            # Vue 应用入口
        ├── App.vue            # 顶层组件
        │
        ├── assets/            # 静态资源（图片、字体等）
        │   ├── styles/
        │   │   ├── base.css   # 全局基础样式
        │   │   └── chart.css  # 图表通用样式
        │   └── images/
        │
        ├── components/        # Vue 组件目录
        │   ├── tabs/          # 标签页组件
        │   │   ├── OverviewTab.vue
        │   │   ├── CityTab.vue
        │   │   ├── IndustryTab.vue
        │   │   ├── ExperienceTab.vue
        │   │   └── Chart3DTab.vue
        │   ├── charts/        # 可视化图表组件（D3.js）
        │   │   ├── BarChart.vue   # 柱状图
        │   │   ├── LineChart.vue  # 折线图（待实现）
        │   │   └── ScatterChart.vue # 散点图（待实现）
        │   ├── Dashboard.vue  # 仪表盘（组合多个图表）
        │   └── Header.vue     # 页面头部组件
        │
        ├── composables/       # 组合式函数（Vue 3）
        │   └── useResizeObserver.js  # 自适应大小监听
        │
        ├── utils/             # 通用工具函数
        │   ├── colorScale.js  # D3颜色比例
        │   ├── format.js      # 数据格式化函数
        │   └── fetchData.js   # 数据获取封装
        │
        ├── api/               # 后端接口模块
        │   ├── apiClient.js   # Axios基础实例
        │   ├── cityApi.js     # 城市分析API
        │   ├── industryApi.js # 行业分析API
        │   ├── experienceApi.js # 经验分析API
        │   ├── overviewApi.js # 总览API
        │   └── salary3dApi.js # 三维薪资API
        │
        └── config/            # 项目配置
            └── appConfig.js  # 全局配置（API地址、主题色等）
```

## 技术栈

- **Vue 3**: 使用组合式API (Composition API)
- **Vite**: 快速的前端构建工具
- **D3.js**: 数据可视化库
- **ECharts & ECharts GL**: 用于3D图表可视化
- **Axios**: HTTP客户端
- **ES6+**: 现代JavaScript语法

## 快速开始

### 1. 安装依赖

**前端依赖：**
```bash
cd fronted
npm install
```

**后端依赖：**
```bash
pip install -r requirements.txt
```

### 2. 启动开发服务器

**终端1 - 启动前端开发服务器：**
```bash
cd fronted
npm run dev
```
前端将在 `http://localhost:3000` 启动

**终端2 - 启动后端API服务：**
```bash
python app.py
```
后端将在 `http://localhost:5000` 启动

或者使用启动脚本：
```bash
python start_platform.py
```

### 3. 构建生产版本

```bash
cd fronted
npm run build
```

构建产物将输出到 `frontend/dist/` 目录

### 4. 预览生产版本

```bash
cd fronted
npm run preview
```

## 开发说明

### 添加新的图表组件

1. 在 `src/components/charts/` 目录下创建新的Vue组件
2. 使用D3.js进行数据可视化
3. 参考 `src/utils/colorScale.js` 使用颜色工具
4. 在相应的标签页组件中引入使用

### 添加新的API接口

1. 在 `src/api/` 目录下创建或修改API文件
2. 使用 `apiClient` 进行请求
3. 在组件中使用 `useFetchData` 组合式函数

### 样式规范

- 全局样式放在 `src/assets/styles/base.css`
- 图表样式放在 `src/assets/styles/chart.css`
- 组件样式使用 `<style scoped>` 进行作用域隔离

## 项目特性

- ✅ Vue 3 组合式API
- ✅ Vite 快速构建
- ✅ 模块化架构
- ✅ 响应式设计
- ✅ D3.js 数据可视化支持
- ✅ ECharts 3D图表支持
- ✅ Axios API封装
- ✅ 组合式函数复用

## 环境变量

创建 `.env` 文件（可选）：

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

## 浏览器支持

- Chrome (最新版本)
- Firefox (最新版本)
- Safari (最新版本)
- Edge (最新版本)

## 许可证

MIT License
