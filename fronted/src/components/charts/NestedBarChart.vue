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
      
      // 处理自定义系列的点击
      if (params.componentType === 'series' && params.seriesType === 'custom' && params.data) {
        const itemData = params.data[5]; // 获取存储的itemData
        if (itemData && itemData.job_title) {
          console.log('NestedBarChart: 点击柱子，职位名称:', itemData.job_title);
          emit('selectJob', itemData.job_title);
        }
      }
    })
  }

  console.log('NestedBarChart: 图表渲染完成')
}

// 获取行业集中度颜色
const getConcentrationColor = (concentration, min, max) => {
  const range = max - min || 1;
  const normalized = (concentration - min) / range;
  
  // 使用颜色插值：从浅蓝(低集中度) -> 黄色(中等) -> 深红(高集中度)
  if (normalized < 0.5) {
    // 浅蓝到黄色
    const ratio = normalized * 2;
    const r = Math.floor(84 + (250 - 84) * ratio);
    const g = Math.floor(112 + (200 - 112) * ratio);
    const b = Math.floor(198 + (88 - 198) * ratio);
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    // 黄色到深红
    const ratio = (normalized - 0.5) * 2;
    const r = Math.floor(250 + (238 - 250) * ratio);
    const g = Math.floor(200 + (44 - 200) * ratio);
    const b = Math.floor(88 + (44 - 88) * ratio);
    return `rgb(${r}, ${g}, ${b})`;
  }
};

// 宏观对比图表配置
const getMacroComparisonOption = () => {
  const data = props.data.macro_comparison
  const jobTitles = data.map(d => d.job_title.substring(0, 8) + '...')
  
  // 计算行业集中度的最大值和最小值，用于归一化
  const concentrations = data.map(d => d.industry_concentration)
  const maxConcentration = Math.max(...concentrations)
  const minConcentration = Math.min(...concentrations)
  const concentrationRange = maxConcentration - minConcentration || 1 // 避免除零
  
  // 准备数据，包含内外柱子的值和样式
  const seriesData = data.map((item, index) => {
    const normalizedConcentration = (item.industry_concentration - minConcentration) / concentrationRange;
    const innerHeight = item.skill_score * (normalizedConcentration * 0.6 + 0.4);
    const color = getConcentrationColor(item.industry_concentration, minConcentration, maxConcentration);
    
    console.log('Item:', item.job_title, {
      concentration: item.industry_concentration,
      normalized: normalizedConcentration,
      color: color
    });
    
    return {
      outerValue: item.skill_score,
      innerValue: innerHeight,
      outerStyle: {
        color: 'rgba(84, 112, 198, 0.3)',
        borderColor: '#5470c6',
        borderWidth: 2
      },
      innerStyle: {
        color: color,
        borderColor: '#fff',
        borderWidth: 1,
        fill: color
      },
      itemData: {
        job_title: item.job_title,
        skill_score: item.skill_score,
        avg_salary: item.avg_salary,
        avg_experience_rank: item.avg_experience_rank,
        avg_education_rank: item.avg_education_rank,
        industry_concentration: item.industry_concentration,
        concentrationLevel: normalizedConcentration < 0.33 ? '低' : 
                          normalizedConcentration < 0.67 ? '中' : '高',
        // 添加计算好的颜色
        color: color
      }
    };
  });

  // 使用自定义系列实现嵌套柱状图效果
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
    legend: {
      data: ['综合技能分数', '行业集中度（内部柱子）'],
      top: 35
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: 100,
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
    series: [{
      name: '职位对比',
      type: 'custom',
      renderItem: function(params, api) {
        const dataIndex = params.dataIndex;
        const outerValue = api.value(1);
        const innerValue = api.value(2);
        
        const point = api.coord([api.value(0), outerValue]);
        const innerPoint = api.coord([api.value(0), innerValue]);
        
        const barWidth = api.size([1, 0])[0] * 0.6;
        const innerBarWidth = barWidth * 0.6;
        
        return {
          type: 'group',
          children: [{
            // 外柱
            type: 'rect',
            shape: {
              x: point[0] - barWidth / 2,
              y: point[1],
              width: barWidth,
              height: api.size([0, outerValue])[1],
            },
            style: {
              fill: 'rgba(84, 112, 198, 0.3)',
              stroke: '#5470c6',
              lineWidth: 2
            },
            emphasis: {
              style: {
                fill: 'rgba(84, 112, 198, 0.5)',
                stroke: '#3a5aa0',
                lineWidth: 2
              }
            },
            cursor: 'pointer'
          }, {
            // 内柱
            type: 'rect',
            shape: {
              x: point[0] - innerBarWidth / 2,
              y: innerPoint[1],
              width: innerBarWidth,
              height: api.size([0, innerValue])[1],
            },
            style: {
              fill: api.value(6) || '#ff0000', // 直接使用颜色值
              stroke: '#fff',
              lineWidth: 1
            },
            emphasis: {
              style: {
                fill: api.value(6) || '#ff0000', // 直接使用颜色值
                stroke: '#fff',
                lineWidth: 2,
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.3)'
              }
            }
          }],
          // 添加点击事件
          onclick: function() {
            const itemData = api.value(5);
            if (itemData && itemData.job_title) {
              emit('selectJob', itemData.job_title);
            }
          }
        };
      },
      // 数据格式：[索引, 外柱值, 内柱值, 外柱样式, 内柱样式, 其他数据, 颜色值]
      data: seriesData.map((item, index) => [
        index,  // x轴分类索引
        item.outerValue,
        item.innerValue,
        item.outerStyle,
        item.innerStyle,
        item.itemData,
        item.itemData.color // 直接传递颜色值
      ]),
      encode: {
        x: 0,
        y: 1
      }
    }],
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.componentType === 'series' && params.seriesType === 'custom') {
          const data = params.value[5];
          return `
            <div style="padding: 10px;">
              <strong>${data.job_title}</strong><br/>
              综合技能分数: ${data.skill_score.toFixed(1)}<br/>
              平均薪资: ${data.avg_salary}K<br/>
              经验要求: ${data.avg_experience_rank}<br/>
              学历要求: ${data.avg_education_rank}<br/>
              行业集中度: ${data.industry_concentration.toFixed(2)} (${data.concentrationLevel})
            </div>
          `;
        }
        return '';
      }
    },
    graphic: [
      {
        type: 'text',
        right: 20,
        top: 100,
        style: {
          text: '行业集中度颜色：\n浅蓝(低) → 黄色(中) → 深红(高)',
          fontSize: 11,
          fill: '#666',
          textAlign: 'right'
        }
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
