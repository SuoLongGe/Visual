<template>
  <div class="industry-diff-bar">
    <div v-if="selectedIndustries.length === 0" class="placeholder">
      <p>请选择 1-2 个行业查看指标</p>
      <p class="hint">在左侧行业散点图中点击气泡加载数据</p>
    </div>
    <div v-else ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  selectedIndustries: {
    type: Array,
    default: () => []
  }
})

const chartContainer = ref(null)
let chartInstance = null

const dimensionConfig = [
  { key: 'job_count', name: '招聘总数', unit: '个', formatter: (v) => formatLargeNumber(v) },
  { key: 'avg_median_salary', name: '平均中位薪资', unit: 'K', formatter: (v) => `${(v || 0).toFixed(1)}` },
  { key: 'avg_experience_rank', name: '平均经验', unit: '级', formatter: (v) => `${(v || 0).toFixed(2)}` },
  { key: 'avg_education_rank', name: '平均学历', unit: '级', formatter: (v) => `${(v || 0).toFixed(2)}` },
  { key: 'avg_city_tier_score', name: '平均城市评级', unit: '级', formatter: (v) => `${(v || 0).toFixed(2)}` }
]

const formatLargeNumber = (value) => {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(1)}万`
  }
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(1)}千`
  }
  return value.toFixed(0)
}

const buildOption = (industries) => {
  const hasSecond = industries.length > 1
  const first = industries[0]
  const second = industries[1]

  const categories = dimensionConfig.map(dim => dim.name)

  // 为每个维度单独归一化，行业A向左、行业B向右
  const seriesDataLeft = []
  const seriesDataRight = []

  dimensionConfig.forEach((dim, index) => {
    const rawA = Number(first?.[dim.key] ?? 0)
    const rawB = hasSecond ? Number(second?.[dim.key] ?? 0) : 0
    const maxAbs = Math.max(Math.abs(rawA), Math.abs(rawB), 1e-6)


    const normA = (rawA / maxAbs) * 1.5
    const normB = (rawB / maxAbs) * 1.5

    seriesDataLeft.push({
      value: -normA,         // 向左
      dimIndex: index,
      raw: rawA
    })

    seriesDataRight.push({
      value: normB,          // 向右
      dimIndex: index,
      raw: rawB
    })
  })

  return {
    title: {
      text: hasSecond
        ? `${first.company_type} vs ${second.company_type}`
        : `${first.company_type} 指标对照`,
      left: 'center',
      top: 5,
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold'
      },
      subtext: hasSecond ? '展示两个行业在五个核心指标上的真实数值对比' : '当前仅显示一个行业，可继续选择进行对比',
      subtextStyle: {
        fontSize: 12,
        color: '#666'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const lines = params.map(p => {
          const dim = dimensionConfig[p.data.dimIndex]
          const unit = dim.unit || ''
          const fmt = dim.formatter
          const raw = typeof p.data.raw === 'number' ? p.data.raw : Number(p.data.raw || 0)
          const text = fmt ? fmt(raw) : `${raw}${unit}`
          return `${p.marker} ${p.seriesName}: ${text}${unit && !text.includes(unit) ? unit : ''}`
        })
        return `${params[0].axisValue}<br/>${lines.join('<br/>')}`
      }
    },
    grid: {
      top: 60,
      bottom: 20,
      left: 30,   // 留更多空间给左侧文字
      right: 30,  // 留更多空间给右侧文字
      containLabel: true
    },
    xAxis: {
      type: 'value',
      min: -1.5,  // 略微放大左右范围，让柱更长
      max: 1.5,
      axisLine: { lineStyle: { color: '#999' } },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e0e0e0' }
      },
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: '#333',
        fontSize: 12,
        margin: 36   // 增大文字到柱之间的垂直间距，避免重叠
      }
    },
    series: [
      {
        name: first.company_type,
        type: 'bar',
        data: seriesDataLeft,
        itemStyle: {
          color: '#5470c6'
        },
        barWidth: 18,
        label: {
          show: true,
          position: 'left',
          formatter: (p) => {
            const dim = dimensionConfig[p.data.dimIndex]
            const unit = dim.unit || ''
            const fmt = dim.formatter
            const raw = typeof p.data.raw === 'number' ? p.data.raw : Number(p.data.raw || 0)
            const text = fmt ? fmt(raw) : `${raw}${unit}`
            return text
          }
        }
      },
      hasSecond && {
        name: second.company_type,
        type: 'bar',
        data: seriesDataRight,
        itemStyle: {
          color: '#ee6666'
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p) => {
            const dim = dimensionConfig[p.data.dimIndex]
            const unit = dim.unit || ''
            const fmt = dim.formatter
            const raw = typeof p.data.raw === 'number' ? p.data.raw : Number(p.data.raw || 0)
            const text = fmt ? fmt(raw) : `${raw}${unit}`
            return text
          }
        }
      }
    ],
    barGap: '-100%',
    barCategoryGap: '40%',
    barWidth: '40%',
    barGap: '-100%',
    barCategoryGap: '40%',
    barWidth: '40%',
    barGap: '-100%',
    barCategoryGap: '40%',
    barWidth: '40%',
  }
}

const updateChart = () => {
  if (!chartInstance || props.selectedIndustries.length === 0) return
  const option = buildOption(props.selectedIndustries)
  chartInstance.setOption(option, true)
}

const initChart = async () => {
  console.log('container size:', chartContainer.value?.offsetWidth, chartContainer.value?.offsetHeight)
  await nextTick()
  await nextTick() // 必须两次

  if (!chartContainer.value) return

  const dom = chartContainer.value
  if (!dom.offsetWidth || !dom.offsetHeight) {
    console.warn('chartContainer has no size')
  }

  disposeChart()

  chartInstance = echarts.init(dom)
  window.addEventListener('resize', handleResize)

  updateChart()
  chartInstance.resize()
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
  }
}

watch(() => props.selectedIndustries, async (newVal) => {
  await nextTick()
  if (newVal.length === 0) {
    // 清空选择时直接销毁图表实例，避免旧实例绑定到已被卸载的 DOM
    disposeChart()
    return
  }

  if (!chartInstance) {
    initChart()
  } else {
    updateChart()
  }
}, { deep: true })

onMounted(() => {
  if (props.selectedIndustries.length > 0) {
    initChart()
  }
})

onUnmounted(() => {
  disposeChart()
})
</script>

<style scoped>
.industry-diff-bar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  flex: 1;
  width: 100%;
  height: calc(100% - 10px);
  min-height: 300px;
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