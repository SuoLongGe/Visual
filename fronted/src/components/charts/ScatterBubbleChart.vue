<template>
  <div class="scatter-bubble-chart">
    <!-- 控制面板 -->
    <div class="controls">
      <div class="control-item" v-if="viewMode === 'city'">
        <label for="city-select">选择城市：</label>
        <select 
          id="city-select" 
          v-model="selectedCity" 
          @change="loadScatterData" 
          class="city-select"
        >
          <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      <div class="control-item" v-else>
        <label>行业模式：</label>
        <span class="mode-hint">已展示全国 160 个行业类别</span>
      </div>
      
      <div class="control-item">
        <label>视图切换：</label>
        <div class="color-mode-buttons">
          <button 
            :class="['mode-btn', { active: colorMode === 'job_level' }]"
            @click="setViewMode('job_level')"
          >
            按城市 · 职位层级
          </button>
          <button 
            :class="['mode-btn', { active: colorMode === 'industry' }]"
            @click="setViewMode('industry')"
          >
            全国 · 行业类别
          </button>
        </div>
      </div>
    </div>

    <!-- 图例 / 提示 -->
    <div class="legend">
      <template v-if="viewMode === 'city'">
        <div class="legend-title">职位层级</div>
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
      </template>
      <template v-else>
        <div class="legend-title">全国行业类别散点</div>
        <p class="industry-legend-hint">
          气泡颜色自动分配，无需手动筛选；横轴为平均经验层级，纵轴为平均薪资。
        </p>
      </template>
    </div>

    <!-- ECharts容器 -->
    <div ref="chartContainer" class="chart-container"></div>

    <!-- 选中节点信息 -->
    <div v-if="selectedNodes.length > 0" class="selected-info">
      <div class="selected-header">
        <span>
          {{ viewMode === 'city' ? '已选择 ' + selectedNodes.length + ' 个职位' : '已选择 ' + selectedNodes.length + ' 个行业' }}
        </span>
        <button @click="clearSelection" class="clear-btn">清除选择</button>
      </div>
      <div class="selected-list">
        <div
          v-for="(node, index) in selectedNodes"
          :key="`${node.job_title}-${node.avg_salary}-${node.avg_experience}-${index}`"
          class="selected-node"
        >
          <template v-if="viewMode === 'city'">
            <span class="node-title">{{ node.job_title }}</span>
            <span class="node-info">
              平均薪资：{{ node.avg_salary?.toFixed(2) }}K |
              平均经验：{{ node.avg_experience?.toFixed(2) }} |
              平均学历：{{ node.avg_education?.toFixed(2) }}
            </span>
          </template>
          <template v-else>
            <span class="node-title">{{ node.company_type }}</span>
            <span class="node-info">
              招聘总数：{{ node.job_count }} |
              平均薪资：{{ node.avg_median_salary?.toFixed(2) }}K |
              平均经验：{{ node.avg_experience_rank?.toFixed(2) }}
            </span>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { 
  getRepresentativeCities, 
  getScatterData, 
  getNationalIndustryScatter
} from '@/api/q1Api'

// 响应式数据
const cities = ref([])
const selectedCity = ref('')
const scatterData = ref(null)
const industryScatterData = ref(null)
const colorMode = ref('job_level') // 'job_level' 或 'industry'
const viewMode = computed(() => colorMode.value === 'job_level' ? 'city' : 'industry')
const hiddenCategories = ref(new Set())
const selectedNodes = ref([])
const chartContainer = ref(null)
let chartInstance = null

// 定义配色方案
const jobLevelColors = {
  '平薪新人': '#5470c6',  // 蓝色
  '基薪普及': '#91cc75',  // 绿色
  '优薪技能': '#fac858',
  '高新管理': '#ee6666'
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
  if (viewMode.value !== 'city') return []
  return Object.entries(jobLevelColors).map(([name, color]) => ({
    name,
    color
  }))
})

// 切换类别显示/隐藏
const toggleCategory = (category) => {
  if (viewMode.value !== 'city') return
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
  if (!selectedCity.value || viewMode.value !== 'city') return
  
  try {
    // 加载散点图数据
    const response = await getScatterData(selectedCity.value)
    scatterData.value = response
    
    // 更新图表
    await nextTick()
    updateChart()
  } catch (error) {
    console.error('加载散点图数据失败:', error)
  }
}

// 加载全国行业散点数据
const loadIndustryScatterData = async () => {
  try {
    const response = await getNationalIndustryScatter()
    industryScatterData.value = response
    const typeList = response?.data?.map(item => item.company_type) || []
    industryColors.value = generateIndustryColors(typeList)
    await nextTick()
    updateChart()
  } catch (error) {
    console.error('加载行业散点数据失败:', error)
  }
}

