<template>
  <div class="position-parallel-chart">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="error-message">
      <p>错误: {{ error }}</p>
    </div>
    
    <div v-if="!loading && !error && !hasData" class="empty-state">
      <p>请选择职位以查看平行坐标图</p>
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <div ref="chartContainer" class="chart-container"></div>
      
      <div class="legend-section">
        <div class="legend-title">职位图例</div>
        <div class="legend-items">
          <div 
            v-for="(position, index) in positions" 
            :key="position.job_title"
            class="legend-item"
            @mouseenter="highlightPosition(index)"
            @mouseleave="unhighlightPosition"
          >
            <span 
              class="legend-color" 
              :style="{ backgroundColor: positionColors[index] }"
            ></span>
            <span class="legend-label">{{ position.job_title }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

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

const chartContainer = ref(null)
const hasData = ref(false)
const positions = ref([])
const dimensions = ref([])

// 定义颜色方案（3个职位）
const positionColors = ['#5470c6', '#91cc75', '#ee6666']

// D3对象
let svg = null
let g = null
let yScales = {}
let highlightedIndex = -1

// 监听数据变化
watch(() => props.data, (newData) => {
  console.log('PositionParallelChart: 数据变化', newData)
  if (newData && newData.dimensions && newData.positions && newData.positions.length > 0) {
    dimensions.value = newData.dimensions
    positions.value = newData.positions
    hasData.value = true
    console.log('PositionParallelChart: 设置hasData为true', {
      dimensions: dimensions.value,
      positions: positions.value
    })
    nextTick(() => {
      setTimeout(() => {
        renderChart()
      }, 100)
    })
  } else {
    console.log('PositionParallelChart: 数据格式不正确或为空', newData)
    hasData.value = false
  }
}, { immediate: true, deep: true })

// 监听loading和error状态（只在有错误时重置hasData）
watch([() => props.loading, () => props.error], ([loading, error]) => {
  // 只有在有错误时才重置hasData，loading状态变化不应该影响已加载的数据
  if (error) {
    console.log('PositionParallelChart: 检测到错误，重置hasData', error)
    hasData.value = false
  }
  // 如果loading变为false且没有错误，保持hasData状态（由数据watch控制）
})

const renderChart = () => {
  if (!chartContainer.value || !dimensions.value.length || !positions.value.length) return
  
  const container = chartContainer.value
  const containerWidth = container.clientWidth || 1000
  const containerHeight = container.clientHeight || 600
  
  // 清除旧图表
  d3.select(container).selectAll('*').remove()
  
  // 设置边距
  const margin = { top: 60, right: 80, bottom: 60, left: 80 }
  const width = containerWidth - margin.left - margin.right
  const height = containerHeight - margin.top - margin.bottom
  
  // 创建SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)
  
  g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  
  // 计算每个轴的x位置
  const axisCount = dimensions.value.length
  const axisSpacing = width / (axisCount - 1)
  
  // 创建y轴比例尺（每个维度0-100）
  dimensions.value.forEach((dim, i) => {
    yScales[dim] = d3.scaleLinear()
      .domain([0, 100])
      .range([height, 0])
  })
  
  // 绘制背景网格线
  dimensions.value.forEach((dim, i) => {
    const xPos = i * axisSpacing
    
    // 绘制水平网格线
    for (let j = 0; j <= 5; j++) {
      const yPos = yScales[dim](j * 20)
      g.append('line')
        .attr('x1', xPos - 20)
        .attr('x2', xPos + 20)
        .attr('y1', yPos)
        .attr('y2', yPos)
        .attr('stroke', '#e0e0e0')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '3,3')
    }
  })
  
  // 绘制坐标轴
  dimensions.value.forEach((dim, i) => {
    const xPos = i * axisSpacing
    
    // 创建y轴
    const yAxis = d3.axisLeft(yScales[dim])
      .ticks(5)
      .tickFormat(d => d)
    
    g.append('g')
      .attr('class', 'axis')
      .attr('transform', `translate(${xPos}, 0)`)
      .call(yAxis)
      .selectAll('text')
      .style('font-size', '12px')
      .style('fill', '#666')
    
    // 添加维度标签
    g.append('text')
      .attr('class', 'dimension-label')
      .attr('x', xPos)
      .attr('y', -20)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .style('font-weight', 'bold')
      .style('fill', '#2c3e50')
      .text(dim)
  })
  
  // 绘制折线（每个职位一条线）
  const line = d3.line()
    .x((d, i) => i * axisSpacing)
    .y((d, i) => yScales[dimensions.value[i]](d))
    .curve(d3.curveMonotoneX)
  
  positions.value.forEach((position, posIndex) => {
    const pathData = position.values.map((val, i) => ({
      value: val,
      dimension: dimensions.value[i]
    }))
    
    // 绘制折线
    const path = g.append('path')
      .datum(position.values)
      .attr('class', `position-line position-${posIndex}`)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', positionColors[posIndex])
      .attr('stroke-width', 3)
      .attr('opacity', highlightedIndex === -1 || highlightedIndex === posIndex ? 1 : 0.2)
      .style('cursor', 'pointer')
    
    // 添加数据点
    position.values.forEach((value, dimIndex) => {
      const xPos = dimIndex * axisSpacing
      const yPos = yScales[dimensions.value[dimIndex]](value)
      
      const circle = g.append('circle')
        .attr('class', `data-point point-${posIndex}-${dimIndex}`)
        .attr('cx', xPos)
        .attr('cy', yPos)
        .attr('r', 6)
        .attr('fill', positionColors[posIndex])
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .attr('opacity', highlightedIndex === -1 || highlightedIndex === posIndex ? 1 : 0.2)
        .style('cursor', 'pointer')
      
      // 添加交互提示
      circle.on('mouseover', function(event) {
        d3.select(this).attr('r', 8)
        
        const tooltip = d3.select('body').append('div')
          .attr('class', 'parallel-tooltip')
          .style('opacity', 0)
          .html(`
            <div class="tooltip-header">${position.job_title}</div>
            <div class="tooltip-content">
              <div><strong>${dimensions.value[dimIndex]}:</strong> ${value.toFixed(1)}</div>
              <div class="tooltip-details">
                <div>薪资: ${position.details.salary}</div>
                <div>经验: ${position.details.experience}</div>
                <div>学历: ${position.details.education}</div>
                <div>行业熵: ${position.details.industry_entropy}</div>
                <div>职位频率: ${position.details.job_frequency}</div>
              </div>
            </div>
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px')
        
        tooltip.transition()
          .duration(200)
          .style('opacity', 1)
      })
      .on('mouseout', function() {
        d3.select(this).attr('r', 6)
        d3.selectAll('.parallel-tooltip').remove()
      })
      
      // 折线悬停效果
      path.on('mouseover', function() {
        highlightPosition(posIndex)
      })
      .on('mouseout', function() {
        unhighlightPosition()
      })
    })
  })
}

const highlightPosition = (index) => {
  highlightedIndex = index
  updateHighlight()
}

const unhighlightPosition = () => {
  highlightedIndex = -1
  updateHighlight()
}

const updateHighlight = () => {
  if (!g) return
  
  // 更新所有线条和点的透明度
  positions.value.forEach((position, posIndex) => {
    const opacity = highlightedIndex === -1 || highlightedIndex === posIndex ? 1 : 0.2
    
    g.selectAll(`.position-${posIndex}`)
      .attr('opacity', opacity)
    
    position.values.forEach((value, dimIndex) => {
      g.selectAll(`.point-${posIndex}-${dimIndex}`)
        .attr('opacity', opacity)
    })
  })
}

// 窗口大小改变时重新渲染
let resizeHandler = null

onMounted(() => {
  resizeHandler = () => {
    if (hasData.value) {
      renderChart()
    }
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  if (svg) {
    svg.remove()
  }
  d3.selectAll('.parallel-tooltip').remove()
})
</script>

<style scoped>
.position-parallel-chart {
  width: 100%;
  height: 100%;
  min-height: 600px;
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
  border: 4px solid rgba(84, 112, 198, 0.1);
  border-top: 4px solid #5470c6;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 0.8s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  background: #fee;
  border: 2px solid #f44336;
  border-radius: 8px;
  color: #c33;
  text-align: center;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 16px;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  min-height: 500px;
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
}

.legend-section {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.legend-title {
  font-size: 14px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 10px;
}

.legend-items {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.legend-item:hover {
  background-color: rgba(84, 112, 198, 0.1);
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.legend-label {
  font-size: 13px;
  color: #2c3e50;
  font-weight: 500;
}

:deep(.axis line) {
  stroke: #666;
  stroke-width: 1.5;
}

:deep(.axis path) {
  stroke: #666;
  stroke-width: 1.5;
}

:deep(.axis text) {
  fill: #666;
  font-size: 12px;
}
</style>

<style>
/* 全局工具提示样式 */
.parallel-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-width: 250px;
}

.parallel-tooltip .tooltip-header {
  font-size: 15px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #67C23A;
  border-bottom: 2px solid #67C23A;
  padding-bottom: 6px;
}

.parallel-tooltip .tooltip-content {
  line-height: 1.6;
}

.parallel-tooltip .tooltip-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 12px;
  color: #ccc;
}

.parallel-tooltip .tooltip-details div {
  margin: 4px 0;
}
</style>

