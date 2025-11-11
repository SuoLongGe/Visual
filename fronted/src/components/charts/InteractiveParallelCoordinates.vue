<template>
  <div class="interactive-viz">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error-message">错误: {{ error }}</div>
    
    <div v-if="hasData" class="viz-container">
      <!-- 控制面板 -->
      <div class="control-panel">
        <div class="control-group">
          <label>线条颜色映射：</label>
          <select v-model="colorBy">
            <option value="salary">薪资</option>
            <option value="entropy">岗位多样性</option>
            <option value="job_count">岗位数量</option>
          </select>
        </div>
        
        <div class="control-group">
          <label>线条透明度：</label>
          <input type="range" v-model.number="lineOpacity" min="0.1" max="1" step="0.1" />
          <span>{{ lineOpacity.toFixed(1) }}</span>
        </div>
        
        <div class="control-group">
          <label>显示模式：</label>
          <select v-model="displayMode">
            <option value="all">全部数据</option>
            <option value="top200">前200条</option>
            <option value="top100">前100条</option>
          </select>
        </div>
        
        <div class="control-group">
          <button @click="clearSelection" class="btn-clear">清除选择</button>
        </div>
        
        <div class="info-group">
          <span class="info-label">已选择:</span>
          <span class="info-value">{{ selectedData.length }} / {{ displayedCount }}</span>
        </div>
      </div>
      
      <!-- 主可视化区域 -->
      <div class="main-viz-area">
        <!-- 左侧：平行坐标图 -->
        <div class="parallel-section">
          <h3>平行坐标图 <span class="subtitle">（可在轴上拖动刷选）</span></h3>
          <div ref="parallelContainer" class="parallel-container"></div>
        </div>
        
        <!-- 右侧：散点图矩阵 -->
        <div class="scatter-section">
          <h3>散点图矩阵 <span class="subtitle">（可框选数据点）</span></h3>
          <div class="scatter-grid">
            <div class="scatter-item">
              <h4>薪资 vs 岗位多样性</h4>
              <div ref="scatter1" class="scatter-container"></div>
            </div>
            <div class="scatter-item">
              <h4>薪资 vs 岗位数量</h4>
              <div ref="scatter2" class="scatter-container"></div>
            </div>
            <div class="scatter-item">
              <h4>岗位多样性 vs 岗位数量</h4>
              <div ref="scatter3" class="scatter-container"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 图例和统计信息 -->
      <div class="legend-panel">
        <div class="legend-item">
          <span class="legend-label">颜色映射:</span>
          <span class="legend-value">{{ colorByLabel }}</span>
        </div>
        <div class="legend-item">
          <span class="legend-label">交互提示:</span>
          <span class="legend-value">在轴上拖动刷选 | 在散点图上框选 | 鼠标悬停查看详情</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed, onUnmounted } from 'vue'
import * as d3 from 'd3'
import '@/assets/styles/chart.css'

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

// Refs
const parallelContainer = ref(null)
const scatter1 = ref(null)
const scatter2 = ref(null)
const scatter3 = ref(null)
const hasData = ref(false)

// 控制参数
const colorBy = ref('salary')
const lineOpacity = ref(0.3)
const displayMode = ref('top200')

// 数据和状态
const allData = ref([])
const displayedData = ref([])
const selectedData = ref([])
const displayedCount = ref(0)
const brushRanges = ref({}) // 存储每个轴的刷选范围

// D3 对象
let parallelSvg = null
let scatter1Svg = null
let scatter2Svg = null
let scatter3Svg = null
let tooltip = null
let dimensions = []
let yScales = {}
let colorScale = null

const colorByLabel = computed(() => {
  return colorBy.value === 'salary' ? '平均薪资' : 
         colorBy.value === 'entropy' ? '岗位多样性（香农熵）' : '岗位数量'
})

