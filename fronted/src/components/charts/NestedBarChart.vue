<template>
  <div class="nested-bar-chart">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="error-message">
      <p>错误: {{ error }}</p>
    </div>
    
    <div v-if="!loading && !error && !hasData" class="empty-state">
      <p>请选择职位以查看嵌套柱状图</p>
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <!-- 显示当前模式 -->
      <div class="chart-header">
        <h3 v-if="!isMicroMode">{{ '宏观对比视图（点击柱子查看详情）' }}</h3>
        <h3 v-else>微观分析视图 - {{ microData.job_title }}</h3>
      </div>
      
      <div ref="chartContainer" :class="['chart-container', { clickable: !isMicroMode }]"></div>
    </div>
    
    <!-- 城市分布模态框 -->
    <div v-if="showCityModal" class="modal-overlay" @click="showCityModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>所有城市分布</h3>
          <button class="close-btn" @click="showCityModal = false">×</button>
        </div>
        <div class="modal-body">
          <div v-for="(city, index) in allCitiesData" :key="index" class="city-item">
            <span class="city-rank">{{ index + 1 }}</span>
            <span class="city-name">{{ city.city }}</span>
            <span class="city-count">{{ city.count }}个</span>
            <span class="city-percent">{{ city.percentage }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['selectJob'])

const chartContainer = ref(null)
const hasData = ref(false)
let chartInstance = null

// 城市分布模态框
const showCityModal = ref(false)
const allCitiesData = ref([])

// 显示城市分布模态框
const showCityDistribution = (cities) => {
  allCitiesData.value = cities
  showCityModal.value = true
}

// 判断是否为微观模式
const isMicroMode = computed(() => {
  return props.data && props.data.micro_analysis !== null
})

// 获取微观数据
const microData = computed(() => {
  return props.data?.micro_analysis || {}
})

// 监听数据变化
watch(() => props.data, (newData) => {
  console.log('NestedBarChart: 数据变化', newData)
  if (newData && newData.macro_comparison && newData.macro_comparison.length > 0) {
    hasData.value = true
    console.log('NestedBarChart: 设置hasData为true')
    nextTick(() => {
      setTimeout(() => {
        renderChart()
      }, 100)
    })
  } else {
    console.log('NestedBarChart: 数据格式不正确或为空', newData)
    hasData.value = false
  }
}, { immediate: true, deep: true })

// 监听error状态
watch(() => props.error, (error) => {
  if (error) {
    console.log('NestedBarChart: 检测到错误，重置hasData', error)
    hasData.value = false
  }
})

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || !props.data) {
    console.log('NestedBarChart: 容器或数据不存在，跳过渲染')
    return
  }

  console.log('NestedBarChart: 开始渲染图表', { isMicroMode: isMicroMode.value })

  // 销毁旧实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新实例
  chartInstance = echarts.init(chartContainer.value)

  let option
  if (isMicroMode.value) {
    option = getMicroAnalysisOption()
  } else {
    option = getMacroComparisonOption()
  }

  chartInstance.setOption(option)
  
  // 添加点击事件（仅在宏观模式下）
  if (!isMicroMode.value) {
    chartInstance.off('click') // 先移除旧的事件监听
    chartInstance.on('click', (params) => {
      console.log('NestedBarChart: 点击事件触发', {
        componentType: params.componentType,
        seriesType: params.seriesType,
        dataIndex: params.dataIndex,
        seriesIndex: params.seriesIndex
      })
      
      // 只处理柱状图的点击，且必须有有效的dataIndex
      if (params.componentType === 'series' 
          && params.seriesType === 'bar' 
          && params.dataIndex !== undefined 
          && params.dataIndex !== null) {
        
        const macroData = props.data.macro_comparison
        if (macroData && macroData[params.dataIndex]) {
          const jobTitle = macroData[params.dataIndex].job_title
          console.log('NestedBarChart: 点击柱子，职位名称:', jobTitle, '类型:', typeof jobTitle)
          
          if (typeof jobTitle === 'string' && jobTitle.trim()) {
            emit('selectJob', jobTitle)
          } else {
            console.error('NestedBarChart: 无效的职位名称', jobTitle)
          }
        }
      }
    })
  }

  console.log('NestedBarChart: 图表渲染完成')
}

