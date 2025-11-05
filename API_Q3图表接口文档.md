# Q3图表API接口文档

## 文档概述

本文档详细说明了Q3图表功能（三维柱状图和箱线图）的后端API接口。这两个接口用于展示招聘数据中工作经验、学历、薪资等维度的统计分析。

**版本**: v1.0  
**最后更新**: 2025-01-XX  
**基础URL**: `http://localhost:5000/api`

---

## 目录

1. [接口1：三维柱状图数据接口](#接口1三维柱状图数据接口)
2. [接口2：箱线图数据接口](#接口2箱线图数据接口)
3. [响应格式说明](#响应格式说明)
4. [错误码说明](#错误码说明)
5. [使用示例](#使用示例)

---

## 接口1：三维柱状图数据接口

### 接口信息

- **接口路径**: `/charts/3d/experience-education-salary`
- **请求方法**: `GET`
- **接口描述**: 获取经验-学历-薪资组合的三维柱状图数据，用于展示不同工作经验与学历组合下的平均薪资分布

### 请求参数

本接口无需任何请求参数。

### 请求示例

```bash
# cURL
curl -X GET "http://localhost:5000/api/charts/3d/experience-education-salary"

# JavaScript (fetch)
fetch('http://localhost:5000/api/charts/3d/experience-education-salary')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error))

# Python (requests)
import requests
response = requests.get('http://localhost:5000/api/charts/3d/experience-education-salary')
data = response.json()
```

### 响应数据格式

#### 成功响应 (HTTP 200)

```json
{
  "status": "success",
  "code": 200,
  "message": "获取三维柱状图数据成功",
  "timestamp": "2025-01-XXT10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "experiences": [
      "1-3年",
      "3-5年",
      "5-10年",
      "10年以上",
      "不限",
      "应届生"
    ],
    "educations": [
      "本科",
      "大专",
      "硕士",
      "博士",
      "高中",
      "中专",
      "不限",
      "初中",
      "其他"
    ],
    "data_3d": [
      [0, 0, 15.5],
      [0, 1, 12.3],
      [0, 2, 18.7],
      ...
    ],
    "data_detail": [
      {
        "experience": "1-3年",
        "education": "本科",
        "avg_salary": 15.5,
        "job_count": 1250
      },
      {
        "experience": "1-3年",
        "education": "大专",
        "avg_salary": 12.3,
        "job_count": 890
      },
      ...
    ]
  }
}
```

#### 响应字段说明

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `status` | string | 响应状态，固定为 "success" |
| `code` | integer | HTTP状态码，成功时为200 |
| `message` | string | 响应消息 |
| `timestamp` | string | 响应时间戳（ISO 8601格式） |
| `request_id` | string | 请求唯一标识符（UUID） |
| `data` | object | 响应数据对象 |
| `data.experiences` | array[string] | 所有唯一的经验要求值列表（已排序） |
| `data.educations` | array[string] | 所有唯一的学历要求值列表（已排序） |
| `data.data_3d` | array[array] | 三维数据数组，格式为 `[x索引, y索引, z值]` |
| `data.data_3d[][0]` | integer | 经验在experiences数组中的索引（从0开始） |
| `data.data_3d[][1]` | integer | 学历在educations数组中的索引（从0开始） |
| `data.data_3d[][2]` | float | 该组合对应的平均薪资（单位：K，即千元） |
| `data.data_detail` | array[object] | 详细数据列表，包含每个组合的具体信息 |
| `data.data_detail[].experience` | string | 工作经验要求 |
| `data.data_detail[].education` | string | 学历要求 |
| `data.data_detail[].avg_salary` | float | 平均薪资（单位：K） |
| `data.data_detail[].job_count` | integer | 该组合下的职位数量 |

#### 数据说明

1. **experiences 数组**：包含数据库中所有唯一的经验要求值，按字母顺序排序
2. **educations 数组**：包含数据库中所有唯一的学历要求值，按字母顺序排序
3. **data_3d 数组**：
   - 每个元素是一个三元数组 `[x, y, z]`
   - `x` 是经验在 `experiences` 数组中的索引（从0开始）
   - `y` 是学历在 `educations` 数组中的索引（从0开始）
   - `z` 是该经验-学历组合的平均薪资（单位：K）
   - 如果某个组合没有数据，薪资值会被设置为0
4. **data_detail 数组**：包含所有有数据的经验-学历组合的详细信息

#### 错误响应

```json
{
  "status": "error",
  "code": 500,
  "message": "服务器内部错误",
  "timestamp": "2025-01-XXT10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {
    "type": "INTERNAL_ERROR",
    "details": "具体错误信息"
  }
}
```

---

## 接口2：箱线图数据接口

### 接口信息

- **接口路径**: `/charts/boxplot/salary-distribution`
- **请求方法**: `GET`
- **接口描述**: 获取箱线图统计数据，用于展示在特定经验-学历组合条件下，不同城市或公司类型的薪资分布情况

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `experience` | string | 是 | 工作经验要求 | "1-3年" |
| `education` | string | 是 | 学历要求 | "本科" |
| `city` | string | 否 | 城市筛选（可选） | "北京" |
| `company_type` | string | 否 | 公司类型筛选（可选） | "上市公司" |

### 请求示例

```bash
# cURL - 基础请求（仅经验和学历）
curl -X GET "http://localhost:5000/api/charts/boxplot/salary-distribution?experience=1-3年&education=本科"

# cURL - 带城市筛选
curl -X GET "http://localhost:5000/api/charts/boxplot/salary-distribution?experience=1-3年&education=本科&city=北京"

# cURL - 带公司类型筛选
curl -X GET "http://localhost:5000/api/charts/boxplot/salary-distribution?experience=1-3年&education=本科&company_type=上市公司"

# JavaScript (fetch)
const params = new URLSearchParams({
  experience: '1-3年',
  education: '本科',
  city: '北京'  // 可选
})

fetch(`http://localhost:5000/api/charts/boxplot/salary-distribution?${params}`)
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error))

# Python (requests)
import requests

params = {
    'experience': '1-3年',
    'education': '本科',
    'city': '北京'  # 可选
}

response = requests.get(
    'http://localhost:5000/api/charts/boxplot/salary-distribution',
    params=params
)
data = response.json()
```

### 响应数据格式

#### 成功响应 (HTTP 200)

```json
{
  "status": "success",
  "code": 200,
  "message": "获取箱线图数据成功",
  "timestamp": "2025-01-XXT10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "city_data": [
      {
        "name": "北京",
        "stats": {
          "min": 8.5,
          "q1": 12.3,
          "median": 15.7,
          "q3": 19.2,
          "max": 25.8,
          "count": 450
        },
        "count": 450
      },
      {
        "name": "上海",
        "stats": {
          "min": 9.2,
          "q1": 13.1,
          "median": 16.5,
          "q3": 20.1,
          "max": 26.3,
          "count": 380
        },
        "count": 380
      },
      ...
    ],
    "company_type_data": [
      {
        "name": "上市公司",
        "stats": {
          "min": 10.5,
          "q1": 14.2,
          "median": 17.8,
          "q3": 21.5,
          "max": 28.5,
          "count": 320
        },
        "count": 320
      },
      {
        "name": "民营公司",
        "stats": {
          "min": 8.0,
          "q1": 11.5,
          "median": 14.5,
          "q3": 17.8,
          "max": 23.2,
          "count": 580
        },
        "count": 580
      },
      ...
    ],
    "cities": [
      "北京",
      "上海",
      "深圳",
      "广州",
      ...
    ],
    "company_types": [
      "上市公司",
      "民营公司",
      "外资公司",
      ...
    ]
  }
}
```

#### 响应字段说明

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `status` | string | 响应状态，固定为 "success" |
| `code` | integer | HTTP状态码，成功时为200 |
| `message` | string | 响应消息 |
| `timestamp` | string | 响应时间戳（ISO 8601格式） |
| `request_id` | string | 请求唯一标识符（UUID） |
| `data` | object | 响应数据对象 |
| `data.city_data` | array[object] | 按城市分组的箱线图统计数据 |
| `data.city_data[].name` | string | 城市名称 |
| `data.city_data[].stats` | object | 统计量对象 |
| `data.city_data[].stats.min` | float | 最小值（单位：K） |
| `data.city_data[].stats.q1` | float | 下四分位数（Q1，单位：K） |
| `data.city_data[].stats.median` | float | 中位数（单位：K） |
| `data.city_data[].stats.q3` | float | 上四分位数（Q3，单位：K） |
| `data.city_data[].stats.max` | float | 最大值（单位：K） |
| `data.city_data[].stats.count` | integer | 该城市的样本数量 |
| `data.city_data[].count` | integer | 该城市的样本数量（与stats.count相同） |
| `data.company_type_data` | array[object] | 按公司类型分组的箱线图统计数据 |
| `data.company_type_data[]` | object | 结构同city_data，但name为公司类型 |
| `data.cities` | array[string] | 所有可用的城市列表（已排序） |
| `data.company_types` | array[string] | 所有可用的公司类型列表（已排序） |

#### 统计量计算方法

箱线图的统计量使用标准的分位数计算方法：

1. **最小值 (min)**: 数据集中最小的薪资值
2. **下四分位数 (Q1)**: 25%分位数，使用 `(n+1) * 0.25` 位置计算，支持线性插值
3. **中位数 (median)**: 50%分位数，数据集的中间值
4. **上四分位数 (Q3)**: 75%分位数，使用 `(n+1) * 0.75` 位置计算，支持线性插值
5. **最大值 (max)**: 数据集中最大的薪资值

**注意**: 如果Python版本 >= 3.8，系统会优先使用 `statistics.quantiles()` 方法进行更精确的计算。

#### 错误响应

##### 参数错误 (HTTP 400)

```json
{
  "status": "error",
  "code": 400,
  "message": "参数错误",
  "timestamp": "2025-01-XXT10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {
    "message": "必须指定experience（工作经验）和education（学历）参数"
  }
}
```

##### 服务器错误 (HTTP 500)

```json
{
  "status": "error",
  "code": 500,
  "message": "服务器内部错误",
  "timestamp": "2025-01-XXT10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": {
    "type": "INTERNAL_ERROR",
    "details": "具体错误信息"
  }
}
```

---

## 响应格式说明

### 通用响应结构

所有接口都遵循统一的响应格式：

```json
{
  "status": "success" | "error",
  "code": 200 | 400 | 404 | 500,
  "message": "响应消息",
  "timestamp": "ISO 8601格式的时间戳",
  "request_id": "UUID格式的请求ID",
  "data": { ... },  // 成功时包含
  "error": { ... }  // 错误时包含
}
```

### 时间戳格式

时间戳使用ISO 8601格式：`YYYY-MM-DDTHH:MM:SS`

示例：`2025-01-15T10:30:00`

### 请求ID

每个请求都会生成一个唯一的UUID作为请求ID，用于日志追踪和问题排查。

---

## 错误码说明

| HTTP状态码 | 说明 | 可能原因 |
|-----------|------|---------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求参数错误 | 缺少必填参数或参数格式错误 |
| 404 | 资源不存在 | 请求的接口路径不存在 |
| 500 | 服务器内部错误 | 数据库连接失败、SQL执行错误等 |

---

## 使用示例

### 示例1：获取三维柱状图数据

```javascript
// JavaScript示例
async function load3DChart() {
  try {
    const response = await fetch('http://localhost:5000/api/charts/3d/experience-education-salary')
    const result = await response.json()
    
    if (result.code === 200) {
      const { experiences, educations, data_3d } = result.data
      
      console.log(`经验类型: ${experiences.length} 种`)
      console.log(`学历类型: ${educations.length} 种`)
      console.log(`数据点: ${data_3d.length} 个`)
      
      // 使用ECharts渲染3D图表
      // ...
    }
  } catch (error) {
    console.error('加载失败:', error)
  }
}
```

### 示例2：获取箱线图数据（基础）

```javascript
// JavaScript示例
async function loadBoxplot(experience, education) {
  const params = new URLSearchParams({
    experience: experience,
    education: education
  })
  
  try {
    const response = await fetch(
      `http://localhost:5000/api/charts/boxplot/salary-distribution?${params}`
    )
    const result = await response.json()
    
    if (result.code === 200) {
      const { city_data, company_type_data } = result.data
      
      // 按城市展示箱线图
      console.log('城市数据:', city_data)
      
      // 按公司类型展示箱线图
      console.log('公司类型数据:', company_type_data)
    }
  } catch (error) {
    console.error('加载失败:', error)
  }
}

