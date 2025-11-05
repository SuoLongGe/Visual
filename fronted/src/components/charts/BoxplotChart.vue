<template>
  <div class="boxplot-chart">
    <div v-if="!filters.experience || !filters.education" class="info-tip">
      <p>💡 请在上方的3D图表中点击柱体，选择工作经验和学历要求</p>
    </div>
    
    <div class="filter-section">
      <div class="filter-group">
        <label>工作经验：</label>
        <div class="selected-value" :class="{ 'selected': filters.experience, 'not-selected': !filters.experience }">
          {{ filters.experience || '未选择 - 点击3D图表柱体' }}
        </div>
      </div>
      
      <div class="filter-group">
        <label>学历要求：</label>
        <div class="selected-value" :class="{ 'selected': filters.education, 'not-selected': !filters.education }">
          {{ filters.education || '未选择 - 点击3D图表柱体' }}
        </div>
      </div>
      
      <div class="filter-group">
        <label>城市筛选：</label>
        <select v-model="filters.city" class="filter-select">
          <option value="">全部</option>
          <option v-for="city in availableCities" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>公司类型：</label>
        <select v-model="filters.company_type" class="filter-select">
          <option value="">全部</option>
          <option v-for="type in availableCompanyTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>视图类型：</label>
        <select v-model="viewType" class="filter-select">
          <option value="city">按城市分布</option>
          <option value="company_type">按公司类型分布</option>
        </select>
      </div>
      
      <button class="btn" @click="handleLoad" :disabled="loading || !filters.experience || !filters.education">
        {{ loading ? '加载中...' : '重新加载箱线图' }}
      </button>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div v-if="hasData" ref="chartContainer" id="boxplot-container" class="chart-container"></div>
    
    <div v-if="stats && !loading" class="summary-info" style="margin-top: 20px;">
      <h3>统计信息</h3>
      <p>数据点数量: {{ stats.total_count }}</p>
      <p>平均薪资: {{ stats.avg_salary }}K</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getBoxplotData } from '@/api/salary3dApi.js'