// 监听数据变化
watch(() => props.data, (newData) => {
  if (newData && newData.data && Array.isArray(newData.data)) {
    allData.value = newData.data
    hasData.value = true
    nextTick(() => {
      setTimeout(() => {
        initVisualization()
      }, 100)
    })
  } else {
    hasData.value = false
  }
}, { immediate: true, deep: true })

// 监听控制参数变化
watch([colorBy, lineOpacity, displayMode], () => {
  if (hasData.value) {
    updateVisualization()
  }
})

// 初始化可视化
const initVisualization = () => {
  if (!parallelContainer.value || allData.value.length === 0) return
  
  // 准备数据
  prepareData()
  
  // 创建颜色比例尺
  createColorScale()
  
  // 渲染平行坐标图
  renderParallelCoordinates()
  
  // 渲染散点图
  renderScatterPlots()
}

// 准备数据
const prepareData = () => {
  let data = [...allData.value]
  
  // 根据显示模式筛选
  if (displayMode.value === 'top200') {
    data = data.slice(0, 200)
  } else if (displayMode.value === 'top100') {
    data = data.slice(0, 100)
  }
  
  displayedData.value = data
  displayedCount.value = data.length
  
  // 定义维度
  dimensions = [
    { name: 'city', label: '城市', type: 'categorical', accessor: d => d.city },
    { name: 'experience', label: '经验', type: 'categorical', accessor: d => d.experience },
    { name: 'education', label: '学历', type: 'categorical', accessor: d => d.education },
    { name: 'salary', label: '薪资', type: 'numeric', accessor: d => d.salary },
    { name: 'entropy', label: '多样性', type: 'numeric', accessor: d => d.entropy },
    { name: 'company_type', label: '公司类型', type: 'categorical', accessor: d => d.company_type }
  ]
}

// 创建颜色比例尺
const createColorScale = () => {
  let values = []
  if (colorBy.value === 'salary') {
    values = displayedData.value.map(d => d.salary)
  } else if (colorBy.value === 'entropy') {
    values = displayedData.value.map(d => d.entropy)
  } else {
    values = displayedData.value.map(d => d.job_count)
  }
  
  const min = d3.min(values) || 0
  const max = d3.max(values) || 100
  
  colorScale = d3.scaleSequential(d3.interpolateViridis)
    .domain([max, min])
}