// 准备图表数据
const prepareChartData = () => {
  if (viewMode.value === 'city') {
    if (!scatterData.value || !scatterData.value.data) return []
    const data = scatterData.value.data
    const groupedData = {}
    data.forEach(point => {
      const categoryValue = point.job_level
      if (hiddenCategories.value.has(categoryValue)) return
      if (!groupedData[categoryValue]) {
        groupedData[categoryValue] = []
      }
      groupedData[categoryValue].push({
        value: [
          point.avg_experience,
          point.avg_salary,
          point.normalized_size
        ],
        itemStyle: {
          color: jobLevelColors[categoryValue] || '#ccc'
        },
        rawData: point
      })
    })
    return Object.entries(groupedData).map(([categoryName, points]) => ({
      name: categoryName,
      type: 'scatter',
      symbolSize: dataPoint => dataPoint[2],
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

  // 行业模式：单个系列，按行业着色
  if (!industryScatterData.value || !industryScatterData.value.data) return []
  const industryPoints = industryScatterData.value.data.map(item => ({
    value: [
      item.avg_experience_rank,
      item.avg_median_salary,
      item.normalized_size
    ],
    name: item.company_type,
    itemStyle: {
      color: industryColors.value[item.company_type] || '#5470c6'
    },
    rawData: item
  }))

  return [
    {
      name: '行业类别',
      type: 'scatter',
      symbolSize: dataPoint => dataPoint[2],
      data: industryPoints,
      emphasis: {
        focus: 'self',
        itemStyle: {
          borderColor: '#333',
          borderWidth: 2
        }
      }
    }
  ]
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || !scatterData.value) return
  
  const series = prepareChartData()
  
  const option = {
    title: {
      text: viewMode.value === 'city' 
        ? `${selectedCity.value} - 职位分布散点图`
        : '全国行业类别散点（160）',
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const data = params.data.rawData

        if (viewMode.value === 'industry') {
          return `
            <div style="padding: 8px; max-width: 320px;">
              <strong>${data.company_type}</strong><br/>
              <span style="color: #666;">招聘总数：</span>${data.job_count}<br/>
              <span style="color: #666;">平均中位薪资：</span>${data.avg_median_salary.toFixed(2)}K<br/>
              <span style="color: #666;">平均经验层级：</span>${data.avg_experience_rank.toFixed(2)}<br/>
              <span style="color: #666;">平均学历层级：</span>${data.avg_education_rank.toFixed(2)}<br/>
              <span style="color: #666;">平均城市等级：</span>${data.avg_city_tier_label || '暂无'}${data.avg_city_tier_score ? `（${data.avg_city_tier_score.toFixed(2)}）` : ''}<br/>
            </div>
          `
        }

        const samples = data.samples || []
        const samplesHtml = samples.length
          ? samples.map((s, idx) => `
              <div style="margin-top:4px;font-size:12px;">
                <span style="color:#999;">样本${idx + 1}：</span>
                薪资：${s.salary}，学历：${s.education}，经验：${s.experience}
              </div>
            `).join('')
          : '<div style="margin-top:4px;font-size:12px;color:#aaa;">无示例数据</div>'

        return `
          <div style="padding: 8px; max-width: 320px;">
            <strong>${data.job_title}</strong><br/>
            <span style="color: #666;">平均薪资：</span>${data.avg_salary.toFixed(2)}K<br/>
            <span style="color: #666;">薪资标准差：</span>${data.salary_std.toFixed(2)}K<br/>
            <span style="color: #666;">平均经验：</span>${data.avg_experience.toFixed(2)}（层级）<br/>
            <span style="color: #666;">平均学历：</span>${data.avg_education.toFixed(2)}（层级）<br/>
            <span style="color: #666;">香农熵：</span>${data.avg_shannon_entropy.toFixed(3)}<br/>
            <span style="color: #666;">招聘人数：</span>${data.job_in_city_cnt}<br/>
            <span style="color: #666;">薪资范围：</span>${data.min_annual_salary.toFixed(2)}K - ${data.max_annual_salary.toFixed(2)}K<br/>
            <span style="color: #666;">职位层级：</span>${data.job_level}<br/>
            <span style="color: #666;">行业示例：</span>${data.company_type}<br/>
            <div style="margin-top:6px;padding-top:4px;border-top:1px solid #eee;font-size:12px;color:#666;">
              <div style="margin-bottom:2px;color:#999;">该城市该职位的示例记录：</div>
              ${samplesHtml}
            </div>
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
      name: viewMode.value === 'city' ? '经验层级 (1-10)' : '平均经验层级',
      nameLocation: 'middle',
      nameGap: 30,
      type: 'value',
      // 城市模式保留原来的 0-10，行业模式聚焦在 4-6 区间，减少空白和拥挤
      min: viewMode.value === 'city' ? 0 : 4,
      max: viewMode.value === 'city' ? 10 : 6,
      splitNumber: viewMode.value === 'city' ? 10 : 8,
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
    const isSameEntity = (a, b) => {
      if (viewMode.value === 'city') {
        return a.job_title === b.job_title &&
               a.avg_salary === b.avg_salary &&
               a.avg_experience === b.avg_experience &&
               a.company_type === b.company_type
      }
      return a.company_type === b.company_type
    }

    const index = selectedNodes.value.findIndex(n => isSameEntity(n, data))

    if (index >= 0) {
      selectedNodes.value.splice(index, 1)
    } else {
      // 行业模式限制最大2个，便于右侧差异对比
      if (viewMode.value === 'industry' && selectedNodes.value.length >= 2) {
        selectedNodes.value.shift()
      }
      selectedNodes.value.push(data)
    }
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)

  updateChart()
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

const setViewMode = (mode) => {
  if (colorMode.value === mode) return
  colorMode.value = mode
}

// 监听模式变化
watch(colorMode, async (mode) => {
  hiddenCategories.value = new Set()
  selectedNodes.value = []

  if (mode === 'job_level') {
    if (selectedCity.value) {
      await loadScatterData()
    }
  } else {
    if (!industryScatterData.value) {
      await loadIndustryScatterData()
    } else {
      await nextTick()
      updateChart()
    }
  }
})

// 组件挂载时初始化
onMounted(async () => {
  await loadInitialData()
  await loadIndustryScatterData()
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
  selectedNodes,
  viewMode
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

.mode-hint {
  font-size: 14px;
  color: #666;
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

.industry-legend-hint {
  font-size: 13px;
  color: #666;
  margin: 0;
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

