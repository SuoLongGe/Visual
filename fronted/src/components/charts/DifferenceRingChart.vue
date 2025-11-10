<template>
  <div class="difference-ring-chart">
    <div v-show="selectedJobs.length < 2" class="no-data-message">
      <p>请从散点图中选择2个职位进行差异对比</p>
      <p class="hint">点击散点图中的气泡选中职位</p>
    </div>
    <div v-show="selectedJobs.length > 2" class="warning-message">
      <p>差异对比仅支持2个职位</p>
      <p class="hint">当前已选择 {{ selectedJobs.length }} 个职位</p>
    </div>
    <div v-show="selectedJobs.length === 2" ref="chartContainer" class="chart-container"></div>
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

// 计算两个职位之间的差异度
const calculateDifference = (job1, job2) => {
  // 归一化函数 - 将不同维度的值统一到0-100范围
  const normalize = (value, min, max) => {
    if (max === min) return 50
    return ((value - min) / (max - min)) * 100
  }
  
  // 获取两个职位的原始数据
  const salary1 = job1.salary_value || 0
  const salary2 = job2.salary_value || 0
  const exp1 = job1.experience_rank || 0
  const exp2 = job2.experience_rank || 0
  const edu1 = job1.education_rank || 0
  const edu2 = job2.education_rank || 0
  const count1 = job1.recruit_count || 0
  const count2 = job2.recruit_count || 0
  
  // 城市等级映射
  const cityLevelMap = { 'A': 10, 'B': 7, 'C': 5, 'D': 3, '未知': 1 }
  const city1 = cityLevelMap[job1.city_level] || 1
  const city2 = cityLevelMap[job2.city_level] || 1
  
  // 计算归一化的值（用于展示）
  const salaryMin = Math.min(salary1, salary2)
  const salaryMax = Math.max(salary1, salary2)
  const countMin = Math.min(count1, count2)
  const countMax = Math.max(count1, count2)
  
  // 计算各维度的差异（欧式距离）
  const dimensions = [
    {
      name: '薪资水平',
      diff: Math.abs(salary1 - salary2),
      value1: salary1,
      value2: salary2,
      unit: 'K',
      color: '#5470c6'
    },
    {
      name: '经验要求',
      diff: Math.abs(exp1 - exp2) * 10, // 放大10倍使其更明显
      value1: exp1,
      value2: exp2,
      unit: '级',
      color: '#91cc75'
    },
    {
      name: '学历要求',
      diff: Math.abs(edu1 - edu2) * 10, // 放大10倍使其更明显
      value1: edu1,
      value2: edu2,
      unit: '级',
      color: '#fac858'
    },
    {
      name: '招聘人数',
      diff: Math.abs(count1 - count2),
      value1: count1,
      value2: count2,
      unit: '人',
      color: '#ee6666'
    },
    {
      name: '城市等级',
      diff: Math.abs(city1 - city2) * 10, // 放大10倍使其更明显
      value1: city1,
      value2: city2,
      unit: '级',
      color: '#73c0de'
    }
  ]
  
  // 计算总差异度
  const totalDiff = dimensions.reduce((sum, dim) => sum + dim.diff, 0)
  
  // 计算每个维度的贡献百分比
  dimensions.forEach(dim => {
    dim.percentage = totalDiff > 0 ? (dim.diff / totalDiff) * 100 : 20
  })
  
  return {
    totalDiff: totalDiff.toFixed(2),
    dimensions,
    job1,
    job2
  }
}

// 更新图表
const updateChart = () => {
  if (!chartInstance || props.selectedJobs.length !== 2) {
    console.log('DifferenceChart: 更新失败 - chartInstance:', !!chartInstance, 'jobs:', props.selectedJobs.length)
    return
  }
  
  console.log('DifferenceChart: 开始更新图表')
  const diffData = calculateDifference(props.selectedJobs[0], props.selectedJobs[1])
  
  const option = {
    title: {
      text: `总体差异度: ${diffData.totalDiff}`,
      left: 'center',
      top: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333'
      },
      subtext: '基于五个维度',
      subtextStyle: {
        fontSize: 12,
        color: '#999'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const dim = params.data.dimData
        return `
          <div style="padding: 8px;">
            <strong>${dim.name}</strong><br/>
            <span style="color: #666;">差异值：</span>${dim.diff.toFixed(2)}<br/>
            <span style="color: #666;">贡献度：</span>${dim.percentage.toFixed(1)}%<br/>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;"/>
            <span style="color: #666;">职位1：</span>${dim.value1}${dim.unit}<br/>
            <span style="color: #666;">职位2：</span>${dim.value2}${dim.unit}
          </div>
        `
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      data: diffData.dimensions.map(d => d.name),
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '差异度分布',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          fontSize: 11
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        data: diffData.dimensions.map(dim => ({
          value: dim.percentage,
          name: dim.name,
          itemStyle: {
            color: dim.color
          },
          dimData: dim
        }))
      }
    ]
  }
  
  chartInstance.setOption(option, true)
}

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return
  
  chartInstance = echarts.init(chartContainer.value)
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  if (props.selectedJobs.length === 2) {
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
  console.log('DifferenceChart: 接收到新数据', newJobs.length)
  await nextTick()
  
  if (newJobs.length === 2) {
    if (!chartInstance && chartContainer.value) {
      console.log('DifferenceChart: 初始化图表')
      initChart()
    } else if (chartInstance) {
      console.log('DifferenceChart: 更新图表')
      updateChart()
    }
  } else if (chartInstance && newJobs.length !== 2) {
    // 清空图表
    console.log('DifferenceChart: 清空图表')
    chartInstance.clear()
  }
}, { deep: true, immediate: true })

// 组件挂载
onMounted(() => {
  if (props.selectedJobs.length === 2) {
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
.difference-ring-chart {
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

.no-data-message,
.warning-message {
  text-align: center;
  padding: 40px 20px;
}

.no-data-message {
  color: #999;
}

.warning-message {
  color: #f39c12;
}

.no-data-message p,
.warning-message p {
  margin: 8px 0;
  font-size: 14px;
}

.no-data-message p:first-child,
.warning-message p:first-child {
  font-size: 15px;
  font-weight: 500;
}

.no-data-message p:first-child {
  color: #666;
}

.warning-message p:first-child {
  color: #e67e22;
}

.hint {
  font-size: 12px;
  color: #aaa;
}
</style>

