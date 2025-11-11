<template>
  <div class="chart-3d">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <div ref="chartContainer" id="3d-chart-container" class="chart-container"></div>
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
  
  // 计算容器尺寸以自适应比例
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight
  const aspectRatio = containerWidth / containerHeight
  
  // 根据容器大小动态调整盒子尺寸
  const boxWidth = Math.min(200, containerWidth * 0.4)
  const boxDepth = Math.min(100, containerWidth * 0.2)
  const boxHeight = Math.min(200, containerHeight * 0.35)
  
  const option = {
    backgroundColor: '#fafafa',
    title: {
      text: '经验-学历-薪资 3D 分析',
      subtext: '点击柱体查看详细分析 | 鼠标拖动旋转视角',
      left: 'center',
      top: 15,
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      borderColor: '#409EFF',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 13
      },
      formatter: function(params) {
        const expIdx = Math.round(params.value[0])
        const eduIdx = Math.round(params.value[1])
        const salary = params.value[2].toFixed(2)
        const exp = experiences[expIdx] || '未知'
        const edu = educations[eduIdx] || '未知'
        return `
          <div style="padding: 8px;">
            <div style="font-size: 14px; font-weight: bold; margin-bottom: 8px; color: #409EFF;">
              ${exp} × ${edu}
            </div>
            <div style="margin: 4px 0;">
              <span style="color: #67C23A;">💰 平均薪资：</span>
              <span style="font-size: 16px; font-weight: bold;">${salary}K</span>
            </div>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 11px; color: #aaa;">
              💡 点击柱体查看该组合的详细分布
            </div>
          </div>
        `
      }
    },
    visualMap: {
      show: true,
      dimension: 2,
      min: 0,
      max: Math.max(...data3d.map(item => item[2])),
      inRange: {
        color: [
          '#1a237e', '#283593', '#303f9f', '#3949ab', '#3f51b5',
          '#5c6bc0', '#7986cb', '#9fa8da', '#c5cae9', 
          '#64b5f6', '#42a5f5', '#2196f3', '#1e88e5', 
          '#ffeb3b', '#ffc107', '#ff9800', '#ff5722', '#f44336'
        ]
      },
      calculable: true,
      precision: 2,
      text: ['高薪', '低薪'],
      textStyle: {
        color: '#333',
        fontSize: 12
      },
      left: 'left',
      bottom: '5%',
      itemWidth: 20,
      itemHeight: 140
    },
    xAxis3D: {
      type: 'category',
      data: experiences,
      name: '工作经验',
      nameTextStyle: {
        color: '#000',
        fontSize: 16,
        fontWeight: 'bold',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: [4, 8],
        borderRadius: 4
      },
      nameGap: 35,
      axisLabel: {
        rotate: -45,
        interval: 0,
        fontSize: 13,
        color: '#000',
        fontWeight: '600',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        padding: [3, 6],
        borderRadius: 3
      },
      axisLine: {
        lineStyle: {
          color: '#333',
          width: 3
        }
      },
      axisTick: {
        lineStyle: {
          color: '#333',
          width: 2
        },
        length: 6
      }
    },
    yAxis3D: {
      type: 'category',
      data: educations,
      name: '学历层次',
      nameTextStyle: {
        color: '#000',
        fontSize: 16,
        fontWeight: 'bold',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: [4, 8],
        borderRadius: 4
      },
      nameGap: 35,
      axisLabel: {
        interval: 0,
        fontSize: 13,
        rotate: 0,
        color: '#000',
        fontWeight: '600',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        padding: [3, 6],
        borderRadius: 3,
        formatter: function(value) {
          return value
        }
      },
      axisLine: {
        lineStyle: {
          color: '#333',
          width: 3
        }
      },
      axisTick: {
        lineStyle: {
          color: '#333',
          width: 2
        },
        length: 6
      }
    },
    zAxis3D: {
      type: 'value',
      name: '平均薪资(K)',
      nameTextStyle: {
        color: '#000',
        fontSize: 16,
        fontWeight: 'bold',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: [4, 8],
        borderRadius: 4
      },
      nameGap: 30,
      axisLabel: {
        formatter: '{value}K',
        fontSize: 13,
        color: '#000',
        fontWeight: '600',
        backgroundColor: 'rgba(255, 255, 255, 0.85)',
        padding: [3, 6],
        borderRadius: 3
      },
      axisLine: {
        lineStyle: {
          color: '#333',
          width: 3
        }
      },
      axisTick: {
        lineStyle: {
          color: '#333',
          width: 2
        },
        length: 6
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(51, 51, 51, 0.25)',
          width: 1.5
        }
      }
    },
    grid3D: {
      boxWidth: boxWidth,
      boxDepth: boxDepth,
      boxHeight: boxHeight,
      environment: 'auto',
      viewControl: {
        projection: 'perspective',
        autoRotate: false,
        autoRotateDirection: 'cw',
        autoRotateSpeed: 8,
        rotateSensitivity: 1.5,
        zoomSensitivity: 1.2,
        panSensitivity: 1,
        distance: 250,
        alpha: 25,
        beta: 40,
        minAlpha: 5,
        maxAlpha: 90,
        minDistance: 150,
        maxDistance: 400,
        animation: true,
        animationDurationUpdate: 1000,
        animationEasingUpdate: 'cubicOut'
      },
      light: {
        main: {
          intensity: 1.5,
          shadow: true,
          shadowQuality: 'high',
          alpha: 30,
          beta: 40
        },
        ambient: {
          intensity: 0.6
        },
        ambientCubemap: {
          texture: null,
          diffuseIntensity: 0.5,
          specularIntensity: 0.5
        }
      },
      postEffect: {
        enable: true,
        bloom: {
          enable: false
        },
        SSAO: {
          enable: true,
          quality: 'medium',
          radius: 2,
          intensity: 1
        }
      },
      temporalSuperSampling: {
        enable: true
      }
    },
    series: [
      {
        type: 'bar3D',
        data: scatterData.map(function(item, index) {
          return {
            value: [item[0], item[1], 0],
            targetValue: item[2],
            itemIndex: index
          }
        }),
        shading: 'realistic',
        realisticMaterial: {
          metalness: 0.3,
          roughness: 0.5
        },
        label: {
          show: false,
          distance: 2,
          formatter: function(param) {
            return param.value[2].toFixed(1) + 'K'
          },
          textStyle: {
            fontSize: 10,
            color: '#333',
            fontWeight: 'bold'
          }
        },
        itemStyle: {
          opacity: 0.92,
          borderWidth: 0.5,
          borderColor: 'rgba(255, 255, 255, 0.3)'
        },
        emphasis: {
          label: {
            show: true,
            textStyle: {
              fontSize: 12,
              color: '#fff',
              backgroundColor: 'rgba(0,0,0,0.7)',
              padding: 4,
              borderRadius: 3
            }
          },
          itemStyle: {
            opacity: 1,
            borderWidth: 2,
            borderColor: '#FFD700'
          }
        },
        animationDuration: 2000,
        animationEasing: 'elasticOut',
        animationDelay: function(idx) {
          return idx * 20
        }
      }
    ]
  }
  
  chart3D.setOption(option)
  
  // 柱体生长动画
  setTimeout(() => {
    const updatedData = scatterData.map(function(item) {
      return {
        value: [item[0], item[1], item[2]]
      }
    })
    
    chart3D.setOption({
      series: [{
        data: updatedData
      }]
    })
  }, 100)
  
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
.chart-3d {
  width: 100%;
}

.chart-wrapper {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 650px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.chart-container:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}


.loading {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  border: 4px solid rgba(84, 112, 198, 0.1);
  border-top: 4px solid #5470c6;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: #666;
  font-size: 14px;
}

.result.error {
  background: linear-gradient(135deg, #fee 0%, #fdd 100%);
  border: 1px solid #fcc;
  color: #c33;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.result.error pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-container {
    height: 500px;
  }
}
</style>

