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

const gradeMap = [
  { min: 10, label: 'A' },
  { min: 8, label: 'B' },
  { min: 6, label: 'C' },
  { min: 4, label: 'D' },
  { min: 2, label: 'E' },
  { min: 0, label: 'F' }
]

const getGrade = (score) => {
  const found = gradeMap.find(g => score >= g.min)
  return found ? found.label : 'F'
}

// 计算两个职位之间的差异度
const calculateDifference = (job1, job2) => {
  // 定义各维度的合理范围（用于归一化）
  const dimensionRanges = {
    salary: { min: 0, max: 100 },      // 薪资范围：0-100K
    experience: { min: 0, max: 10 },   // 经验层级：0-10
    education: { min: 0, max: 10 },    // 学历层级：0-10
    count: { min: 0, max: 50000 },     // 招聘人数：0-50000
    std: { min: 0, max: 50 },          // 薪资标准差：0-50K
    entropy: { min: 0, max: 1 }        // 香农熵：0-1
  }
  
  // 归一化函数 - 将值映射到0-100范围
  const normalize = (value, min, max) => {
    if (max === min) return 50
    const normalized = ((value - min) / (max - min)) * 100
    return Math.max(0, Math.min(100, normalized)) // 限制在0-100
  }
  
  // 获取两个职位的聚合数据（六个维度）
  const salary1 = job1.avg_salary || 0
  const salary2 = job2.avg_salary || 0
  const exp1 = job1.avg_experience || 0
  const exp2 = job2.avg_experience || 0
  const edu1 = job1.avg_education || 0
  const edu2 = job2.avg_education || 0
  const count1 = job1.job_in_city_cnt || 0
  const count2 = job2.job_in_city_cnt || 0
  const std1 = job1.salary_std || 0
  const std2 = job2.salary_std || 0
  const ent1 = job1.avg_shannon_entropy || 0
  const ent2 = job2.avg_shannon_entropy || 0
  
  // 先归一化到0-100范围，再计算差异
  const normSalary1 = normalize(salary1, dimensionRanges.salary.min, dimensionRanges.salary.max)
  const normSalary2 = normalize(salary2, dimensionRanges.salary.min, dimensionRanges.salary.max)
  const normExp1 = normalize(exp1, dimensionRanges.experience.min, dimensionRanges.experience.max)
  const normExp2 = normalize(exp2, dimensionRanges.experience.min, dimensionRanges.experience.max)
  const normEdu1 = normalize(edu1, dimensionRanges.education.min, dimensionRanges.education.max)
  const normEdu2 = normalize(edu2, dimensionRanges.education.min, dimensionRanges.education.max)
  const normCount1 = normalize(count1, dimensionRanges.count.min, dimensionRanges.count.max)
  const normCount2 = normalize(count2, dimensionRanges.count.min, dimensionRanges.count.max)
  const normStd1 = normalize(std1, dimensionRanges.std.min, dimensionRanges.std.max)
  const normStd2 = normalize(std2, dimensionRanges.std.min, dimensionRanges.std.max)
  const normEnt1 = normalize(ent1, dimensionRanges.entropy.min, dimensionRanges.entropy.max)
  const normEnt2 = normalize(ent2, dimensionRanges.entropy.min, dimensionRanges.entropy.max)
  
  // 计算归一化后的差异（都在0-100范围内，可以公平比较）
  const dimensions = [
    {
      name: '薪资水平',
      diff: Math.abs(normSalary1 - normSalary2),
      value1: salary1,
      value2: salary2,
      unit: 'K',
      color: '#5470c6'
    },
    {
      name: '经验要求',
      diff: Math.abs(normExp1 - normExp2),
      value1: exp1,
      value2: exp2,
      unit: '级',
      color: '#91cc75'
    },
    {
      name: '学历要求',
      diff: Math.abs(normEdu1 - normEdu2),
      value1: edu1,
      value2: edu2,
      unit: '级',
      color: '#fac858'
    },
    {
      name: '招聘人数',
      diff: Math.abs(normCount1 - normCount2),
      value1: count1,
      value2: count2,
      unit: '人',
      color: '#ee6666',
      ratio: (() => {
        const larger = Math.max(count1, count2)
        const smaller = Math.min(count1, count2)
        if (smaller === 0) return larger > 0 ? Infinity : 1
        return larger / smaller
      })()
    },
    {
      name: '薪资标准差',
      diff: Math.abs(normStd1 - normStd2),
      value1: std1,
      value2: std2,
      unit: 'K',
      color: '#73c0de'
    },
    {
      name: '香农熵',
      diff: Math.abs(normEnt1 - normEnt2),
      value1: ent1,
      value2: ent2,
      unit: '',
      color: '#9a60b4'
    }
  ]
  
  // 计算每个维度的归一化差异分数（0-2），总分0-12
  let totalScore = 0
  dimensions.forEach(dim => {
    let normalizedScore = 0
    if (dim.name === '招聘人数') {
      const ratio = dim.ratio ?? 1
      if (ratio >= 10) {
        normalizedScore = 2
      } else {
        normalizedScore = ((ratio - 1) / (10 - 1)) * 2
      }
    } else {
      normalizedScore = Math.min(2, (dim.diff / 100) * 2)
    }
    dim.score = normalizedScore
    totalScore += normalizedScore
  })
  
  const grade = getGrade(totalScore)
  
  return {
    totalScore: totalScore.toFixed(2),
    grade,
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
      text: `总差异分数: ${diffData.totalScore}`,
      left: 'center',
      top: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#333'
      },
      subtext: `等级：${diffData.grade}`,
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
            <span style="color: #666;">归一化差异分数：</span>${dim.score.toFixed(2)} / 2<br/>
            <span style="color: #666;">原始差异 (0-100)：</span>${dim.diff.toFixed(2)}${dim.name === '招聘人数' && dim.ratio ? `（倍率：${dim.ratio === Infinity ? '∞' : dim.ratio.toFixed(1)}x）` : ''}<br/>
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
          value: dim.score,
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