const props = defineProps({
  experience: {
    type: String,
    default: ''
  },
  education: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:experience', 'update:education'])

const filters = ref({
  experience: '',
  education: '',
  city: '',
  company_type: ''
})

const viewType = ref('city')
const chartContainer = ref(null)
const hasData = ref(false)
const loading = ref(false)
const error = ref(null)
const stats = ref(null)
const availableCities = ref([])
const availableCompanyTypes = ref([])
let boxplotChart = null
let resizeHandler = null

// 监听props变化，更新filters并自动加载
watch(() => props.experience, (val) => {
  if (val) {
    filters.value.experience = val
    // 如果两个参数都有了，自动加载
    if (filters.value.experience && filters.value.education) {
      handleLoad()
    }
  }
}, { immediate: true })

watch(() => props.education, (val) => {
  if (val) {
    filters.value.education = val
    // 如果两个参数都有了，自动加载
    if (filters.value.experience && filters.value.education) {
      handleLoad()
    }
  }
}, { immediate: true })

// 监听视图类型变化
watch(viewType, () => {
  if (hasData.value && filters.value.experience && filters.value.education) {
    handleLoad()
  }
})

const handleLoad = async () => {
  try {
    // 验证必填参数
    if (!filters.value.experience || !filters.value.education) {
      error.value = '请先点击3D图表中的柱体选择工作经验和学历要求'
      return
    }
    
    loading.value = true
    error.value = null
    
    const response = await getBoxplotData(filters.value)
    
    if (response.code !== 200) {
      error.value = response.message || '获取数据失败'
      return
    }
    
    // 更新可用的城市和公司类型
    availableCities.value = response.data.cities || []
    availableCompanyTypes.value = response.data.company_types || []
    
    // 设置数据标记，让容器显示
    hasData.value = true
    
    // 等待 DOM 更新
    await nextTick()
    
    // 再次等待确保容器已渲染
    setTimeout(() => {
      renderBoxplot(response.data)
      calculateStats(response.data)
    }, 100)
  } catch (err) {
    console.error('加载箱线图失败:', err)
    error.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
}

const renderBoxplot = (data) => {
  const container = chartContainer.value || document.getElementById('boxplot-container')
  if (!container) {
    console.error('箱线图容器不存在')
    return
  }
  
  if (boxplotChart) {
    boxplotChart.dispose()
  }
  
  boxplotChart = echarts.init(container)
  
  // 根据视图类型选择数据
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    boxplotChart.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center'
      }
    })
    return
  }
  
  // 准备箱线图数据
  // ECharts箱线图数据格式：[min, Q1, median, Q3, max]
  const boxplotData = dataSource.map(item => {
    const stats = item.stats
    return [stats.min, stats.q1, stats.median, stats.q3, stats.max]
  })
  const categories = dataSource.map(item => item.name)
  
  const option = {
    title: {
      text: viewType.value === 'city' ? '不同城市薪资分布箱线图' : '不同公司类型薪资分布箱线图',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const index = params.dataIndex
        const item = dataSource[index]
        if (!item || !item.stats) return ''
        
        const stats = item.stats
        return `
          <div style="padding: 10px;">
            <strong>${item.name}</strong><br/>
            最小值: ${stats.min}K<br/>
            下四分位数(Q1): ${stats.q1}K<br/>
            中位数: ${stats.median}K<br/>
            上四分位数(Q3): ${stats.q3}K<br/>
            最大值: ${stats.max}K<br/>
            样本数: ${stats.count}
          </div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%'
    },
    xAxis: {
      type: 'category',
      data: categories,
      name: viewType.value === 'city' ? '城市' : '公司类型',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      },
      axisLabel: {
        rotate: -45,
        interval: 0,
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: '薪资(K)',
      nameTextStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      },
      axisLabel: {
        formatter: '{value}K'
      }
    },
    series: [
      {
        name: '薪资分布',
        type: 'boxplot',
        data: boxplotData,
        itemStyle: {
          color: '#5470c6',
          borderColor: '#333'
        },
        emphasis: {
          itemStyle: {
            borderColor: '#900'
          }
        }
      },
      // 添加散点图显示中位数
      {
        name: '中位数',
        type: 'scatter',
        data: dataSource.map((item, index) => [index, item.stats.median]),
        symbolSize: 8,
        itemStyle: {
          color: '#ff6b6b'
        },
        label: {
          show: true,
          formatter: function(params) {
            return params.value[1].toFixed(1)
          },
          position: 'top',
          fontSize: 10
        }
      }
    ]
  }
  
  boxplotChart.setOption(option)
  
  // 窗口大小改变时重新调整图表
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  
  resizeHandler = () => {
    if (boxplotChart) {
      boxplotChart.resize()
    }
  }
  
  window.addEventListener('resize', resizeHandler)
}

const calculateStats = (data) => {
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    stats.value = null
    return
  }
  
  let totalCount = 0
  let totalSalary = 0
  
  dataSource.forEach(item => {
    if (item.stats) {
      totalCount += item.stats.count
      totalSalary += item.stats.median * item.stats.count
    }
  })
  
  stats.value = {
    total_count: totalCount,
    avg_salary: totalCount > 0 ? (totalSalary / totalCount).toFixed(2) : '0'
  }
}

onUnmounted(() => {
  if (boxplotChart) {
    boxplotChart.dispose()
    boxplotChart = null
  }
  
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 600px;
  margin-top: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  position: relative;
}

.filter-section {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  min-width: 150px;
  cursor: pointer;
}

.filter-select:hover {
  border-color: #5470c6;
}

.filter-select:focus {
  outline: none;
  border-color: #5470c6;
  box-shadow: 0 0 0 2px rgba(84, 112, 198, 0.2);
}

.selected-value {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
  font-weight: 500;
}

.selected-value.selected {
  border: 1px solid #5470c6;
  background: #e3f2fd;
  color: #1976d2;
}

.selected-value.not-selected {
  border: 1px solid #ddd;
  background: #f5f5f5;
  color: #999;
  font-style: italic;
}

.info-tip {
  padding: 15px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  margin-bottom: 20px;
  color: #856404;
}

.info-tip p {
  margin: 0;
  font-size: 14px;
}

.btn {
  padding: 10px 20px;
  background: #5470c6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn:hover:not(:disabled) {
  background: #4558a3;
}

.btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.summary-info {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.summary-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
}

.summary-info p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #5470c6;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result.error {
  background: #fee;
  border: 1px solid #fcc;
  color: #c33;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}

.result.error pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>

