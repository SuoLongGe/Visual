<template>
  <div class="continuous-progress-bar-chart">
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
    default: 'Math-Based 多维进度条图（连续型）'
  },
  description: {
    type: String,
    default: '展示职位在数量、学历、经验等维度的连续型综合排名'
  }
})

const chartContainer = ref(null)
let svg = null
let g = null
let xScale = null
let yScale = null

const { width, height } = useResizeObserver(chartContainer)

// 定义三种进度条的颜色（科技感配色：霓虹蓝、青色、紫色）
const barConfigs = [
  { 
    key: 'records_count_norm', 
    color: '#00D9FF',  // 霓虹青色
    glowColor: '#00FFFF',  // 发光色
    gradientId: 'gradient-cyan'
  },
  { 
    key: 'education_rank', 
    color: '#0080FF',  // 电光蓝
    glowColor: '#00BFFF',  // 发光色
    gradientId: 'gradient-blue'
  },
  { 
    key: 'experience_rank', 
    color: '#7B2CBF',  // 霓虹紫
    glowColor: '#9D4EDD',  // 发光色
    gradientId: 'gradient-purple'
  }
]

const renderChart = () => {
  if (!chartContainer.value || !props.data || props.data.length === 0) return

  const container = chartContainer.value
  const containerWidth = container.clientWidth || 1000
  const containerHeight = container.clientHeight || 600

  // 清除旧图表
  d3.select(container).selectAll('*').remove()

  // 设置边距
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

  // 创建渐变定义
  const defs = svg.append('defs')
  
  barConfigs.forEach(config => {
    // 创建线性渐变（从左到右，科技感渐变）
    const gradient = defs.append('linearGradient')
      .attr('id', config.gradientId)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', config.glowColor || config.color)
      .attr('stop-opacity', 1)
    
    gradient.append('stop')
      .attr('offset', '50%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 1)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', d3.rgb(config.color).darker(0.5))
      .attr('stop-opacity', 0.9)
    
    // 创建激光效果渐变（在进度条右侧，增强科技感）
    const laserGradient = defs.append('linearGradient')
      .attr('id', `${config.gradientId}-laser`)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%')
    
    laserGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', config.glowColor || config.color)
      .attr('stop-opacity', 1)
    
    laserGradient.append('stop')
      .attr('offset', '30%')
      .attr('stop-color', '#FFFFFF')
      .attr('stop-opacity', 1)
    
    laserGradient.append('stop')
      .attr('offset', '70%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0.8)
    
    laserGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0)
    
    // 创建激光光晕效果（增强科技感）
    const laserGlow = defs.append('radialGradient')
      .attr('id', `${config.gradientId}-glow`)
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%')
    
    laserGlow.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#FFFFFF')
      .attr('stop-opacity', 1)
    
    laserGlow.append('stop')
      .attr('offset', '40%')
      .attr('stop-color', config.glowColor || config.color)
      .attr('stop-opacity', 0.9)
    
    laserGlow.append('stop')
      .attr('offset', '70%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0.7)
    
    laserGlow.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0)
    
    // 创建高光渐变（从上到下，用于进度条内部高光）
    const highlightGradient = defs.append('linearGradient')
      .attr('id', `${config.gradientId}-highlight`)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')
    
    highlightGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', config.glowColor || config.color)
      .attr('stop-opacity', 0.6)
    
    highlightGradient.append('stop')
      .attr('offset', '50%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0.3)
    
    highlightGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', config.color)
      .attr('stop-opacity', 0)
  })

  // 创建X轴比例尺（0-1的归一化值）
  xScale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, chartWidth])

  // 创建Y轴比例尺（职位名称）
  yScale = d3.scaleBand()
    .domain(props.data.map(d => d.job_title))
    .range([0, chartHeight])
    .padding(0.3)

  // 每个职位的高度
  const jobHeight = yScale.bandwidth()
  const barHeight = jobHeight * 0.25  // 每条进度条的高度
  const barSpacing = jobHeight * 0.05  // 进度条之间的间距

  // 添加X轴
  const xAxis = d3.axisBottom(xScale)
    .tickValues([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    .tickFormat(d3.format('.1f'))
  
  const xAxisGroup = g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${chartHeight})`)
    .call(xAxis)
  
  // 更新X轴样式（科技感）
  xAxisGroup.selectAll('path')
    .attr('stroke', '#00D9FF')
    .attr('stroke-width', 1.5)
    .style('filter', 'drop-shadow(0 0 2px #00D9FF)')
  
  xAxisGroup.selectAll('line')
    .attr('stroke', '#00D9FF')
    .attr('stroke-width', 1)
    .style('filter', 'drop-shadow(0 0 1px #00D9FF)')
  
  xAxisGroup.selectAll('text')
    .attr('fill', '#D4AF37')
    .attr('font-size', '11px')
    .attr('font-weight', '500')
  
  // 添加X轴标签
  g.append('text')
    .attr('class', 'axis-label')
    .attr('x', chartWidth / 2)
    .attr('y', chartHeight + 50)
    .attr('fill', '#D4AF37')
    .attr('font-size', '13px')
    .attr('font-weight', '500')
    .attr('text-anchor', 'middle')
    .text('归一化值')

  // 添加Y轴
  const yAxisGroup = g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(yScale))
  
  // 更新Y轴样式（科技感）
  yAxisGroup.selectAll('path')
    .attr('stroke', '#00D9FF')
    .attr('stroke-width', 1.5)
    .style('filter', 'drop-shadow(0 0 2px #00D9FF)')
  
  yAxisGroup.selectAll('line')
    .attr('stroke', '#00D9FF')
    .attr('stroke-width', 1)
    .style('filter', 'drop-shadow(0 0 1px #00D9FF)')
  
  yAxisGroup.selectAll('text')
    .style('font-size', '12px')
    .style('fill', '#D4AF37')
    .style('font-weight', '500')

  // 添加网格线
  const gridLines = g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${chartHeight})`)
  
  xScale.ticks(5).forEach(tick => {
    gridLines.append('line')
      .attr('class', 'grid-line')
      .attr('x1', xScale(tick))
      .attr('x2', xScale(tick))
      .attr('y1', 0)
      .attr('y2', -chartHeight)
      .attr('stroke', '#2a3a4a')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0.6)
  })

  // 为每个职位绘制三条进度条
  props.data.forEach((job, jobIndex) => {
    const yPos = yScale(job.job_title)
    const centerY = yPos + jobHeight / 2
    
    barConfigs.forEach((config, barIndex) => {
      const value = Math.max(0, Math.min(1, job[config.key] || 0))  // 确保值在0-1之间
      const progressWidth = xScale(value)
      
      // 计算每条进度条的Y位置（三条进度条垂直居中排列）
      const totalBarsHeight = barHeight * 3 + barSpacing * 2
      const startY = centerY - totalBarsHeight / 2
      const barY = startY + barIndex * (barHeight + barSpacing)
      
      // 绘制进度条背景（深色科技感）
      g.append('rect')
        .attr('class', `bar-bg bar-${config.key}`)
        .attr('x', 0)
        .attr('y', barY)
        .attr('width', chartWidth)
        .attr('height', barHeight)
        .attr('fill', '#0a0a1a')
        .attr('rx', 2)
        .attr('opacity', 0.4)
        .attr('stroke', '#1a1a2e')
        .attr('stroke-width', 1)
        .style('filter', `drop-shadow(0 0 2px ${config.color}40)`)

      // 创建进度条组
      const progressGroup = g.append('g')
        .attr('class', `progress-bar progress-${config.key}`)
        .attr('data-job', job.job_title)
        .attr('data-type', config.key)
        .attr('data-value', value)

      // 绘制进度条主体（带渐变）
      const progressBar = progressGroup.append('rect')
        .attr('class', 'progress-fill')
        .attr('x', 0)
        .attr('y', barY)
        .attr('width', 0)  // 初始宽度为0，用于动画
        .attr('height', barHeight)
        .attr('fill', `url(#${config.gradientId})`)
        .attr('rx', 2)
        .attr('opacity', 0.9)

      // 添加进度条内部高光效果（科技感）
      progressGroup.append('rect')
        .attr('class', 'progress-highlight')
        .attr('x', 0)
        .attr('y', barY)
        .attr('width', 0)
        .attr('height', barHeight * 0.4)
        .attr('fill', `url(#${config.gradientId}-highlight)`)
        .attr('rx', 2)
        .style('opacity', 0.8)

      // 添加进度条边框（发光效果，增强科技感）
      progressGroup.append('rect')
        .attr('class', 'progress-border')
        .attr('x', 0)
        .attr('y', barY)
        .attr('width', 0)
        .attr('height', barHeight)
        .attr('fill', 'none')
        .attr('stroke', config.glowColor || config.color)
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.8)
        .attr('rx', 2)
        .style('filter', `drop-shadow(0 0 4px ${config.glowColor || config.color}) drop-shadow(0 0 8px ${config.color}60)`)

      // 激光效果组（在进度条右侧）
      const laserGroup = progressGroup.append('g')
        .attr('class', 'laser-effect')
        .attr('opacity', 0)

      // 激光主体（垂直条）
      laserGroup.append('rect')
        .attr('class', 'laser-bar')
        .attr('x', 0)
        .attr('y', barY - 2)
        .attr('width', 8)
        .attr('height', barHeight + 4)
        .attr('fill', `url(#${config.gradientId}-laser)`)
        .attr('rx', 4)

      // 激光光晕（圆形）
      laserGroup.append('circle')
        .attr('class', 'laser-glow')
        .attr('cx', 4)
        .attr('cy', barY + barHeight / 2)
        .attr('r', barHeight / 2 + 2)
        .attr('fill', `url(#${config.gradientId}-glow)`)
        .style('filter', 'blur(2px)')

      // 激光粒子效果（多个小点）
      for (let i = 0; i < 5; i++) {
        laserGroup.append('circle')
          .attr('class', 'laser-particle')
          .attr('cx', 4)
          .attr('cy', barY + (barHeight / 6) * (i + 1))
          .attr('r', 1.5)
          .attr('fill', '#FFFFFF')
          .attr('opacity', 0.8)
      }

      // 动画：进度条填充
      progressBar
        .transition()
        .duration(1000)
        .delay(barIndex * 100)
        .ease(d3.easeCubicOut)
        .attr('width', progressWidth)

      // 动画：高光效果
      progressGroup.select('.progress-highlight')
        .transition()
        .duration(1000)
        .delay(barIndex * 100)
        .ease(d3.easeCubicOut)
        .attr('width', progressWidth)

      // 动画：边框
      progressGroup.select('.progress-border')
        .transition()
        .duration(1000)
        .delay(barIndex * 100)
        .ease(d3.easeCubicOut)
        .attr('width', progressWidth)

      // 动画：激光效果（在进度条填充完成后显示）
      laserGroup
        .attr('transform', `translate(${progressWidth}, 0)`)
        .transition()
        .duration(300)
        .delay(1000 + barIndex * 100)
        .ease(d3.easeCubicOut)
        .attr('opacity', 1)

      // 激光动画（持续闪烁）
      laserGroup.selectAll('.laser-particle')
        .transition()
        .duration(500)
        .delay(1300 + barIndex * 100)
        .attr('opacity', 0.3)
        .transition()
        .duration(500)
        .attr('opacity', 0.9)
        .on('end', function repeat() {
          d3.select(this)
            .transition()
            .duration(500)
            .attr('opacity', 0.3)
            .transition()
            .duration(500)
            .attr('opacity', 0.9)
            .on('end', repeat)
        })

      // 添加交互：鼠标悬浮
      progressGroup
        .on('mouseover', function(event) {
          const rect = d3.select(this).select('.progress-fill')
          const border = d3.select(this).select('.progress-border')
          const laser = d3.select(this).select('.laser-effect')
          
          rect
            .transition()
            .duration(200)
            .attr('opacity', 1)
            .style('filter', 'brightness(1.2)')
          
          border
            .transition()
            .duration(200)
            .attr('stroke-opacity', 1)
            .style('filter', `drop-shadow(0 0 8px ${config.glowColor || config.color}) drop-shadow(0 0 12px ${config.color}80)`)
          
          laser
            .transition()
            .duration(200)
            .attr('opacity', 1.2)

          // 显示提示框
          const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip visible')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.9)')
            .style('color', 'white')
            .style('padding', '12px')
            .style('border-radius', '6px')
            .style('pointer-events', 'none')
            .style('font-size', '13px')
            .style('z-index', '1000')
            .style('box-shadow', '0 2px 8px rgba(0,0,0,0.3)')
            .style('border', `1px solid ${config.glowColor || config.color}`)
            .style('box-shadow', `0 0 10px ${config.color}40, 0 2px 8px rgba(0,0,0,0.5)`)
            .html(`
              <div style="font-weight: 600; margin-bottom: 6px; color: ${config.glowColor || config.color}; text-shadow: 0 0 4px ${config.glowColor || config.color};">${job.job_title}</div>
              <div style="margin-bottom: 4px;">数值: ${d3.format('.3f')(value)}</div>
              <div style="margin-bottom: 4px;">进度: ${d3.format('.1%')(value)}</div>
              <div style="color: #aaa; font-size: 11px;">综合得分: ${d3.format('.3f')(job.composite_score || 0)}</div>
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')

          tooltip.transition()
            .duration(200)
            .style('opacity', 1)
        })
        .on('mouseout', function() {
          const rect = d3.select(this).select('.progress-fill')
          const border = d3.select(this).select('.progress-border')
          const laser = d3.select(this).select('.laser-effect')
          
          rect
            .transition()
            .duration(200)
            .attr('opacity', 0.9)
            .style('filter', 'brightness(1)')
          
          border
            .transition()
            .duration(200)
            .attr('stroke-opacity', 0.8)
            .style('filter', `drop-shadow(0 0 4px ${config.glowColor || config.color}) drop-shadow(0 0 8px ${config.color}60)`)
          
          laser
            .transition()
            .duration(200)
            .attr('opacity', 1)

          d3.selectAll('.tooltip').remove()
        })

      // 添加数值标签（在进度条右侧，科技感发光文字）
      g.append('text')
        .attr('class', 'bar-label')
        .attr('x', progressWidth + 15)
        .attr('y', barY + barHeight / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'start')
        .attr('fill', '#D4AF37')
        .attr('font-size', '12px')
        .attr('font-weight', '600')
        .attr('opacity', 0)
        .text(d3.format('.3f')(value))
        .transition()
        .duration(1000)
        .delay(barIndex * 100)
        .attr('opacity', 1)
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
.continuous-progress-bar-chart {
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

/* 进度条动画效果 */
:deep(.progress-fill) {
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.laser-effect) {
  animation: laser-pulse 2s ease-in-out infinite;
}

@keyframes laser-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>

