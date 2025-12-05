<template>
  <div class="radar-comparison-chart">
    <div v-if="selectedJobs.length === 0" class="no-data-message">
      <p>请从散点图中选择2-3个职位进行对比</p>
      <p class="hint">点击散点图中的气泡即可选中</p>
    </div>
    <div v-show="selectedJobs.length > 0" ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

// Props
const props = defineProps({
  selectedJobs: {
    type: Array,
    default: () => []
  }
})

const chartContainer = ref(null)
let chartInstance = null

// 城市等级映射到数值
const cityLevelMap = {
  'A': 10,
  'B': 7,
  'C': 5,
  'D': 3,
  '未知': 1
}

// 将数据标准化到0-100范围（六个维度）
// 使用数据集动态范围，并为max≈min的情况添加10% padding，避免绘制成直线
const normalizeData = (jobs) => {
  if (jobs.length === 0) return []
  
  // 根据当前数据计算范围，并添加10% padding
  const getRange = (values, fallbackSpan = 10) => {
    const valid = values.filter(v => typeof v === 'number' && !Number.isNaN(v))
    if (!valid.length) {
      return { min: 0, max: fallbackSpan }
    }
    let minVal = Math.min(...valid)
    let maxVal = Math.max(...valid)
    if (maxVal === minVal) {
      const pad = Math.max(Math.abs(maxVal || 1) * 0.1, 1)
      minVal = Math.max(0, minVal - pad)
      maxVal = maxVal + pad
    } else {
      const span = maxVal - minVal
      const pad = Math.max(span * 0.1, 1)
      minVal = Math.max(0, minVal - pad)
      maxVal = maxVal + pad
    }
    return { min: minVal, max: maxVal }
  }
  
  // 归一化函数 - 将值映射到0-100范围
  const normalize = (value, min, max) => {
    if (max === min) return 0
    const normalized = ((value - min) / (max - min)) * 100
    return Math.max(0, Math.min(100, normalized)) // 限制在0-100
  }
  
  const salaries = jobs.map(j => j.avg_salary || 0)
  const experiences = jobs.map(j => j.avg_experience || 0)
  const educations = jobs.map(j => j.avg_education || 0)
  const recruitCounts = jobs.map(j => j.job_in_city_cnt || 0)
  const salaryStds = jobs.map(j => j.salary_std || 0)
  const entropies = jobs.map(j => j.avg_shannon_entropy || 0)

  // 对招聘人数做log压缩，避免几万 vs 几百差异过大
  const recruitCountsTransformed = recruitCounts.map(c => Math.log10((c || 0) + 1))

  const salaryRange = getRange(salaries, 100)
  const experienceRange = getRange(experiences, 10)
  const educationRange = getRange(educations, 10)
  const countRange = getRange(recruitCountsTransformed, Math.log10(50000 + 1))
  const stdRange = getRange(salaryStds, 50)
  const entropyRange = getRange(entropies, 1)
  
  return jobs.map(job => ({
    name: job.job_title,
    value: [
      normalize(job.avg_salary || 0, salaryRange.min, salaryRange.max),
      normalize(job.avg_experience || 0, experienceRange.min, experienceRange.max),
      normalize(job.avg_education || 0, educationRange.min, educationRange.max),
      normalize(Math.log10(((job.job_in_city_cnt || 0)) + 1), countRange.min, countRange.max),
      normalize(job.salary_std || 0, stdRange.min, stdRange.max),
      normalize(job.avg_shannon_entropy || 0, entropyRange.min, entropyRange.max)
    ],
    rawData: job
  }))
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || props.selectedJobs.length === 0) {
    console.log('RadarChart: 更新失败 - chartInstance:', !!chartInstance, 'jobs:', props.selectedJobs.length)
    return
  }
  
  console.log('RadarChart: 开始更新图表，职位数:', props.selectedJobs.length)
  const normalizedData = normalizeData(props.selectedJobs)
  
  // 生成颜色
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
  
  const option = {
    title: {
      text: '职位多维对比',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const job = params.data.rawData
        return `
          <div style="padding: 8px;">
            <strong>${job.job_title}</strong><br/>
            <span style="color: #666;">平均薪资：</span>${(job.avg_salary || 0).toFixed(2)}K<br/>
            <span style="color: #666;">薪资标准差：</span>${(job.salary_std || 0).toFixed(2)}K<br/>
            <span style="color: #666;">平均经验：</span>${(job.avg_experience || 0).toFixed(2)}（层级）<br/>
            <span style="color: #666;">平均学历：</span>${(job.avg_education || 0).toFixed(2)}（层级）<br/>
            <span style="color: #666;">招聘人数：</span>${job.job_in_city_cnt || 0}<br/>
            <span style="color: #666;">香农熵：</span>${(job.avg_shannon_entropy || 0).toFixed(3)}<br/>
          </div>
        `
      }
    },
    legend: {
      top: 35,
      left: 'center',
      data: normalizedData.map(d => d.name),
      textStyle: {
        fontSize: 11
      }
    },
    radar: {
      indicator: [
        { name: '薪资水平', max: 100 },
        { name: '平均经验', max: 100 },
        { name: '平均学历', max: 100 },
        { name: '招聘人数', max: 100 },
        { name: '薪资标准差', max: 100 },
        { name: '香农熵', max: 100 }
      ],
      center: ['50%', '60%'],
      radius: '50%',
      splitNumber: 4,
      shape: 'polygon',
      name: {
        textStyle: {
          color: '#333',
          fontSize: 12
        }
      },
      splitLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250, 250, 250, 0.3)', 'rgba(200, 200, 200, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      }
    },
    series: [{
      type: 'radar',
      data: normalizedData.map((item, index) => ({
        ...item,
        lineStyle: {
          color: colors[index % colors.length],
          width: 2
        },
        areaStyle: {
          color: colors[index % colors.length],
          opacity: 0.2
        },
        symbol: 'circle',
        symbolSize: 6
      }))
    }]
  }
  
  chartInstance.setOption(option, true)
}

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return
  
  chartInstance = echarts.init(chartContainer.value)
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  if (props.selectedJobs.length > 0) {
    updateChart()
  }
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 监听选中职位变化
watch(() => props.selectedJobs, async (newJobs) => {
  console.log('RadarChart: 接收到新数据', newJobs.length)
  await nextTick()
  
  if (newJobs.length > 0) {
    if (!chartInstance && chartContainer.value) {
      console.log('RadarChart: 初始化图表')
      initChart()
    } else if (chartInstance) {
      console.log('RadarChart: 更新图表')
      updateChart()
    }
  }
}, { deep: true, immediate: true })

// 组件挂载
onMounted(() => {
  if (props.selectedJobs.length > 0) {
    initChart()
  }
})

// 组件卸载
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.radar-comparison-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.no-data-message {
  text-align: center;
  color: #999;
  padding: 40px 20px;
}

.no-data-message p {
  margin: 8px 0;
  font-size: 14px;
}

.no-data-message p:first-child {
  font-size: 15px;
  color: #666;
  font-weight: 500;
}

.hint {
  font-size: 12px;
  color: #aaa;
}
</style>


