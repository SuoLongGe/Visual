<template>
  <div class="parallel-coordinates-chart">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error-message">错误: {{ error }}</div>
    <div v-if="!loading && !error && !hasData && data" class="error-message">
      数据格式不正确，请检查控制台日志。当前数据: {{ JSON.stringify(data) }}
    </div>
    <div v-if="!loading && !error && !data" class="error-message">
      暂无数据
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <div class="chart-controls">
        <div class="control-group">
          <label>线条颜色：</label>
          <select v-model="colorBy" @change="updateChart">
            <option value="salary">平均薪资</option>
            <option value="entropy">岗位多样性（香农熵）</option>
            <option value="job_count">岗位数量</option>
          </select>
        </div>
        <div class="control-group">
          <label>线条透明度：</label>
          <input 
            type="range" 
            v-model.number="lineOpacity" 
            min="0.1" 
            max="1" 
            step="0.1"
            @input="updateChart"
          />
          <span>{{ lineOpacity.toFixed(1) }}</span>
        </div>
        <div class="control-group">
          <label>显示方式：</label>
          <select v-model="displayMode" @change="updateChart">
            <option value="all">显示全部</option>
            <option value="top100">显示前100条</option>
            <option value="top50">显示前50条</option>
          </select>
        </div>
      </div>
      
      <div ref="chartContainer" class="chart-container"></div>
      
      <div class="legend-section">
        <div class="legend-item">
          <span class="legend-label">线条颜色：</span>
          <span class="legend-value">{{ colorByLabel }}</span>
        </div>
        <div class="legend-item">
          <span class="legend-label">线条数量：</span>
          <span class="legend-value">{{ displayedCount }} 条</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
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

const chartContainer = ref(null)
const hasData = ref(false)
const colorBy = ref('salary')
const lineOpacity = ref(0.3)
const displayMode = ref('top100')
let svg = null
let g = null
let tooltip = null
let dimensions = []
let yScales = {}
let displayedCount = ref(0)

const colorByLabel = ref('平均薪资')

watch(colorBy, () => {
  colorByLabel.value = colorBy.value === 'salary' ? '平均薪资' : 
                      colorBy.value === 'entropy' ? '岗位多样性（香农熵）' : '岗位数量'
  updateChart()
})

// 监听数据变化
watch(() => props.data, (newData) => {
  console.log('ParallelCoordinatesChart 收到数据:', newData)
  
  let actualData = newData
  if (newData && newData.code && newData.data) {
    actualData = newData.data
  }
  
  // 检查数据格式：新格式是 { data: [...] }，旧格式是 { experiences, data: [...] }
  if (actualData && (actualData.data || (actualData.experiences && actualData.data))) {
    hasData.value = true
    nextTick(() => {
      setTimeout(() => {
        renderChart(actualData)
      }, 100)
    })
  } else {
    hasData.value = false
  }
}, { immediate: true, deep: true })

const updateChart = () => {
  if (hasData.value && props.data) {
    let actualData = props.data
    if (actualData && actualData.code && actualData.data) {
      actualData = actualData.data
    }
    if (actualData) {
      renderChart(actualData)
    }
  }
}

