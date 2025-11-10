<template>
  <div class="scatter-bubble-chart">
    <!-- 控制面板 -->
    <div class="controls">
      <div class="control-item">
        <label for="city-select">选择城市：</label>
        <select id="city-select" v-model="selectedCity" @change="loadScatterData" class="city-select">
          <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      
      <div class="control-item">
        <label>颜色编码：</label>
        <div class="color-mode-buttons">
          <button 
            :class="['mode-btn', { active: colorMode === 'job_level' }]"
            @click="colorMode = 'job_level'"
          >
            职位层级
          </button>
          <button 
            :class="['mode-btn', { active: colorMode === 'industry' }]"
            @click="colorMode = 'industry'"
          >
            行业类别
          </button>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend">
      <div class="legend-title">{{ colorMode === 'job_level' ? '职位层级' : '行业类别' }}</div>
      <div class="legend-items">
        <div 
          v-for="item in legendItems" 
          :key="item.name"
          class="legend-item"
          @click="toggleCategory(item.name)"
          :class="{ inactive: hiddenCategories.has(item.name) }"
        >
          <span class="legend-color" :style="{ backgroundColor: item.color }"></span>
          <span class="legend-label">{{ item.name }}</span>
        </div>
      </div>
    </div>

    <!-- ECharts容器 -->
    <div ref="chartContainer" class="chart-container"></div>

    <!-- 选中节点信息 -->
    <div v-if="selectedNodes.length > 0" class="selected-info">
      <div class="selected-header">
        <span>已选择 {{ selectedNodes.length }} 个职位</span>
        <button @click="clearSelection" class="clear-btn">清除选择</button>
      </div>
      <div class="selected-list">
        <div v-for="(node, index) in selectedNodes" :key="`${node.job_title}-${node.salary}-${node.experience}-${index}`" class="selected-node">
          <span class="node-title">{{ node.job_title }}</span>
          <span class="node-info">{{ node.salary }} | {{ node.experience }} | {{ node.company_type }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getRepresentativeCities, getScatterData, getJobLevels, getIndustries } from '@/api/q1Api'

// 响应式数据
const cities = ref([])
const selectedCity = ref('')
const scatterData = ref(null)
const colorMode = ref('job_level') // 'job_level' 或 'industry'
const jobLevels = ref([])
const industries = ref([])
const hiddenCategories = ref(new Set())
const selectedNodes = ref([])
const chartContainer = ref(null)
let chartInstance = null

// 定义配色方案
const jobLevelColors = {
  '基薪普及': '#5470c6',
  '平薪新人': '#91cc75',
  '优薪技能': '#fac858',
  '高薪管理': '#ee6666'
}

// 生成行业配色（使用渐变色）
const generateIndustryColors = (industries) => {
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5da8a1',
    '#c4ccd3', '#759aa0', '#e69d87', '#8dc1a9', '#d48265'
  ]
  const colorMap = {}
  industries.forEach((industry, index) => {
    colorMap[industry] = colors[index % colors.length]
  })
  return colorMap
}

const industryColors = ref({})

// 计算图例项
const legendItems = computed(() => {
  if (colorMode.value === 'job_level') {
    return Object.entries(jobLevelColors).map(([name, color]) => ({
      name,
      color
    }))
  } else {
    return Object.entries(industryColors.value).map(([name, color]) => ({
      name,
      color
    }))
  }
})

// 切换类别显示/隐藏
const toggleCategory = (category) => {
  if (hiddenCategories.value.has(category)) {
    hiddenCategories.value.delete(category)
  } else {
    hiddenCategories.value.add(category)
  }
  updateChart()
}

// 清除选择
const clearSelection = () => {
  selectedNodes.value = []
  if (chartInstance) {
    chartInstance.dispatchAction({
      type: 'unselect'
    })
  }
}

// 加载初始数据
const loadInitialData = async () => {
  try {
    // 加载城市列表
    const citiesResponse = await getRepresentativeCities()
    cities.value = citiesResponse.cities
    
    // 加载职位层级
    const jobLevelsResponse = await getJobLevels()
    jobLevels.value = jobLevelsResponse.job_levels
    
    // 选择第一个城市
    if (cities.value.length > 0) {
      selectedCity.value = cities.value[0]
      await loadScatterData()
    }
  } catch (error) {
    console.error('加载初始数据失败:', error)
  }
}

// 加载散点图数据
const loadScatterData = async () => {
  if (!selectedCity.value) return
  
  try {
    // 加载散点图数据
    const response = await getScatterData(selectedCity.value)
    scatterData.value = response
    
    // 加载该城市的行业列表
    const industriesResponse = await getIndustries(selectedCity.value)
    industries.value = industriesResponse.industries
    industryColors.value = generateIndustryColors(industries.value)
    
    // 更新图表
    await nextTick()
    updateChart()
  } catch (error) {
    console.error('加载散点图数据失败:', error)
  }
}

