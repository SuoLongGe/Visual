<template>
  <div class="fracture-chart">
    <div v-if="selectedIndustries.length !== 2" class="placeholder">
      <p>请保持选中 2 个行业以生成裂纹占比图</p>
      <p class="hint">裂纹面积越大，表示该维度差异贡献越高</p>
    </div>
    <div v-else ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Delaunay } from 'd3-delaunay'

const props = defineProps({
  selectedIndustries: {
    type: Array,
    default: () => []
  }
})

const chartContainer = ref(null)
let chartInstance = null

const dimensionConfig = [
  { key: 'avg_median_salary', name: '平均薪资', unit: 'K', min: 0, max: 200 },
  { key: 'avg_experience_rank', name: '平均经验', unit: '级', min: 0, max: 10 },
  { key: 'avg_education_rank', name: '平均学历', unit: '级', min: 0, max: 10 },
  { key: 'avg_city_tier_score', name: '平均城市等级', unit: '级', min: 1, max: 4 },
  { key: 'job_count', name: '招聘总数', unit: '个', min: 0, max: 50000, useRatio: true }
]

const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

const buildDiffPayload = (industryA, industryB) => {
  const result = {
    industryA: industryA.company_type,
    industryB: industryB.company_type,
    dimensions: [],
    totalScore: 0
  }

  dimensionConfig.forEach((config, idx) => {
    const valueA = industryA[config.key] ?? 0
    const valueB = industryB[config.key] ?? 0
    let score = 0
    let ratio = null
    let winner = 'A'
    const rawDiff = Math.abs(valueA - valueB)

    if (config.useRatio) {
      const larger = Math.max(valueA, valueB)
      const smaller = Math.max(1, Math.min(valueA, valueB))
      ratio = larger / (smaller || 1)
      score = ratio >= 10 ? 2 : ((ratio - 1) / 9) * 2
      winner = larger === valueA ? 'A' : 'B'
    } else {
      const span = Math.max(config.max - config.min, 1)
      score = Math.min(2, (rawDiff / span) * 2)
      winner = valueA >= valueB ? 'A' : 'B'
    }

    result.totalScore += score
    result.dimensions.push({
      name: config.name,
      unit: config.unit,
      valueA,
      valueB,
      score,
      ratio,
      winner,
      color: colors[idx % colors.length]
    })
  })

  return result
}

// 使用 d3-delaunay 生成 Voronoi 图

// 使用 d3-delaunay 生成 Voronoi 图，完美处理边界，确保填满容器

// 使用 d3-delaunay 生成真正的 Voronoi 图，完美填满容器
const buildOption = (diffData, width, height) => {
  const crackData = diffData.dimensions.map((dim, index) => ({
    ...dim,
    index
  }))

  const totalMax = dimensionConfig.length * 2
  const graphicElements = []

  const cx = width / 2
  const cy = height / 2

  // 根据权重分布种子点
  const totalWeight = crackData.reduce((sum, d) => sum + (d.score || 0.1), 0)
  const points = []
  const siteData = []
  const maxDist = Math.min(width, height) * 0.4

  crackData.forEach((dim, idx) => {
    const weight = Math.max(dim.score || 0.1, 0.1)
    const weightRatio = weight / totalWeight

    // 权重大的在中心附近，权重小的延伸到边缘
    const distFromCenter = maxDist * (0.15 + (1 - weightRatio) * 0.85)
    const angle = (idx * Math.PI * 2) / crackData.length

    const siteX = cx + Math.cos(angle) * distFromCenter
    const siteY = cy + Math.sin(angle) * distFromCenter

    points.push(siteX, siteY)
    siteData.push({ dim, weight })
  })

  // 使用 d3-delaunay 生成 Voronoi 图
  const delaunay = Delaunay.from(points)
  const voronoi = delaunay.voronoi([0, 0, width, height]) // 设置边界为整个容器

  // 为每个种子点生成 Voronoi cell
  // d3-delaunay 的 cellPolygon(i) 返回第 i 个 cell 的多边形顶点数组
  siteData.forEach((siteInfo, idx) => {
    const polygon = voronoi.cellPolygon(idx)
    
    if (polygon && polygon.length >= 6) { // 至少3个点（每个点2个坐标）
      // polygon 是一个 Float64Array，每两个元素是一个点的 x, y
      const points = []
      for (let i = 0; i < polygon.length; i += 2) {
        points.push([polygon[i], polygon[i + 1]])
      }
      
      // 确保闭合（d3-delaunay 通常已经闭合，但为了保险）
      if (points.length > 0) {
        const first = points[0]
        const last = points[points.length - 1]
        if (Math.abs(first[0] - last[0]) > 0.001 || Math.abs(first[1] - last[1]) > 0.001) {
          points.push([first[0], first[1]])
        }
      }

      if (points.length >= 3) {
        graphicElements.push({
          type: 'polygon',
          shape: { 
            points: points
          },
          style: {
            fill: siteInfo.dim.color || '#ccc',
            stroke: '#333',
            lineWidth: 2,
            opacity: 0.9
          },
          z: 10 - siteInfo.dim.index
        })
      }
    }
  })

  // 中央总差异度文本（cx 和 cy 已在前面声明）
  graphicElements.push(
    {
      type: 'text',
      left: cx,
      top: cy - 10,
      style: {
        text: diffData.totalScore.toFixed(2),
        fontSize: 24,
        fontWeight: 'bold',
        fill: '#000',
        textAlign: 'center',
        textVerticalAlign: 'middle'
      },
      z: 100
    },
    {
      type: 'text',
      left: cx,
      top: cy + 18,
      style: {
        text: '差异总分',
        fontSize: 12,
        fill: '#666',
        textAlign: 'center',
        textVerticalAlign: 'middle'
      },
      z: 100
    }
  )

  // 在每个种子点位置添加维度名称标签
  siteData.forEach((siteInfo, idx) => {
    const x = points[idx * 2]
    const y = points[idx * 2 + 1]
    graphicElements.push({
      type: 'text',
      left: x,
      top: y,
      style: {
        text: siteInfo.dim.name,
        fontSize: 11,
        fontWeight: 'bold',
        fill: '#000',
        textAlign: 'center',
        textVerticalAlign: 'middle',
        backgroundColor: 'rgba(255,255,255,0.7)',
        padding: [2, 4]
      },
      z: 100
    })
  })

  return {
    grid: {
      left: 0,
      right: 0,
      top: 0,
      bottom: 0
    },
    graphic: graphicElements
  }
}