// 渲染平行坐标图
const renderParallelCoordinates = () => {
  const container = parallelContainer.value
  if (!container) return
  
  // 清除旧内容
  d3.select(container).selectAll('*').remove()
  
  const width = container.clientWidth || 800
  const height = 500
  const margin = { top: 60, right: 30, bottom: 30, left: 30 }
  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom
  
  // 创建 SVG
  parallelSvg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
  
  const g = parallelSvg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  
  // X 比例尺
  const xScale = d3.scalePoint()
    .domain(dimensions.map(d => d.name))
    .range([0, innerWidth])
    .padding(0.2)
  
  // Y 比例尺
  dimensions.forEach(dim => {
    if (dim.type === 'numeric') {
      const values = displayedData.value.map(dim.accessor)
      const min = d3.min(values) || 0
      const max = d3.max(values) || 100
      yScales[dim.name] = d3.scaleLinear()
        .domain([min * 0.95, max * 1.05])
        .range([innerHeight, 0])
        .nice()
    } else {
      const allValues = [...new Set(displayedData.value.map(dim.accessor))].sort()
      yScales[dim.name] = d3.scalePoint()
        .domain(allValues)
        .range([innerHeight, 0])
        .padding(0.5)
    }
  })
  
  // 绘制轴（带动画）
  dimensions.forEach((dim, dimIndex) => {
    const x = xScale(dim.name)
    const axisG = g.append('g')
      .attr('class', 'axis')
      .attr('transform', `translate(${x},0)`)
      .attr('opacity', 0)
    
    // 轴线
    axisG.append('line')
      .attr('y1', innerHeight)
      .attr('y2', innerHeight)
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
    
    // 轴标题
    axisG.append('text')
      .attr('y', -15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(dim.label)
    
    // 轴从下到上展开动画
    axisG.select('line')
      .transition()
      .duration(800)
      .delay(dimIndex * 120)
      .attr('y1', 0)
    
    // 轴标题渐入
    axisG
      .transition()
      .duration(500)
      .delay(dimIndex * 120)
      .attr('opacity', 1)
    
    // 刻度（带延迟渐入）
    if (dim.type === 'numeric') {
      const axis = d3.axisLeft(yScales[dim.name]).ticks(5)
      const ticksGroup = axisG.append('g')
        .attr('opacity', 0)
        .call(axis)
      
      ticksGroup
        .transition()
        .duration(400)
        .delay(dimIndex * 120 + 300)
        .attr('opacity', 1)
    } else {
      const values = yScales[dim.name].domain()
      values.forEach((value, valueIndex) => {
        const y = yScales[dim.name](value)
        axisG.append('text')
          .attr('x', -10)
          .attr('y', y)
          .attr('dy', '0.32em')
          .attr('text-anchor', 'end')
          .attr('font-size', '10px')
          .attr('fill', '#666')
          .attr('opacity', 0)
          .text(value.length > 12 ? value.substring(0, 12) + '...' : value)
          .transition()
          .duration(300)
          .delay(dimIndex * 120 + 300 + valueIndex * 30)
          .attr('opacity', 1)
      })
    }
    
    // 添加刷选功能（延迟添加，等动画完成）
    const brush = d3.brushY()
      .extent([[-10, 0], [10, innerHeight]])
      .on('brush end', (event) => handleBrush(event, dim.name))
    
    const brushG = axisG.append('g')
      .attr('class', 'brush')
      .attr('opacity', 0)
    
    setTimeout(() => {
      brushG
        .call(brush)
        .transition()
        .duration(300)
        .attr('opacity', 1)
    }, dimIndex * 120 + 1000)
  })
  
  // 绘制线条（带动画）
  const line = d3.line()
  
  const pathsGroup = g.append('g')
    .attr('class', 'lines')
  
  const paths = pathsGroup.selectAll('.line')
    .data(displayedData.value)
    .enter()
    .append('path')
    .attr('class', 'line')
    .attr('d', d => {
      const points = dimensions.map(dim => {
        const x = xScale(dim.name)
        const y = yScales[dim.name](dim.accessor(d))
        return [x, y]
      })
      return line(points)
    })
    .attr('fill', 'none')
    .attr('stroke', d => getColor(d))
    .attr('stroke-width', 1.5)
    .attr('opacity', 0)
    .attr('data-id', (d, i) => i)
    .on('mouseover', function(event, d) {
      highlightData(d)
      showTooltip(event, d)
    })
    .on('mouseout', function() {
      unhighlightAll()
      hideTooltip()
    })
    .on('click', function(event, d) {
      toggleSelection(d)
    })
  
  // 线条从左到右绘制动画
  paths.each(function() {
    const path = d3.select(this)
    const totalLength = this.getTotalLength()
    
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
  })
  
  paths
    .transition()
    .duration(1500)
    .delay((d, i) => i * 3) // 每条线错开 3ms
    .attr('stroke-dashoffset', 0)
    .attr('opacity', lineOpacity.value)
    .on('end', function() {
      // 动画结束后移除 dasharray，避免影响后续交互
      d3.select(this)
        .attr('stroke-dasharray', 'none')
    })
}

// 渲染散点图
const renderScatterPlots = () => {
  renderScatter(scatter1.value, 'salary', 'entropy', '薪资', '岗位多样性')
  renderScatter(scatter2.value, 'salary', 'job_count', '薪资', '岗位数量')
  renderScatter(scatter3.value, 'entropy', 'job_count', '岗位多样性', '岗位数量')
}

// 渲染单个散点图
const renderScatter = (container, xKey, yKey, xLabel, yLabel) => {
  if (!container) return
  
  d3.select(container).selectAll('*').remove()
  
  const width = container.clientWidth || 300
  const height = 250
  const margin = { top: 20, right: 20, bottom: 40, left: 50 }
  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom
  
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
  
  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  
  // 比例尺
  const xValues = displayedData.value.map(d => d[xKey])
  const yValues = displayedData.value.map(d => d[yKey])
  
  const xScale = d3.scaleLinear()
    .domain([d3.min(xValues) * 0.95, d3.max(xValues) * 1.05])
    .range([0, innerWidth])
    .nice()
  
  const yScale = d3.scaleLinear()
    .domain([d3.min(yValues) * 0.95, d3.max(yValues) * 1.05])
    .range([innerHeight, 0])
    .nice()
  
  // 坐标轴（带渐入动画）
  const xAxisG = g.append('g')
    .attr('transform', `translate(0,${innerHeight})`)
    .attr('opacity', 0)
    .call(d3.axisBottom(xScale).ticks(5))
  
  const yAxisG = g.append('g')
    .attr('opacity', 0)
    .call(d3.axisLeft(yScale).ticks(5))
  
  xAxisG.transition()
    .duration(400)
    .delay(200)
    .attr('opacity', 1)
  
  yAxisG.transition()
    .duration(400)
    .delay(200)
    .attr('opacity', 1)
  
  // 轴标签（带渐入动画）
  g.append('text')
    .attr('x', innerWidth / 2)
    .attr('y', innerHeight + 35)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('fill', '#666')
    .attr('opacity', 0)
    .text(xLabel)
    .transition()
    .duration(400)
    .delay(400)
    .attr('opacity', 1)
  
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -innerHeight / 2)
    .attr('y', -35)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('fill', '#666')
    .attr('opacity', 0)
    .text(yLabel)
    .transition()
    .duration(400)
    .delay(400)
    .attr('opacity', 1)
  
  // 绘制点（带动画）
  g.selectAll('.dot')
    .data(displayedData.value)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('cx', d => xScale(d[xKey]))
    .attr('cy', d => yScale(d[yKey]))
    .attr('r', 0)
    .attr('fill', d => getColor(d))
    .attr('opacity', 0)
    .attr('data-id', (d, i) => i)
    .on('mouseover', function(event, d) {
      highlightData(d)
      showTooltip(event, d)
    })
    .on('mouseout', function() {
      unhighlightAll()
      hideTooltip()
    })
    .on('click', function(event, d) {
      toggleSelection(d)
    })
    .transition()
    .duration(600)
    .delay((d, i) => i * 2)
    .attr('r', 4)
    .attr('opacity', 0.7)
  
  // 添加框选功能（延迟添加，等点的动画完成）
  const brush = d3.brush()
    .extent([[0, 0], [innerWidth, innerHeight]])
    .on('end', (event) => handleScatterBrush(event, xKey, yKey, xScale, yScale))
  
  const brushG = g.append('g')
    .attr('class', 'brush')
    .attr('opacity', 0)
  
  setTimeout(() => {
    brushG
      .call(brush)
      .transition()
      .duration(300)
      .attr('opacity', 1)
  }, 1000)
}

