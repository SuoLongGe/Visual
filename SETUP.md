# 项目设置指南

## 前置要求

- Node.js >= 16.0.0
- npm >= 7.0.0 或 yarn >= 1.22.0
- Python >= 3.8
- pip

## 安装步骤

### 1. 安装前端依赖

```bash
cd fronted
npm install
```

或者使用 yarn:

```bash
cd fronted
yarn install
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 启动项目

#### 方式一：分别启动（推荐开发时使用）

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
后端将在 `http://localhost:5001` 启动

#### 方式二：使用启动脚本（推荐生产环境）

```bash
python start_platform.py
```

这会同时启动后端服务，并在浏览器中打开前端页面。

## 项目结构说明

### 前端项目结构

```
frontend/
├── package.json          # 项目依赖配置
├── vite.config.js        # Vite构建配置
├── index.html            # 入口HTML
├── public/               # 静态资源（不参与构建）
└── src/                  # 源代码目录
    ├── main.js           # Vue应用入口
    ├── App.vue           # 根组件
    ├── assets/           # 静态资源
    │   └── styles/       # 样式文件
    ├── components/       # Vue组件
    │   ├── tabs/         # 标签页组件
    │   └── charts/       # 图表组件
    ├── composables/      # 组合式函数
    ├── utils/            # 工具函数
    ├── api/              # API接口
    └── config/           # 配置文件
```

### 后端项目结构

```
├── app.py                # Flask应用主文件
├── config.py             # 配置文件
├── database.py           # 数据库配置
├── routes/               # 路由模块
├── services/             # 业务逻辑层
├── models/               # 数据模型
└── utils/                # 工具函数
```

## 开发说明

### 添加新的API接口

1. 在 `src/api/` 目录下创建或修改API文件
2. 使用 `apiClient` 进行HTTP请求
3. 在组件中使用 `useFetchData` 组合式函数

示例：

```javascript
// src/api/exampleApi.js
import apiClient from './apiClient.js'

export async function getExampleData() {
  return await apiClient.get('/example')
}
```

### 添加新的图表组件

1. 在 `src/components/charts/` 目录下创建Vue组件
2. 使用D3.js进行数据可视化
3. 参考 `BarChart.vue` 的实现方式

示例：

```vue
<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as d3 from 'd3'

const chartContainer = ref(null)

onMounted(() => {
  // 使用D3.js绘制图表
})
</script>
```

### 使用组合式函数

项目提供了以下组合式函数：

- `useFetchData`: 数据获取封装
- `useResizeObserver`: 自适应大小监听

示例：

```javascript
import { useFetchData } from '@/utils/fetchData.js'
import { getData } from '@/api/dataApi.js'

const { data, loading, error, execute } = useFetchData(getData)

// 执行请求
execute()
```

## 构建生产版本

### 构建前端

```bash
cd fronted
npm run build
```

构建产物将输出到 `frontend/dist/` 目录

### 预览生产版本

```bash
cd fronted
npm run preview
```

## 常见问题

### 1. 端口冲突

如果3000或5000端口被占用，可以修改：

- 前端端口：修改 `vite.config.js` 中的 `server.port`
- 后端端口：修改 `app.py` 中的 `port` 参数

### 2. CORS错误

确保后端已启用CORS：

```python
from flask_cors import CORS
CORS(app)
```

### 3. 模块导入错误

确保使用正确的路径别名：

```javascript
// 使用 @ 别名
import { useFetchData } from '@/utils/fetchData.js'
```

### 4. D3.js图表不显示

- 确保容器有明确的宽高
- 检查数据格式是否正确
- 查看浏览器控制台错误信息

## 技术栈

- **前端**: Vue 3 + Vite + D3.js + ECharts
- **后端**: Flask + SQLite
- **构建工具**: Vite
- **包管理**: npm/yarn

## 下一步

- [ ] 添加更多D3.js图表组件
- [ ] 实现数据缓存机制
- [ ] 添加单元测试
- [ ] 优化性能
- [ ] 添加PWA支持

