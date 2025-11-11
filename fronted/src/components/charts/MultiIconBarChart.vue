<template>
  <div class="multi-icon-bar-chart">
    <h3 v-if="title" class="chart-title">{{ title }}</h3>
    <p v-if="description" class="chart-description">{{ description }}</p>
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as d3 from 'd3'
import { useResizeObserver } from '@/composables/useResizeObserver.js'
import '@/assets/styles/chart.css'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  title: {
    type: String,
    default: 'Math-Based 多维 Icon 柱状图'
  },
  description: {
    type: String,
    default: '展示职位在数量、学历、经验等维度的综合排名'
  }
})

const chartContainer = ref(null)
let svg = null
let g = null
let xScale = null
let yScale = null

const { width, height } = useResizeObserver(chartContainer)

// 创建图标路径（SVG path）- 更美观的图标设计
const createIconPath = (type) => {
  const icons = {
    // 小人图标（招聘数量）- Material Design风格
    person: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z',
    // 学士帽图标（学历要求）- 毕业帽设计
    education: 'M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z',
    // 秒表图标（经验要求）- 时钟设计
    experience: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z'
  }
  return icons[type] || icons.person
}

// 将归一化值转换为格子数量（向上取整）
const valueToGridCount = (value) => {
  // 将 0-1 的值映射到 0-10 个格子，向上取整
  // 例如：0.784 -> 8个格子，0.123 -> 2个格子
  return Math.ceil(value * 10)
}

// 创建图标组
const createIconGroup = (type, color) => {
  const iconGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  iconGroup.setAttribute('class', `icon-${type}`)
  
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
  path.setAttribute('d', createIconPath(type))
  path.setAttribute('fill', color)
  path.setAttribute('transform', 'scale(0.8) translate(2, 2)')
  
  iconGroup.appendChild(path)
  return iconGroup
}

