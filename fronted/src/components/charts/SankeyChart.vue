<template>
  <div class="sankey-chart">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="error-message">
      <p>错误: {{ error }}</p>
    </div>
    
    <div v-if="!loading && !error && !hasData" class="empty-state">
      <p>{{ emptyMessage }}</p>
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <div ref="chartContainer" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
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
  },
  emptyMessage: {
    type: String,
    default: '暂无数据'
  }
})

const chartContainer = ref(null)
const hasData = ref(false)
let chartInstance = null

// 监听数据变化
watch(() => props.data, (newData) => {
  console.log('SankeyChart: 数据变化', newData)
  if (newData && newData.nodes && newData.links && newData.nodes.length > 0) {
    hasData.value = true
    console.log('SankeyChart: 设置hasData为true', {
      nodes: newData.nodes.length,
      links: newData.links.length
    })
    nextTick(() => {
      setTimeout(() => {
        renderChart()
      }, 100)
    })
  } else {
    console.log('SankeyChart: 数据格式不正确或为空', newData)
    hasData.value = false
  }
}, { immediate: true, deep: true })

// 监听error状态
watch(() => props.error, (error) => {
  if (error) {
    console.log('SankeyChart: 检测到错误，重置hasData', error)
    hasData.value = false
  }
})

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || !props.data) {
    console.log('SankeyChart: 容器或数据不存在，跳过渲染')
    return
  }

  console.log('SankeyChart: 开始渲染图表')

  // 销毁旧实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新实例
  chartInstance = echarts.init(chartContainer.value)

  // 定义分类颜色
  const categoryColors = {
    '技能要求': '#5470c6',
    '行业分布': '#91cc75',
    '市场需求': '#fac858',
    '特征组合': '#ee6666',
    '薪资结果': '#73c0de'
  }

  // 为节点添加颜色
  const nodesWithColor = props.data.nodes.map(node => ({
    ...node,
    itemStyle: {
      color: categoryColors[node.category] || '#999'
    }
  }))

  const option = {
    title: {
      text: '职位特征与薪资流动桑基图',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#2c3e50'
      }
    },
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: function(params) {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>流量: ${params.data.value} 个职位`
        } else {
          return `${params.data.name}<br/>分类: ${params.data.category}`
        }
      }
    },
    series: [
      {
        type: 'sankey',
        data: nodesWithColor,
        links: props.data.links,
        emphasis: {
          focus: 'adjacency'
        },
        lineStyle: {
          color: 'gradient',
          curveness: 0.5,
          opacity: 0.3
        },
        label: {
          position: 'right',
          fontSize: 11,
          color: '#333',
          formatter: '{b}'
        },
        itemStyle: {
          borderWidth: 1,
          borderColor: '#fff'
        },
        left: '5%',
        right: '20%',
        top: '15%',
        bottom: '10%',
        nodeWidth: 20,
        nodeGap: 12,
        layoutIterations: 32
      }
    ],
    legend: {
      data: props.data.categories || [],
      orient: 'vertical',
      right: 10,
      top: 80,
      textStyle: {
        fontSize: 12
      },
      formatter: function(name) {
        return name
      },
      itemWidth: 20,
      itemHeight: 14
    }
  }

  chartInstance.setOption(option)
  console.log('SankeyChart: 图表渲染完成')
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
.sankey-chart {
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

.chart-container {
  width: 100%;
  height: 600px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #999;
  font-size: 16px;
}
</style>