// 处理平行坐标图刷选
const handleBrush = (event, dimName) => {
  if (!event.selection) {
    delete brushRanges.value[dimName]
  } else {
    const [y0, y1] = event.selection
    const scale = yScales[dimName]
    
    if (scale.invert) {
      // 数值型
      brushRanges.value[dimName] = [scale.invert(y1), scale.invert(y0)]
    } else {
      // 分类型
      const domain = scale.domain()
      brushRanges.value[dimName] = domain.filter(d => {
        const y = scale(d)
        return y >= y0 && y <= y1
      })
    }
  }
  
  applyBrushFilters()
}

// 处理散点图框选
const handleScatterBrush = (event, xKey, yKey, xScale, yScale) => {
  if (!event.selection) {
    selectedData.value = []
  } else {
    const [[x0, y0], [x1, y1]] = event.selection
    
    selectedData.value = displayedData.value.filter(d => {
      const x = xScale(d[xKey])
      const y = yScale(d[yKey])
      return x >= x0 && x <= x1 && y >= y0 && y <= y1
    })
  }
  
  updateHighlight()
}

// 应用刷选过滤
const applyBrushFilters = () => {
  if (Object.keys(brushRanges.value).length === 0) {
    selectedData.value = []
    updateHighlight()
    return
  }
  
  selectedData.value = displayedData.value.filter(d => {
    return Object.entries(brushRanges.value).every(([dimName, range]) => {
      const dim = dimensions.find(dim => dim.name === dimName)
      const value = dim.accessor(d)
      
      if (Array.isArray(range)) {
        // 分类型或数值型范围
        if (typeof range[0] === 'number') {
          return value >= range[0] && value <= range[1]
        } else {
          return range.includes(value)
        }
      }
      return true
    })
  })
  
  updateHighlight()
}