// 调用示例
loadBoxplot('1-3年', '本科')
```

### 示例3：获取箱线图数据（带筛选）

```python
# Python示例
import requests

def get_boxplot_with_filters(experience, education, city=None, company_type=None):
    """
    获取箱线图数据，支持城市和公司类型筛选
    """
    url = 'http://localhost:5000/api/charts/boxplot/salary-distribution'
    params = {
        'experience': experience,
        'education': education
    }
    
    if city:
        params['city'] = city
    if company_type:
        params['company_type'] = company_type
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data['code'] == 200:
            return data['data']
        else:
            print(f"错误: {data['message']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

# 使用示例
# 1. 基础查询
result = get_boxplot_with_filters('1-3年', '本科')

# 2. 带城市筛选
result = get_boxplot_with_filters('1-3年', '本科', city='北京')

# 3. 带公司类型筛选
result = get_boxplot_with_filters('1-3年', '本科', company_type='上市公司')

# 4. 同时筛选城市和公司类型
result = get_boxplot_with_filters('1-3年', '本科', city='北京', company_type='上市公司')
```

### 示例4：前端完整集成示例

```javascript
// Vue 3 Composition API示例
import { ref } from 'vue'
import { get3DSalaryData, getBoxplotData } from '@/api/salary3dApi.js'

export function useQ3Charts() {
  const chart3DData = ref(null)
  const boxplotData = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 加载3D图表数据
  const load3DChart = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await get3DSalaryData()
      if (response.code === 200) {
        chart3DData.value = response.data
      } else {
        error.value = response.message
      }
    } catch (err) {
      error.value = err.message || '加载失败'
    } finally {
      loading.value = false
    }
  }
  
  // 加载箱线图数据
  const loadBoxplot = async (experience, education, city = null, companyType = null) => {
    loading.value = true
    error.value = null
    
    try {
      const filters = { experience, education }
      if (city) filters.city = city
      if (companyType) filters.company_type = companyType
      
      const response = await getBoxplotData(filters)
      if (response.code === 200) {
        boxplotData.value = response.data
      } else {
        error.value = response.message
      }
    } catch (err) {
      error.value = err.message || '加载失败'
    } finally {
      loading.value = false
    }
  }
  
  return {
    chart3DData,
    boxplotData,
    loading,
    error,
    load3DChart,
    loadBoxplot
  }
}
```

---

## 数据说明

### 数据来源

两个接口的数据都来自数据库表 `data`，该表包含以下字段：
- `experience`: 工作经验要求
- `education`: 学历要求
- `salary`: 薪资范围（格式：`起始值-结束值`，单位：K）
- `city`: 城市
- `company_type`: 公司类型

### 数据过滤规则

1. **三维柱状图接口**：
   - 只统计 `experience`、`education`、`salary` 都不为空的记录
   - 只统计 `salary` 格式为 `数字-数字` 的记录（使用正则：`^[0-9]+-[0-9]+`）
   - 薪资计算：取起始值和结束值的平均值 `(起始值 + 结束值) / 2`

2. **箱线图接口**：
   - 必须指定 `experience` 和 `education` 参数
   - `city` 和 `company_type` 为可选筛选条件
   - 同样只统计有效薪资格式的记录
   - 按城市和公司类型分别分组计算统计量

### 数据精度

- 薪资值保留2位小数
- 统计量（min, q1, median, q3, max）保留2位小数

---

## 注意事项

1. **参数编码**：URL参数需要进行URL编码，特别是包含中文的参数
2. **数据量**：如果筛选条件过于严格，可能返回空数据数组
3. **性能**：箱线图接口涉及大量数据计算，建议合理使用筛选条件
4. **并发**：接口支持并发请求，但建议控制请求频率
5. **错误处理**：始终检查响应中的 `code` 字段，确保请求成功

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-01-XX | 初始版本，包含三维柱状图和箱线图接口 |

---

## 技术支持

如有问题或建议，请联系开发团队或查看项目文档。

---

**文档结束**