const createPolygonPoints = (center, radius, sides, color) => {
  const points = []
  for (let i = 0; i < sides; i += 1) {
    const angle = (Math.PI * 2 * i) / sides
    const jitter = radius * (0.85 + hashNoise(color, i) * 0.15)
    points.push([
      center[0] + Math.cos(angle) * jitter,
      center[1] + Math.sin(angle) * jitter
    ])
  }
  return points
}

const formatValue = (value, unit) => {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  return `${value.toFixed(2)}${unit || ''}`
}

const updateChart = () => {
  if (!chartInstance || props.selectedIndustries.length !== 2) return
  const diffData = buildDiffPayload(props.selectedIndustries[0], props.selectedIndustries[1])

  try {
    const width = chartInstance.getWidth()
    const height = chartInstance.getHeight()
    chartInstance.setOption(buildOption(diffData, width, height), true)
    // 初始化完成后强制一次自适应，避免容器初次渲染尺寸变化导致只显示中心文字
    chartInstance.resize()
  } catch (e) {
    // 防御性日志，方便你在浏览器里看到具体错误信息
    // eslint-disable-next-line no-console
    console.error('FractureDifferenceChart: setOption failed', e)
  }
}

const initChart = async () => {
  // 等待 DOM 完整挂载并参与布局，避免容器宽高为 0
  await nextTick()
  if (!chartContainer.value) return

  const dom = chartContainer.value

  // 如果初次挂载时仍然没有尺寸，延迟一帧再尝试一次
  if (!dom.offsetWidth || !dom.offsetHeight) {
    await nextTick()
  }

  if (!dom.offsetWidth || !dom.offsetHeight) {
    console.warn('FractureDifferenceChart: chartContainer has no size, skip init this tick')
    return
  }

  chartInstance = echarts.init(dom)

  // 开发环境下把实例挂到 window 上，方便在浏览器控制台调试：
  // 在控制台里输入 __fractureChart.getOption() 就能看到完整配置
  if (import.meta && import.meta.env && import.meta.env.DEV) {
    // eslint-disable-next-line no-underscore-dangle
    window.__fractureChart = chartInstance
  }

  window.addEventListener('resize', handleResize)
  updateChart()
}

const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
    // 尺寸变化后重算图形，保持自适应
    updateChart()
  }
}

watch(
  () => props.selectedIndustries,
  async (val) => {
    await nextTick()
    if (val.length === 2) {
      if (!chartInstance) {
        await initChart()
      } else {
        updateChart()
      }
    } else if (chartInstance) {
      // 清空旧图形，防止残影
      chartInstance.clear()
    }
  },
  { deep: true }
)

onMounted(async () => {
  if (props.selectedIndustries.length === 2) {
    await initChart()
  }
})

onUnmounted(() => {
  disposeChart()
})
</script>

<style scoped>
.fracture-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 260px;
}

.placeholder {
  text-align: center;
  color: #777;
  padding: 40px 20px;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: #aaa;
}
</style>