// 宏观对比图表配置
const getMacroComparisonOption = () => {
  const data = props.data.macro_comparison
  const jobTitles = data.map(d => d.job_title.substring(0, 8) + '...')
  const skillScores = data.map(d => d.skill_score)
  
  // 为每个柱子生成点状图数据（基于行业集中度）
  const scatterData = []
  data.forEach((item, index) => {
    // 根据行业集中度生成点的数量（集中度越高，点越多）
    // 基础点数 + 根据集中度增加的点数
    const basePoints = 100 // 基础点数
    const concentrationPoints = Math.floor(item.industry_concentration * 3) // 集中度影响的点数
    const pointCount = basePoints + concentrationPoints // 总点数可达到400个
    
    for (let i = 0; i < pointCount; i++) {
      // 在柱子内部随机分布点，覆盖整个柱子高度
      const y = Math.random() * item.skill_score
      // 使用类目名称作为x值，这样散点会自动对齐到对应的柱子
      scatterData.push({
        value: [index, y],
        symbolOffset: [(Math.random() - 0.5) * 170, 0] // 水平偏移，单位是像素（±60像素）
      })
    }
  })

  return {
    title: {
      text: '职位宏观对比（点击柱子查看详情）',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.componentType === 'series' && params.seriesType === 'bar') {
          const item = data[params.dataIndex]
          return `
            <div style="padding: 10px;">
              <strong>${item.job_title}</strong><br/>
              综合技能分数: ${item.skill_score}<br/>
              平均薪资: ${item.avg_salary}K<br/>
              经验要求: ${item.avg_experience_rank}<br/>
              学历要求: ${item.avg_education_rank}<br/>
              行业集中度: ${item.industry_concentration}
            </div>
          `
        }
        return ''
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: 80,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: jobTitles,
      axisLabel: {
        rotate: 45,
        interval: 0
      },
      boundaryGap: true
    },
    yAxis: {
      type: 'value',
      name: '综合技能分数'
    },
    series: [
      {
        name: '综合技能分数',
        type: 'bar',
        data: skillScores,
        barWidth: '60%',
        itemStyle: {
          color: 'rgba(84, 112, 198, 0.6)',
          borderColor: '#5470c6',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            color: 'rgba(84, 112, 198, 0.8)',
            borderColor: '#3a5aa0',
            borderWidth: 2
          }
        },
        cursor: 'pointer',
        z: 1
      },
      {
        name: '行业集中度',
        type: 'scatter',
        data: scatterData,
        symbolSize: 4,
        itemStyle: {
          color: '#fac858',
          opacity: 0.8,
          borderColor: '#ee6666',
          borderWidth: 0.5
        },
        z: 2,
        silent: true // 不响应鼠标事件
      }
    ]
  }
}

// 微观分析图表配置
const getMicroAnalysisOption = () => {
  const micro = props.data.micro_analysis
  const stats = micro.salary_statistics
  
  // 箱线图数据：[min, Q1, median, Q3, max]
  const boxData = [[
    stats.min,
    stats.q1,
    stats.median,
    stats.q3,
    stats.max
  ]]

  return {
    title: {
      text: `${micro.job_title.substring(0, 15)}... 详细分析`,
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.componentType === 'series' && params.seriesType === 'boxplot') {
          return `
            <div style="padding: 10px;">
              <strong>薪资分布</strong><br/>
              最大值: ${stats.max}K<br/>
              上四分位数(Q3): ${stats.q3}K<br/>
              中位数: ${stats.median}K<br/>
              下四分位数(Q1): ${stats.q1}K<br/>
              最小值: ${stats.min}K<br/>
              平均值: ${stats.avg}K
            </div>
          `
        }
        return params.name
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: 120
    },
    xAxis: {
      type: 'category',
      data: ['薪资分布'],
      boundaryGap: true,
      nameGap: 30,
      splitArea: {
        show: false
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '薪资 (K)',
      splitArea: {
        show: true
      }
    },
    series: [
      {
        name: '薪资箱线图',
        type: 'boxplot',
        data: boxData,
        itemStyle: {
          color: '#5470c6',
          borderColor: '#3a5aa0'
        },
        tooltip: {
          formatter: function(param) {
            return [
              '薪资分布:',
              '最大值: ' + param.data[5] + 'K',
              '上四分位数: ' + param.data[4] + 'K',
              '中位数: ' + param.data[3] + 'K',
              '下四分位数: ' + param.data[2] + 'K',
              '最小值: ' + param.data[1] + 'K'
            ].join('<br/>')
          }
        }
      },
      {
        name: '平均值',
        type: 'scatter',
        data: [[0, stats.avg]],
        symbolSize: 10,
        itemStyle: {
          color: '#ee6666'
        },
        label: {
          show: true,
          formatter: function(params) {
            return `中位数: ${params.value[1]}K`
          },
          position: 'right'
        }
      },
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: 60,
        style: {
          text: `前三城市: ${micro.top_cities.map(c => `${c.city}(${c.percentage}%)`).join(', ')}`,
          fontSize: 12,
          fill: '#666',
          cursor: 'pointer',
          textDecoration: 'underline'
        },
        onclick: () => {
          showCityDistribution(micro.all_cities)
        }
      },
      {
        type: 'text',
        left: 'center',
        top: 80,
        style: {
          text: `全局对比 - 平均薪资: ${micro.comparison_with_all.all_positions_avg_salary}K | 百分位: ${micro.comparison_with_all.position_percentile}%`,
          fontSize: 12,
          fill: '#666'
        }
      }
    ]
  }
}

// 窗口大小变化时重新渲染
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.nested-bar-chart {
  width: 100%;
  height: 100%;
  min-height: 600px;
  position: relative;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.chart-header {
  text-align: center;
  padding: 10px 0;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 10px;
}

.chart-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.chart-container {
  width: 100%;
  height: 550px;
}

.chart-container.clickable {
  cursor: pointer;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #5470c6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
  text-align: center;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.city-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.city-item:hover {
  background-color: #f8f9fa;
}

.city-item:last-child {
  border-bottom: none;
}

.city-rank {
  font-weight: bold;
  color: #5470c6;
  width: 40px;
  flex-shrink: 0;
}

.city-name {
  flex: 1;
  color: #333;
  font-weight: 500;
}

.city-count {
  color: #666;
  margin-right: 15px;
}

.city-percent {
  color: #5470c6;
  font-weight: 500;
  min-width: 60px;
  text-align: right;
}
</style>