const renderChart = () => {
  if (!chartContainer.value || !props.data || props.data.length === 0) return

  const container = chartContainer.value
  const containerWidth = container.clientWidth || 1000
  const containerHeight = container.clientHeight || 600

  // 清除旧图表
  d3.select(container).selectAll('*').remove()

  // 设置边距（缩小间距）
  const margin = { top: 30, right: 60, bottom: 80, left: 150 }
  const chartWidth = containerWidth - margin.left - margin.right
  const chartHeight = containerHeight - margin.top - margin.bottom

  // 创建SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)

  g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // 创建X轴比例尺（用于格子图标布局，0-10个格子）
  // 10稍微比10个icon大一点，所以用10.2作为最大值
  xScale = d3.scaleLinear()
    .domain([0, 10.2])
    .range([0, chartWidth])

  // 创建Y轴比例尺（职位名称）
  yScale = d3.scaleBand()
    .domain(props.data.map(d => d.job_title))
    .range([0, chartHeight])
    .padding(0.3)

  // 每个职位的高度
  const jobHeight = yScale.bandwidth()
  const barHeight = jobHeight * 0.25  // 每条行的高度
  const barSpacing = jobHeight * 0.05  // 行之间的间距

  // 添加X轴（只显示0和10两个刻度）
  const xAxis = d3.axisBottom(xScale)
    .tickValues([0, 10])
    .tickFormat(d => String(d))
  
  g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${chartHeight})`)
    .call(xAxis)
  
  // 添加X轴标签
  g.append('text')
    .attr('class', 'axis-label')
    .attr('x', chartWidth / 2)
    .attr('y', chartHeight + 50)
    .attr('fill', '#666')
    .attr('font-size', '12px')
    .attr('text-anchor', 'middle')
    .text('格子数量')

  // 添加Y轴
  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(yScale))
    .selectAll('text')
    .style('font-size', '12px')
    .style('fill', '#333')

  // 添加网格线（只显示0和10位置的网格线）
  const gridLines = g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${chartHeight})`)
  
  // 只添加0和10位置的网格线
  gridLines.selectAll('.grid-line')
    .data([0, 10])
    .enter()
    .append('line')
    .attr('class', 'grid-line')
    .attr('x1', d => xScale(d))
    .attr('x2', d => xScale(d))
    .attr('y1', 0)
    .attr('y2', -chartHeight)
    .attr('stroke', '#e0e0e0')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')

  // 定义三种柱子的颜色和图标类型
  const barConfigs = [
    { key: 'records_count_norm', color: '#5470c6', icon: 'person' },
    { key: 'education_rank', color: '#91cc75', icon: 'education' },
    { key: 'experience_rank', color: '#fac858', icon: 'experience' }
  ]

  // 格子图标配置
  // 计算让10个icon铺满整个宽度（稍微超出一点到10.2的位置）
  const maxIconsPerRow = 10  // 每行最多显示10个图标
  const totalIconsWidth = chartWidth  // 10个icon要铺满整个宽度
  const iconSpacing = totalIconsWidth * 0.02  // 图标之间的间距（2%的宽度）
  const iconSize = (totalIconsWidth - iconSpacing * (maxIconsPerRow - 1)) / maxIconsPerRow  // 计算每个图标的大小

  // 为每个职位绘制三条格子图标行
  props.data.forEach((job, jobIndex) => {
    const yPos = yScale(job.job_title)
    const centerY = yPos + jobHeight / 2
    
    barConfigs.forEach((config, barIndex) => {
      const value = job[config.key] || 0
      const gridCount = valueToGridCount(value)  // 转换为格子数量
      
      // 计算每条行的Y位置（三条行垂直居中排列）
      const totalBarsHeight = barHeight * 3 + barSpacing * 2
      const startY = centerY - totalBarsHeight / 2
      const barY = startY + barIndex * (barHeight + barSpacing)
      
      // 绘制行背景（浅色）
      g.append('rect')
        .attr('class', `bar-bg bar-${config.key}`)
        .attr('x', 0)
        .attr('y', barY)
        .attr('width', chartWidth)
        .attr('height', barHeight)
        .attr('fill', '#f0f0f0')
        .attr('rx', 4)
        .attr('opacity', 0.2)

      // 创建图标组容器（用于整体交互）
      const iconRowGroup = g.append('g')
        .attr('class', `icon-row icon-row-${config.key}`)
        .attr('data-job', job.job_title)
        .attr('data-type', config.key)
        .attr('data-value', value)

      // 绘制格子图标
      const iconCenterY = barY + barHeight / 2
      const startX = 0  // 起始X位置从0开始
      
      for (let i = 0; i < gridCount && i < maxIconsPerRow; i++) {
        const iconX = startX + i * (iconSize + iconSpacing)
        
        // 创建单个图标组
        const iconGroup = iconRowGroup.append('g')
          .attr('class', `icon-cell icon-${config.icon}`)
          .attr('transform', `translate(${iconX}, ${iconCenterY})`)
          .style('cursor', 'pointer')

        // 绘制图标背景（可选，增加视觉层次）
        iconGroup.append('rect')
          .attr('x', -iconSize / 2)
          .attr('y', -iconSize / 2)
          .attr('width', iconSize)
          .attr('height', iconSize)
          .attr('fill', config.color)
          .attr('opacity', 0.12)
          .attr('rx', 4)
          .attr('stroke', config.color)
          .attr('stroke-width', 0.5)
          .attr('stroke-opacity', 0.3)

        // 绘制图标（居中显示）
        // 根据iconSize动态调整缩放比例，使图标填满背景框
        const iconScale = iconSize / 24  // 24是原始图标大小基准
        iconGroup.append('path')
          .attr('d', createIconPath(config.icon))
          .attr('fill', config.color)
          .attr('transform', `scale(${iconScale * 0.7}) translate(-11, -11)`)
          .style('opacity', 0.95)

        // 添加交互：鼠标悬浮单个图标
        iconGroup
          .on('mouseover', function(event) {
            const rect = d3.select(this).select('rect')
            const path = d3.select(this).select('path')
            
            rect
              .transition()
              .duration(150)
              .attr('opacity', 0.25)
              .attr('stroke', config.color)
              .attr('stroke-width', 1.5)
              .attr('stroke-opacity', 0.6)
            
            const iconScale = iconSize / 24
            path
              .transition()
              .duration(150)
              .attr('opacity', 1)
              .attr('transform', `scale(${iconScale * 0.8}) translate(-11, -11)`)

            // 显示提示框
            const tooltip = d3.select('body').append('div')
              .attr('class', 'tooltip visible')
              .style('opacity', 0)
              .style('position', 'absolute')
              .style('background', 'rgba(0, 0, 0, 0.85)')
              .style('color', 'white')
              .style('padding', '12px')
              .style('border-radius', '6px')
              .style('pointer-events', 'none')
              .style('font-size', '13px')
              .style('z-index', '1000')
              .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
              .html(`
                <div style="font-weight: 600; margin-bottom: 6px;">${job.job_title}</div>
                <div style="margin-bottom: 4px;">数值: ${d3.format('.3f')(value)}</div>
                <div style="margin-bottom: 4px;">格子数量: ${gridCount} / 10</div>
                <div style="color: #aaa; font-size: 11px;">综合得分: ${d3.format('.3f')(job.composite_score || 0)}</div>
              `)
              .style('left', (event.pageX + 10) + 'px')
              .style('top', (event.pageY - 10) + 'px')

            tooltip.transition()
              .duration(200)
              .style('opacity', 1)
          })
          .on('mouseout', function() {
            const rect = d3.select(this).select('rect')
            const path = d3.select(this).select('path')
            
            rect
              .transition()
              .duration(150)
              .attr('opacity', 0.12)
              .attr('stroke', config.color)
              .attr('stroke-width', 0.5)
              .attr('stroke-opacity', 0.3)
            
            const iconScale = iconSize / 24
            path
              .transition()
              .duration(150)
              .attr('opacity', 0.95)
              .attr('transform', `scale(${iconScale * 0.7}) translate(-11, -11)`)

            d3.selectAll('.tooltip').remove()
          })
      }

      // 如果格子数量超过最大值，显示省略提示
      if (gridCount > maxIconsPerRow) {
        const lastIconX = startX + maxIconsPerRow * (iconSize + iconSpacing)
        g.append('text')
          .attr('class', 'overflow-indicator')
          .attr('x', lastIconX + 10)
          .attr('y', iconCenterY)
          .attr('dy', '0.35em')
          .attr('fill', '#999')
          .attr('font-size', '11px')
          .text(`+${gridCount - maxIconsPerRow}`)
      }

      // 添加数值标签（在行右侧）
      g.append('text')
        .attr('class', 'bar-label')
        .attr('x', chartWidth + 8)
        .attr('y', iconCenterY)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'start')
        .attr('fill', '#666')
        .attr('font-size', '11px')
        .attr('font-weight', '500')
        .text(`${d3.format('.3f')(value)} (${gridCount})`)
    })
  })

  // 图例已移除：不再显示“招聘数量 / 学历要求 / 经验要求”文字说明
}

// 监听数据变化
watch(() => props.data, () => {
  renderChart()
}, { deep: true })

// 监听容器大小变化
watch([width, height], () => {
  renderChart()
})

onMounted(() => {
  renderChart()
})

onUnmounted(() => {
  if (svg) {
    svg.remove()
  }
  d3.selectAll('.tooltip').remove()
})
</script>

<style scoped>
.multi-icon-bar-chart {
  width: 100%;
  height: 100%;
}

.chart-container {
  width: 100%;
  height: 600px;
  min-height: 400px;
}

.chart-title {
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.chart-description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
  font-size: 14px;
}
</style>

