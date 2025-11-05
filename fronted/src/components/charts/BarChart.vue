//柱状图实现
<template>
  <div class="bar-chart">
    <h3 v-if="title" class="chart-title">{{ title }}</h3>
    <p v-if="description" class="chart-description">{{ description }}</p>
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as d3 from 'd3'
import { useResizeObserver } from '@/composables/useResizeObserver.js'
import { createColorScale } from '@/utils/colorScale.js'
import '@/assets/styles/chart.css'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  xKey: {
    type: String,
    default: 'name'
  },
  yKey: {
    type: String,
    default: 'value'
  },
  color: {
    type: String,
    default: '#667eea'
  }
})

const chartContainer = ref(null)
let svg = null
let g = null
let xScale = null
let yScale = null

const { width, height } = useResizeObserver(chartContainer)

const renderChart = () => {
  if (!chartContainer.value || !props.data || props.data.length === 0) return

  const container = chartContainer.value
  const containerWidth = container.clientWidth || 800
  const containerHeight = container.clientHeight || 600

  // 清除旧图表
  d3.select(container).selectAll('*').remove()

  // 设置边距
  const margin = { top: 20, right: 30, bottom: 60, left: 60 }
  const chartWidth = containerWidth - margin.left - margin.right
  const chartHeight = containerHeight - margin.top - margin.bottom

  // 创建SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)

  g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // 创建比例尺
  xScale = d3.scaleBand()
    .domain(props.data.map(d => d[props.xKey]))
    .range([0, chartWidth])
    .padding(0.2)

  yScale = d3.scaleLinear()
    .domain([0, d3.max(props.data, d => d[props.yKey])])
    .nice()
    .range([chartHeight, 0])

  // 创建颜色比例尺
  const colorScale = createColorScale(
    props.data.map(d => d[props.yKey]),
    'category10'
  )

  // 添加X轴
  g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${chartHeight})`)
    .call(d3.axisBottom(xScale))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .attr('dx', '-.8em')
    .attr('dy', '.15em')

  // 添加Y轴
  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(yScale))

  // 添加网格线
  g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${chartHeight})`)
    .call(d3.axisBottom(xScale).tickSize(-chartHeight).tickFormat(''))

  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(yScale).tickSize(-chartWidth).tickFormat(''))

  // 添加柱状图
  g.selectAll('.bar')
    .data(props.data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', d => xScale(d[props.xKey]))
    .attr('y', d => yScale(d[props.yKey]))
    .attr('width', xScale.bandwidth())
    .attr('height', d => chartHeight - yScale(d[props.yKey]))
    .attr('fill', props.color)
    .on('mouseover', function(event, d) {
      d3.select(this).attr('fill', '#764ba2')
      
      // 显示提示框
      const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip visible')
        .style('opacity', 0)
        .html(`${d[props.xKey]}: ${d[props.yKey]}`)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px')
      
      tooltip.transition()
        .duration(200)
        .style('opacity', 1)
    })
    .on('mouseout', function() {
      d3.select(this).attr('fill', props.color)
      d3.selectAll('.tooltip').remove()
    })

  // 添加数值标签
  g.selectAll('.label')
    .data(props.data)
    .enter()
    .append('text')
    .attr('class', 'label')
    .attr('x', d => xScale(d[props.xKey]) + xScale.bandwidth() / 2)
    .attr('y', d => yScale(d[props.yKey]) - 5)
    .attr('text-anchor', 'middle')
    .text(d => d[props.yKey])
    .style('font-size', '12px')
    .style('fill', '#666')
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
})
</script>

<style scoped>
.bar-chart {
  width: 100%;
}
</style>

