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

// 将数据标准化到0-100范围
const normalizeData = (jobs) => {
  if (jobs.length === 0) return []
  
  // 收集所有值用于归一化
  const salaries = jobs.map(j => j.salary_value)
  const experienceRanks = jobs.map(j => j.experience_rank)
  const educationRanks = jobs.map(j => j.education_rank)
  const recruitCounts = jobs.map(j => j.recruit_count)
  const cityLevels = jobs.map(j => cityLevelMap[j.city_level] || 1)
  
  const maxSalary = Math.max(...salaries)
  const maxRecruitCount = Math.max(...recruitCounts)
  
  // 标准化函数
  const normalize = (value, max) => max > 0 ? (value / max) * 100 : 0
  
  return jobs.map(job => ({
    name: job.job_title,
    value: [
      normalize(job.salary_value, maxSalary),
      job.experience_rank * 10,  // 经验rank是1-10，映射到0-100
      job.education_rank * 10,   // 学历rank是1-10，映射到0-100
      normalize(job.recruit_count, maxRecruitCount),
      (cityLevelMap[job.city_level] || 1) * 10  // 城市等级映射到0-100
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
            <span style="color: #666;">薪资：</span>${job.salary_value}K<br/>
            <span style="color: #666;">经验层级：</span>${job.experience_rank}/10<br/>
            <span style="color: #666;">学历层级：</span>${job.education_rank}/10<br/>
            <span style="color: #666;">招聘人数：</span>${job.recruit_count}<br/>
            <span style="color: #666;">城市等级：</span>${job.city_level}
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
        { name: '经验要求', max: 100 },
        { name: '学历要求', max: 100 },
        { name: '招聘人数', max: 100 },
        { name: '城市等级', max: 100 }
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