// 准备图表数据
const prepareChartData = () => {
  if (!scatterData.value || !scatterData.value.data) return []
  
  const data = scatterData.value.data
  const category = colorMode.value === 'job_level' ? 'job_level' : 'company_type'
  const colors = colorMode.value === 'job_level' ? jobLevelColors : industryColors.value
  
  // 按类别分组
  const groupedData = {}
  
  data.forEach(point => {
    const categoryValue = point[category]
    
    // 如果该类别被隐藏，跳过
    if (hiddenCategories.value.has(categoryValue)) return
    
    if (!groupedData[categoryValue]) {
      groupedData[categoryValue] = []
    }
    
    groupedData[categoryValue].push({
      value: [
        point.experience_rank,
        point.salary_value,
        point.normalized_size
      ],
      itemStyle: {
        color: colors[categoryValue] || '#ccc'
      },
      // 存储完整信息用于tooltip
      rawData: point
    })
  })
  
  // 转换为ECharts series格式
  return Object.entries(groupedData).map(([categoryName, points]) => ({
    name: categoryName,
    type: 'scatter',
    symbolSize: (data) => {
      // 使用归一化后的气泡大小
      return data[2]
    },
    data: points,
    emphasis: {
      focus: 'self',
      itemStyle: {
        borderColor: '#333',
        borderWidth: 2
      }
    }
  }))
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || !scatterData.value) return
  
  const series = prepareChartData()
  
  const option = {
    title: {
      text: `${selectedCity.value} - 职位分布散点图`,
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const data = params.data.rawData
        return `
          <div style="padding: 8px;">
            <strong>${data.job_title}</strong><br/>
            <span style="color: #666;">薪资：</span>${data.salary}<br/>
            <span style="color: #666;">经验：</span>${data.experience}<br/>
            <span style="color: #666;">招聘人数：</span>${data.recruit_count}<br/>
            <span style="color: #666;">职位层级：</span>${data.job_level}<br/>
            <span style="color: #666;">行业：</span>${data.company_type}
          </div>
        `
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      name: '经验层级 (1-10)',
      nameLocation: 'middle',
      nameGap: 30,
      type: 'value',
      min: 0,
      max: 11,
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      }
    },
    yAxis: {
      name: '薪资（K）',
      nameLocation: 'middle',
      nameGap: 50,
      type: 'value',
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#e0e0e0'
        }
      }
    },
    series: series
  }
  
  chartInstance.setOption(option, true)
}

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return
  
  chartInstance = echarts.init(chartContainer.value)
  
  // 监听点击事件实现多选
  chartInstance.on('click', (params) => {
    const data = params.data.rawData
    
    // 使用多个字段组合来唯一标识一个职位
    const isSameJob = (a, b) => {
      return a.job_title === b.job_title && 
             a.salary === b.salary && 
             a.experience === b.experience &&
             a.company_type === b.company_type
    }
    
    // 检查是否已经选中
    const index = selectedNodes.value.findIndex(n => isSameJob(n, data))
    
    if (index >= 0) {
      // 取消选中
      selectedNodes.value.splice(index, 1)
      console.log('ScatterChart: 取消选中职位', index, '剩余:', selectedNodes.value.length)
    } else {
      // 添加到选中列表
      selectedNodes.value.push(data)
      console.log('ScatterChart: 选中职位，总数:', selectedNodes.value.length)
    }
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听颜色模式变化
watch(colorMode, () => {
  updateChart()
})

// 组件挂载时初始化
onMounted(async () => {
  await loadInitialData()
  initChart()
})

// 组件卸载时清理
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})

// 暴露选中的节点数据（供父组件使用）
defineExpose({
  selectedNodes
})
</script>

<style scoped>
.scatter-bubble-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.controls {
  display: flex;
  gap: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-item label {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.city-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  min-width: 150px;
}

.city-select:hover {
  border-color: #5470c6;
}

.color-mode-buttons {
  display: flex;
  gap: 8px;
}

.mode-btn {
  padding: 6px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.mode-btn:hover {
  border-color: #5470c6;
  color: #5470c6;
}

.mode-btn.active {
  background: #5470c6;
  color: white;
  border-color: #5470c6;
}

.legend {
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 15px;
}

.legend-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.legend-item:hover {
  background: #e9ecef;
}

.legend-item.inactive {
  opacity: 0.3;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-block;
}

.legend-label {
  font-size: 13px;
  color: #555;
}

.chart-container {
  flex: 1;
  min-height: 400px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
}

.selected-info {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 280px;
  max-height: 400px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 10;
}

.selected-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #5470c6;
  color: white;
  font-weight: 500;
}

.clear-btn {
  padding: 4px 12px;
  background: white;
  color: #5470c6;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.clear-btn:hover {
  background: #f0f0f0;
}

.selected-list {
  max-height: 340px;
  overflow-y: auto;
  padding: 10px;
}

.selected-node {
  padding: 10px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #5470c6;
}

.node-title {
  display: block;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.node-info {
  display: block;
  font-size: 12px;
  color: #666;
}
</style>