// 高亮数据
const highlightData = (data) => {
  const index = displayedData.value.indexOf(data)
  
  // 高亮平行坐标图的线
  d3.selectAll('.line')
    .attr('opacity', function() {
      const id = parseInt(d3.select(this).attr('data-id'))
      return id === index ? 1 : 0.1
    })
    .attr('stroke-width', function() {
      const id = parseInt(d3.select(this).attr('data-id'))
      return id === index ? 3 : 1.5
    })
  
  // 高亮散点图的点
  d3.selectAll('.dot')
    .attr('opacity', function() {
      const id = parseInt(d3.select(this).attr('data-id'))
      return id === index ? 1 : 0.1
    })
    .attr('r', function() {
      const id = parseInt(d3.select(this).attr('data-id'))
      return id === index ? 6 : 4
    })
}

// 取消高亮
const unhighlightAll = () => {
  if (selectedData.value.length > 0) {
    updateHighlight()
  } else {
    d3.selectAll('.line')
      .attr('opacity', lineOpacity.value)
      .attr('stroke-width', 1.5)
    
    d3.selectAll('.dot')
      .attr('opacity', 0.7)
      .attr('r', 4)
  }
}

// 更新高亮（基于选中数据）
const updateHighlight = () => {
  if (selectedData.value.length === 0) {
    d3.selectAll('.line')
      .attr('opacity', lineOpacity.value)
      .attr('stroke-width', 1.5)
    
    d3.selectAll('.dot')
      .attr('opacity', 0.7)
      .attr('r', 4)
  } else {
    const selectedIndices = new Set(
      selectedData.value.map(d => displayedData.value.indexOf(d))
    )
    
    d3.selectAll('.line')
      .attr('opacity', function() {
        const id = parseInt(d3.select(this).attr('data-id'))
        return selectedIndices.has(id) ? 0.9 : 0.1
      })
      .attr('stroke-width', function() {
        const id = parseInt(d3.select(this).attr('data-id'))
        return selectedIndices.has(id) ? 2.5 : 1
      })
    
    d3.selectAll('.dot')
      .attr('opacity', function() {
        const id = parseInt(d3.select(this).attr('data-id'))
        return selectedIndices.has(id) ? 0.9 : 0.1
      })
      .attr('r', function() {
        const id = parseInt(d3.select(this).attr('data-id'))
        return selectedIndices.has(id) ? 5 : 3
      })
  }
}

// 切换选择状态
const toggleSelection = (data) => {
  const index = selectedData.value.indexOf(data)
  if (index === -1) {
    selectedData.value.push(data)
  } else {
    selectedData.value.splice(index, 1)
  }
  updateHighlight()
}