const renderChart = (data) => {
  if (!chartContainer.value || !data) return

  const container = chartContainer.value
  const containerWidth = container.clientWidth || 1200
  const containerHeight = Math.max(600, container.clientHeight || 600)

  // 清除旧图表
  d3.select(container).selectAll('*').remove()

  // 准备平行坐标图数据
  // 检查数据格式：如果是新的平行坐标图数据格式（扁平数组）
  let flatData = []
  if (Array.isArray(data.data) && data.data.length > 0 && data.data[0].city && data.data[0].experience) {
    // 新格式：直接使用扁平数据（包含所有维度）
    flatData = data.data
  } else if (data.experiences && Array.isArray(data.data)) {
    // 旧格式：将嵌套数据转换为扁平数组
    const experienceData = data.data || []
    experienceData.forEach(expData => {
      expData.cities.forEach(city => {
        flatData.push({
          city: city.city,
          experience: expData.experience,
          education: '未知', // 当前数据中没有教育信息，使用默认值
          salary: city.avg_salary,
          entropy: city.shannon_entropy,
          company_type: '未知', // 当前数据中没有公司类型信息，使用默认值
          job_count: city.job_count
        })
      })
    })
  }

  if (flatData.length === 0) {
    return
  }

  // 定义维度（轴）
  dimensions = [
    { name: 'city', type: 'categorical', accessor: d => d.city },
    { name: 'experience', type: 'categorical', accessor: d => d.experience },
    { name: 'education', type: 'categorical', accessor: d => d.education },
    { name: 'salary', type: 'numeric', accessor: d => d.salary },
    { name: 'entropy', type: 'numeric', accessor: d => d.entropy },
    { name: 'company_type', type: 'categorical', accessor: d => d.company_type }
  ]

  // 设置边距
  const margin = { top: 40, right: 30, bottom: 40, left: 30 }
  const width = containerWidth - margin.left - margin.right
  const height = containerHeight - margin.top - margin.bottom

  // 根据显示模式筛选数据（用于绘制线条）
  let displayData = flatData
  if (displayMode.value === 'top100') {
    displayData = flatData.slice(0, 100)
  } else if (displayMode.value === 'top50') {
    displayData = flatData.slice(0, 50)
  }
  displayedCount.value = displayData.length

  // 计算每个轴的X位置
  const xScale = d3.scalePoint()
    .domain(dimensions.map(d => d.name))
    .range([0, width])
    .padding(0.1)

  // 为每个维度创建Y轴比例尺 - 只使用显示数据中实际存在的值
  dimensions.forEach(dim => {
    if (dim.type === 'numeric') {
      // 数值型：从显示数据中获取范围
      const values = displayData.map(dim.accessor)
      const min = d3.min(values)
      const max = d3.max(values)
      yScales[dim.name] = d3.scaleLinear()
        .domain([min * 0.95, max * 1.05])
        .range([height, 0])
        .nice()
    } else {
      // 分类数据：只从显示数据中收集唯一值，只显示实际有数据线穿过的值
      const allValues = [...new Set(displayData.map(dim.accessor))]
      // 对于经验和学历，按逻辑顺序排序
      if (dim.name === 'experience') {
        // 经验等级排序：从低到高（根据映射表实际值）
        const experienceOrder = [
          '无经验', '1年以下', '应届毕业生', '1-3年', '3-5年', 
          '5-7年', '7-10年', '10年以上', '未知'
        ]
        allValues.sort((a, b) => {
          const aIdx = experienceOrder.indexOf(a)
          const bIdx = experienceOrder.indexOf(b)
          if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx
          if (aIdx !== -1) return -1
          if (bIdx !== -1) return 1
          return a.localeCompare(b)
        })
      } else if (dim.name === 'education') {
        // 学历等级排序：从低到高（根据映射表实际值）
        const educationOrder = [
          '小学以下', '小学', '初中', '高中/中专', '大专', 
          '本科', '硕士', '博士', '博士后', '未知'
        ]
        allValues.sort((a, b) => {
          const aIdx = educationOrder.indexOf(a)
          const bIdx = educationOrder.indexOf(b)
          if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx
          if (aIdx !== -1) return -1
          if (bIdx !== -1) return 1
          return a.localeCompare(b)
        })
      } else {
        // 其他分类数据按字母顺序排序
        allValues.sort()
      }
      
      yScales[dim.name] = d3.scalePoint()
        .domain(allValues)
        .range([height, 0])
        .padding(0.3)  // 减少padding，让标签更密集
    }
  })

  // 创建颜色比例尺（基于所有数据）
  let minColor = Infinity
  let maxColor = -Infinity
  flatData.forEach(d => {
    let value
    if (colorBy.value === 'salary') {
      value = d.salary
    } else if (colorBy.value === 'entropy') {
      value = d.entropy
    } else {
      value = d.job_count
    }
    minColor = Math.min(minColor, value)
    maxColor = Math.max(maxColor, value)
  })

  if (minColor === Infinity) {
    minColor = 0
    maxColor = 100
  }

  const colorScale = d3.scaleSequential(d3.interpolateViridis)
    .domain([maxColor, minColor])

  // 创建SVG
  svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', containerHeight)
    .style('display', 'block')

  g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // 绘制背景网格
  dimensions.forEach(dim => {
    const x = xScale(dim.name)
    
    if (dim.type === 'numeric') {
      const ticks = yScales[dim.name].ticks(5)
      ticks.forEach(tick => {
        g.append('line')
          .attr('x1', x)
          .attr('x2', x)
          .attr('y1', yScales[dim.name](tick))
          .attr('y2', yScales[dim.name](tick))
          .attr('stroke', '#e0e0e0')
          .attr('stroke-width', 0.5)
          .attr('stroke-dasharray', '2,2')
      })
    } else {
      const values = yScales[dim.name].domain()
      values.forEach(value => {
        g.append('line')
          .attr('x1', x)
          .attr('x2', x)
          .attr('y1', yScales[dim.name](value))
          .attr('y2', yScales[dim.name](value))
          .attr('stroke', '#e0e0e0')
          .attr('stroke-width', 0.5)
          .attr('stroke-dasharray', '2,2')
      })
    }
  })

  // 绘制轴
  dimensions.forEach(dim => {
    const x = xScale(dim.name)
    
    // 绘制轴线
    g.append('line')
      .attr('x1', x)
      .attr('x2', x)
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', '#333')
      .attr('stroke-width', 2)

    // 绘制轴标签
    g.append('text')
      .attr('x', x)
      .attr('y', -10)
      .attr('text-anchor', 'middle')
      .attr('font-size', '13px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(dim.name === 'city' ? '城市' :
            dim.name === 'experience' ? '经验要求' :
            dim.name === 'education' ? '学历要求' :
            dim.name === 'salary' ? '平均薪资' :
            dim.name === 'entropy' ? '岗位多样性' :
            '公司类型')

    // 绘制刻度标签
    if (dim.type === 'numeric') {
      const ticks = yScales[dim.name].ticks(5)
      ticks.forEach(tick => {
        g.append('text')
          .attr('x', x)
          .attr('y', yScales[dim.name](tick))
          .attr('dx', -8)
          .attr('text-anchor', 'end')
          .attr('font-size', '10px')
          .attr('fill', '#666')
          .text(dim.name === 'salary' ? tick.toFixed(0) + 'K' : tick.toFixed(2))
      })
    } else {
      // 分类数据：显示所有标签，但根据数量调整字体大小和旋转
      const values = yScales[dim.name].domain()
      const fontSize = values.length > 20 ? '8px' : values.length > 10 ? '9px' : '10px'
      
      values.forEach((value, i) => {
        const yPos = yScales[dim.name](value)
        const text = g.append('text')
          .attr('x', x)
          .attr('y', yPos)
          .attr('dx', -8)
          .attr('text-anchor', 'end')
          .attr('font-size', fontSize)
          .attr('fill', '#666')
          .text(value.length > 15 ? value.substring(0, 15) + '...' : value)
        
        // 如果标签太多，旋转45度避免重叠
        if (values.length > 15) {
          text.attr('transform', `rotate(-45 ${x - 8} ${yPos})`)
            .attr('text-anchor', 'end')
            .attr('dx', -5)
        }
      })
    }
  })

  // 绘制线条
  const line = d3.line()
    .x((d, i) => xScale(dimensions[i].name))
    .y((d, i) => {
      const dim = dimensions[i]
      const value = dim.accessor(d.data)
      return yScales[dim.name](value)
    })
    .curve(d3.curveMonotoneX)

  const paths = g.selectAll('.line')
    .data(displayData)
    .enter()
    .append('path')
    .attr('class', 'line')
    .attr('d', d => line(dimensions.map(() => ({ data: d }))))
    .attr('fill', 'none')
    .attr('stroke', d => {
      let value
      if (colorBy.value === 'salary') {
        value = d.salary
      } else if (colorBy.value === 'entropy') {
        value = d.entropy
      } else {
        value = d.job_count
      }
      return colorScale(value)
    })
    .attr('stroke-width', 1.5)
    .attr('opacity', lineOpacity.value)
    .on('mouseover', function(event, d) {
      d3.select(this)
        .attr('opacity', 1)
        .attr('stroke-width', 3)

      showTooltip(event, d)
    })
    .on('mouseout', function() {
      d3.select(this)
        .attr('opacity', lineOpacity.value)
        .attr('stroke-width', 1.5)

      hideTooltip()
    })
}

