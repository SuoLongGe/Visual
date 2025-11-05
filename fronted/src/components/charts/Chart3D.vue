<template>
  <div class="chart-3d">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div v-if="hasData" ref="chartContainer" id="3d-chart-container" class="chart-container"></div>
    
    <div v-if="summaryData && !loading" class="summary-info" style="margin-top: 20px;">
      <h3>数据统计</h3>
      <p>经验类型数量: {{ summaryData.summary.experience_count }}</p>
      <p>学历层次数量: {{ summaryData.summary.education_count }}</p>
      <p>数据点数量: {{ summaryData.summary.data_points }}</p>
      <p>最高薪资: {{ summaryData.summary.max_salary }}K</p>
      <p>最低薪资: {{ summaryData.summary.min_salary }}K</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-gl'

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

const emit = defineEmits(['bar-click'])

const chartContainer = ref(null)
const hasData = ref(false)
const summaryData = ref(null)
let chart3D = null
let resizeHandler = null

watch(() => props.data, (newData) => {
  if (newData && newData.experiences && newData.educations) {
    hasData.value = true
    nextTick(() => {
      setTimeout(() => {
        render3DChart(newData)
        calculateSummary(newData)
      }, 100)
    })
  } else {
    hasData.value = false
  }
}, { immediate: true, deep: true })

const render3DChart = (data) => {
  const container = chartContainer.value || document.getElementById('3d-chart-container')
  if (!container) {
    console.error('图表容器不存在')
    return
  }
  
  if (chart3D) {
    chart3D.dispose()
  }
  
  chart3D = echarts.init(container)
  
  const experiences = data.experiences || []
  const educations = data.educations || []
  const data3d = data.data_3d || []
  
  const scatterData = data3d.map(item => [item[0], item[1], item[2]])
  
  const option = {
    title: {
      text: '经验-学历-薪资三维柱状图',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const expIdx = Math.round(params.value[0])
        const eduIdx = Math.round(params.value[1])
        const salary = params.value[2].toFixed(2)
        const exp = experiences[expIdx] || '未知'
        const edu = educations[eduIdx] || '未知'
        return `经验: ${exp}<br/>学历: ${edu}<br/>平均薪资: ${salary}K<br/><small>点击柱体查看详细分析</small>`
      }
    },
    visualMap: {
      show: true,
      dimension: 2,
      min: 0,
      max: Math.max(...data3d.map(item => item[2])),
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      },
      calculable: true,
      precision: 2,
      text: ['高', '低'],
      textStyle: {
        color: '#fff'
      },
      left: 'left',
      top: 'bottom'
    },
    xAxis3D: {
      type: 'category',
      data: experiences,
      name: '工作经验',
      nameTextStyle: {
        color: '#333',
        fontSize: 14
      },
      axisLabel: {
        rotate: -45,
        interval: 0,
        fontSize: 12
      }
    },
    yAxis3D: {
      type: 'category',
      data: educations,
      name: '学历层次',
      nameTextStyle: {
        color: '#333',
        fontSize: 14
      },
      axisLabel: {
        interval: 0,
        fontSize: 12,
        rotate: 0,
        formatter: function(value) {
          return value
        }
      }
    },
    zAxis3D: {
      type: 'value',
      name: '平均薪资(K)',
      nameTextStyle: {
        color: '#333',
        fontSize: 14
      },
      axisLabel: {
        formatter: '{value}K'
      }
    },
    grid3D: {
      boxWidth: 200,
      boxDepth: 80,
      boxHeight: 200,
      viewControl: {
        projection: 'orthographic',
        autoRotate: false,
        autoRotateDirection: 'cw',
        autoRotateSpeed: 10,
        rotateSensitivity: 1,
        zoomSensitivity: 1,
        panSensitivity: 1,
        alpha: 40,
        beta: 0
      },
      light: {
        main: {
          intensity: 1.2,
          shadow: true
        },
        ambient: {
          intensity: 0.3
        }
      }
    },
    series: [
      {
        type: 'bar3D',
        data: scatterData.map(function(item) {
          return {
            value: [item[0], item[1], item[2]]
          }
        }),
        shading: 'lambert',
        label: {
          show: false,
          formatter: function(param) {
            return param.value[2].toFixed(1)
          }
        },
        itemStyle: {
          opacity: 0.8
        },
        emphasis: {
          label: {
            show: true
          },
          itemStyle: {
            color: '#900'
          }
        }
      }
    ]
  }
  
  chart3D.setOption(option)
  
  // 添加点击事件
  chart3D.on('click', function(params) {
    if (params.componentType === 'series' && params.seriesType === 'bar3D') {
      const expIdx = Math.round(params.value[0])
      const eduIdx = Math.round(params.value[1])
      const exp = experiences[expIdx]
      const edu = educations[eduIdx]
      
      if (exp && edu) {
        // 触发事件，传递经验和学历
        emit('bar-click', {
          experience: exp,
          education: edu,
          salary: params.value[2]
        })
      }
    }
  })
  
  // 窗口大小改变时重新调整图表
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  
  resizeHandler = () => {
    if (chart3D) {
      chart3D.resize()
    }
  }
  
  window.addEventListener('resize', resizeHandler)
}

const calculateSummary = (data) => {
  summaryData.value = {
    summary: {
      experience_count: data.experiences.length,
      education_count: data.educations.length,
      data_points: data.data_3d.length,
      max_salary: Math.max(...data.data_3d.map(item => item[2])).toFixed(2),
      min_salary: Math.min(...data.data_3d.filter(item => item[2] > 0).map(item => item[2])).toFixed(2)
    },
    experiences: data.experiences,
    educations: data.educations
  }
}

onUnmounted(() => {
  if (chart3D) {
    chart3D.dispose()
    chart3D = null
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