// 清除选择
const clearSelection = () => {
  selectedData.value = []
  brushRanges.value = {}
  
  // 清除所有刷选
  d3.selectAll('.brush').each(function() {
    d3.select(this).call(d3.brush().clear)
    d3.select(this).call(d3.brushY().clear)
  })
  
  updateHighlight()
}

// 获取颜色
const getColor = (d) => {
  let value
  if (colorBy.value === 'salary') {
    value = d.salary
  } else if (colorBy.value === 'entropy') {
    value = d.entropy
  } else {
    value = d.job_count
  }
  return colorScale(value)
}

// 更新可视化
const updateVisualization = () => {
  createColorScale()
  renderParallelCoordinates()
  renderScatterPlots()
}

// Tooltip
const showTooltip = (event, d) => {
  tooltip = d3.select('body')
    .append('div')
    .attr('class', 'viz-tooltip')
    .style('opacity', 0)
    .style('position', 'absolute')
    .style('background', 'rgba(0, 0, 0, 0.9)')
    .style('color', '#fff')
    .style('padding', '12px')
    .style('border-radius', '6px')
    .style('pointer-events', 'none')
    .style('font-size', '12px')
    .style('z-index', 10000)
  
  tooltip.html(`
    <div style="font-weight: bold; margin-bottom: 8px;">数据详情</div>
    <div>城市: <strong>${d.city}</strong></div>
    <div>经验: <strong>${d.experience}</strong></div>
    <div>学历: <strong>${d.education}</strong></div>
    <div>公司类型: <strong>${d.company_type}</strong></div>
    <div>薪资: <strong>${d.salary.toFixed(2)}K</strong></div>
    <div>多样性: <strong>${d.entropy.toFixed(4)}</strong></div>
    <div>岗位数: <strong>${d.job_count}</strong></div>
  `)
    .style('left', (event.pageX + 15) + 'px')
    .style('top', (event.pageY - 10) + 'px')
    .transition()
    .duration(200)
    .style('opacity', 1)
}

const hideTooltip = () => {
  if (tooltip) {
    tooltip.transition()
      .duration(200)
      .style('opacity', 0)
      .remove()
    tooltip = null
  }
}

onUnmounted(() => {
  hideTooltip()
})
</script>

<style scoped>
.interactive-viz {
  width: 100%;
  min-height: 800px;
}

.viz-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-panel {
  display: flex;
  gap: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 6px;
  flex-wrap: wrap;
  align-items: center;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.control-group select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.control-group input[type="range"] {
  width: 100px;
}

.btn-clear {
  padding: 8px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-clear:hover {
  background: #d32f2f;
}

.info-group {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background: #e3f2fd;
  border-radius: 4px;
  margin-left: auto;
}

.info-label {
  font-size: 14px;
  color: #666;
}

.info-value {
  font-size: 14px;
  color: #1976d2;
  font-weight: bold;
}

.main-viz-area {
  display: flex;
  gap: 20px;
}

.parallel-section {
  flex: 2;
  min-width: 0;
}

.scatter-section {
  flex: 1;
  min-width: 400px;
}

.parallel-section h3,
.scatter-section h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.subtitle {
  font-size: 12px;
  font-weight: normal;
  color: #999;
}

.parallel-container {
  width: 100%;
  min-height: 500px;
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.scatter-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.scatter-item {
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px;
}

.scatter-item h4 {
  margin: 0 0 10px 0;
  color: #555;
  font-size: 13px;
}

.scatter-container {
  width: 100%;
  min-height: 250px;
}

.legend-panel {
  display: flex;
  gap: 30px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.legend-label {
  font-size: 13px;
  color: #666;
}

.legend-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.loading {
  padding: 40px;
  text-align: center;
  color: #999;
}

.error-message {
  padding: 20px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c33;
  margin: 20px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-viz-area {
    flex-direction: column;
  }
  
  .scatter-section {
    min-width: 0;
  }
  
  .scatter-grid {
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .scatter-item {
    flex: 1;
    min-width: 300px;
  }
}
</style>