const showTooltip = (event, d) => {
  tooltip = d3.select('body')
    .append('div')
    .attr('class', 'parallel-coordinates-tooltip')
    .style('opacity', 0)
    .style('position', 'absolute')
    .style('background', 'rgba(0, 0, 0, 0.9)')
    .style('color', '#fff')
    .style('padding', '12px')
    .style('border-radius', '6px')
    .style('pointer-events', 'none')
    .style('font-size', '12px')
    .style('z-index', 1000)
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.3)')

  tooltip.html(`
    <div style="font-weight: bold; margin-bottom: 6px; font-size: 14px;">数据详情</div>
    <div style="margin-bottom: 4px;">城市: <strong>${d.city}</strong></div>
    <div style="margin-bottom: 4px;">经验要求: <strong>${d.experience}</strong></div>
    <div style="margin-bottom: 4px;">学历要求: <strong>${d.education}</strong></div>
    <div style="margin-bottom: 4px;">平均薪资: <strong>${d.salary.toFixed(2)}K</strong></div>
    <div style="margin-bottom: 4px;">岗位多样性(熵): <strong>${d.entropy.toFixed(4)}</strong></div>
    <div style="margin-bottom: 4px;">公司类型: <strong>${d.company_type}</strong></div>
    <div>岗位数量: <strong>${d.job_count.toLocaleString()}</strong></div>
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
  if (chartContainer.value) {
    d3.select(chartContainer.value).selectAll('*').remove()
  }
  hideTooltip()
})
</script>

<style scoped>
.parallel-coordinates-chart {
  width: 100%;
  min-height: 600px;
}

.chart-wrapper {
  width: 100%;
}

.chart-controls {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
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
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.control-group select:hover {
  border-color: #5470c6;
}

.control-group input[type="range"] {
  width: 100px;
}

.control-group span {
  font-size: 12px;
  color: #666;
  min-width: 30px;
}

.chart-container {
  width: 100%;
  min-height: 600px;
  overflow: visible;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #fafafa;
}

.legend-section {
  display: flex;
  gap: 30px;
  margin-top: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
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
</style>
