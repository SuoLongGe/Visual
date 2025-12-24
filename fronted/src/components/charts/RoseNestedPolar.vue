<template>
  <div class="rose-nested-polar">
    <h3 v-if="title" class="chart-title">{{ title }}</h3>
    <p v-if="description" class="chart-description">{{ description }}</p>
    <div ref="chartRef" class="chart-container"></div>
    <div class="zoom-controls">
      <button class="zoom-btn" @click.stop.prevent="onZoomInClick" aria-label="放大">＋</button>
      <button class="zoom-btn" @click.stop.prevent="onZoomOutClick" aria-label="缩小">－</button>
    </div>
    <!-- 行业大热按钮已移除；初始加载显示 Top2 热门卡片 -->
    <div v-if="showHotCards && topTwo.length" class="hot-cards">
      <div class="hot-card left" v-if="topTwo[0]">
        <div class="hot-card-title">{{ displayName(topTwo[0]) }}</div>
        <div class="hot-card-row"><span>company_type</span><b>{{ safe(topTwo[0].company_type) }}</b></div>
        <div class="hot-card-row"><span>national_job_count</span><b>{{ formatNum(topTwo[0].national_job_count) }}</b></div>
        <div class="hot-card-row"><span>avg_median_salary</span><b>{{ formatNum(topTwo[0].avg_median_salary) }}</b></div>
        <div class="hot-card-row"><span>avg_experience_rank</span><b>{{ formatFloat(topTwo[0].avg_experience_rank) }}</b></div>
        <div class="hot-card-row"><span>avg_education_rank</span><b>{{ formatFloat(topTwo[0].avg_education_rank) }}</b></div>
      </div>
      <div class="hot-card right" v-if="topTwo[1]">
        <div class="hot-card-title">{{ displayName(topTwo[1]) }}</div>
        <div class="hot-card-row"><span>company_type</span><b>{{ safe(topTwo[1].company_type) }}</b></div>
        <div class="hot-card-row"><span>national_job_count</span><b>{{ formatNum(topTwo[1].national_job_count) }}</b></div>
        <div class="hot-card-row"><span>avg_median_salary</span><b>{{ formatNum(topTwo[1].avg_median_salary) }}</b></div>
        <div class="hot-card-row"><span>avg_experience_rank</span><b>{{ formatFloat(topTwo[1].avg_experience_rank) }}</b></div>
        <div class="hot-card-row"><span>avg_education_rank</span><b>{{ formatFloat(topTwo[1].avg_education_rank) }}</b></div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Polyfill: mark wheel/mousewheel listeners passive by default to avoid browser performance warnings.
// Placed before importing echarts so zrender/echarts' internal registrations inherit improved default.
; (function() {
  const origAdd = EventTarget.prototype.addEventListener
  EventTarget.prototype.addEventListener = function(type, listener, options) {
    try {
      if ((type === 'wheel' || type === 'mousewheel') && (options === undefined || (typeof options === 'object' && options && options.passive === undefined))) {
        const newOpts = (typeof options === 'boolean') ? { passive: true, capture: options } : { ...(options || {}), passive: true }
        return origAdd.call(this, type, listener, newOpts)
      }
    } catch (e) {
      // if anything goes wrong, fallback to original
    }
    return origAdd.call(this, type, listener, options)
  }
})()
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useResizeObserver } from '@/composables/useResizeObserver.js'
import '@/assets/styles/chart.css'

const emit = defineEmits(['hotClick', 'sectorClick', 'sectorHover', 'sectorOut', 'hoverStart', 'hoverEnd'])

function onHotClick() {
  showHotCards.value = !showHotCards.value
  emit('hotClick')
}

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  title: {
    type: String,
    default: '双环嵌套玫瑰极坐标图'
  },
  description: {
    type: String,
    default: ''
  }
  ,
  // 外部联动支持：高亮或过滤行业 id/name
  selectedIndustry: { type: [String, Number], default: null },
  highlightedJob: { type: Object, default: null }
})

const chartRef = ref(null)
let chartInstance = null

const { width, height } = useResizeObserver(chartRef)

// 热门卡片可见性（overlay 会遮挡标签，默认关闭）
const showHotCards = ref(false)

// 缩放控制（用于图表放大/缩小）
const zoomFactor = ref(1)
function zoomIn() {
  zoomFactor.value = Math.min(1.6, +(zoomFactor.value * 1.12).toFixed(2))
  renderChart()
}
function zoomOut() {
  zoomFactor.value = Math.max(0.7, +(zoomFactor.value / 1.12).toFixed(2))
  renderChart()
}
// click wrappers with logging and fallback apply
function applyZoomOption() {
  if (!chartInstance) return
  const baseInner = [14, 48]
  const baseOuter = [56, 86]
  const scale = Math.max(0.7, Math.min(1.3, zoomFactor.value))
  const innerStart = Math.max(6, baseInner[0] * scale)
  const innerEnd = Math.min(90, baseInner[1] * scale)
  const innerRadius = [innerStart.toFixed(1) + '%', innerEnd.toFixed(1) + '%']
  const outerStart = Math.max(innerEnd + 2, baseOuter[0] * scale)
  const outerEnd = Math.min(98, baseOuter[1] * scale)
  const outerRadius = [outerStart.toFixed(1) + '%', outerEnd.toFixed(1) + '%']
  try {
    chartInstance.setOption({
      series: [
        { radius: innerRadius },
        { radius: outerRadius }
      ]
    }, false)
  } catch (e) {
    console.warn('applyZoomOption failed', e)
  }
}

function onZoomInClick(e) {
  console.log('zoomIn clicked', zoomFactor.value)
  e.stopPropagation()
  zoomIn()
  applyZoomOption()
}
function onZoomOutClick(e) {
  console.log('zoomOut clicked', zoomFactor.value)
  e.stopPropagation()
  zoomOut()
  applyZoomOption()
}

// 顶部两个行业（按 national_job_count 降序）
const topTwo = computed(() => {
  if (!Array.isArray(props.data)) return []
  const sorted = [...props.data].sort((a, b) => {
    const av = Number.isFinite(Number(a?.national_job_count)) ? Number(a.national_job_count) : -Infinity
    const bv = Number.isFinite(Number(b?.national_job_count)) ? Number(b.national_job_count) : -Infinity
    return bv - av
  })
  return sorted.slice(0, 2)
})

function safe(v) {
  if (v === null || v === undefined || v === '') return '-'
  return String(v)
}
function formatNum(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return n.toLocaleString()
}
function formatFloat(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '-'
  return n.toFixed(2)
}
function displayName(item) {
  if (!item) return '-'
  return item.industry_name || item.company_type || '-'
}

// 仅用于展示的可视化基线（不会改动原始数据）
const BASELINE = 2

function getInnerColorScale(value, min, max) {
  // 浅红到深红（基于薪资）
  const t = (value - min) / (max - min || 1)
  const r = 255
  const g = Math.round(200 - 120 * t)
  const b = Math.round(200 - 120 * t)
  return `rgb(${r},${g},${b})`
}

function getOuterColorScale(value) {
  // 经验要求：浅绿到深绿（0-1）
  const t = Math.max(0, Math.min(1, value))
  // 从浅绿 (240,255,240) 过渡到深绿 (56,158,13)
  const rStart = 240, gStart = 255, bStart = 240
  const rEnd = 56, gEnd = 158, bEnd = 13
  const r = Math.round(rStart + (rEnd - rStart) * t)
  const g = Math.round(gStart + (gEnd - gStart) * t)
  const b = Math.round(bStart + (bEnd - bStart) * t)
  return `rgb(${r},${g},${b})`
}

const renderChart = () => {
  if (!chartRef.value || !props.data || props.data.length === 0) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, null, {
      devicePixelRatio: (window && window.devicePixelRatio) ? window.devicePixelRatio : 1
    })
  }

  // 构造内外环数据（内环：招聘总数；外环：学历归一化）
  const innerData = props.data.map(d => ({
    name: d.industry_name || d.company_type || '',
    value: Number(d.national_job_count) || 0,
    raw: d
  }))

  const outerData = props.data.map(d => {
    const eduNorm = Number(d.avg_education_rank_normalized)
    const eduVal = Number.isFinite(eduNorm) ? eduNorm : (Number(d.avg_education_rank) || 0)
    return {
      name: d.industry_name || d.company_type || '',
      value: Math.max(0, Math.min(1, eduVal)),
      raw: d
    }
  })

  // 颜色映射：内环根据薪资（浅红→深红），外环根据经验（浅绿→深绿）
  const salaries = props.data.map(d => d.avg_median_salary ?? 0)
  const minSal = Math.min(...salaries)
  const maxSal = Math.max(...salaries)

  innerData.forEach(d => {
    d.itemStyle = { color: getInnerColorScale(d.raw.avg_median_salary ?? 0, minSal, maxSal) }
  })

  outerData.forEach(d => {
    d.itemStyle = { color: getOuterColorScale(Number(d.raw.avg_experience_rank ?? 0)) }
    // 为外环显示比例方便，将 value 扩展到 0~100
    d.value = (d.value || 0) * 100
  })

  // 根据 zoomFactor 缩放半径（基于基线值）
  const baseInner = [14, 48]
  const baseOuter = [56, 86]
  const scale = Math.max(0.7, Math.min(1.3, zoomFactor.value))
  const innerStart = Math.max(6, baseInner[0] * scale)
  const innerEnd = Math.min(90, baseInner[1] * scale)
  const innerRadius = [innerStart.toFixed(1) + '%', innerEnd.toFixed(1) + '%']
  const outerStart = Math.max(innerEnd + 2, baseOuter[0] * scale)
  const outerEnd = Math.min(98, baseOuter[1] * scale)
  const outerRadius = [outerStart.toFixed(1) + '%', outerEnd.toFixed(1) + '%']

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const raw = params.data?.raw || {}
        const name = raw.industry_name || raw.company_type || params.name
        const job = raw.national_job_count ?? '-'
        const sal = raw.avg_median_salary ?? '-'
        const eduNorm = Number(raw.avg_education_rank_normalized)
        const edu = (raw.avg_education_rank_10 != null) ? Number(raw.avg_education_rank_10).toFixed(2) : (Number.isFinite(eduNorm) ? eduNorm.toFixed(3) : '-')
        const exp = (raw.avg_experience_rank_10 != null) ? Number(raw.avg_experience_rank_10).toFixed(2) : ((raw.avg_experience_rank != null) ? Number(raw.avg_experience_rank).toFixed(3) : '-')
        return [
          `<div style="font-weight:600;margin-bottom:6px;">${name}</div>`,
          `<div>招聘总数：${job}</div>`,
          `<div>平均薪资：${sal}</div>`,
          `<div>平均学历（10分制/回退0-1）：${edu}</div>`,
          `<div>经验要求：${exp}</div>`
        ].join('')
      }
    },
    legend: { show: false },
    graphic: [
      {
        type: 'group',
        left: 'center',
        top: 'center',
        children: [
          {
            type: 'text',
            style: {
              text: '行业分布',
              font: '600 14px "Microsoft YaHei", Arial',
              fill: '#0b4a8a'
            },
            top: '10'
          },
          {
            type: 'text',
            style: {
              text: `总行业数 ${props.data.length}`,
              font: '500 12px "Microsoft YaHei", Arial',
              fill: '#4a6b8a'
            },
            top: '32'
          }
        ]
      }
    ],
    series: [
      // 内环：招聘总数（用角度展示份额）
      {
        name: '招聘总数',
        type: 'pie',
        radius: ['14%', '48%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        label: {
          show: false,
          position: 'outside'
        },
        labelLine: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(0,0,0,0.3)',
            borderColor: '#fff',
            borderWidth: 2
          }
        },
        data: innerData,
        animationType: 'scale',
        animationEasing: 'cubicOut'
      },
      // 外环：学历（展示为 0~100 的值以便弧长变化），颜色按经验映射
      {
        name: '学历/经验',
        type: 'pie',
        radius: ['56%', '86%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'outside',
          formatter: (params) => {
            const name = params.data?.raw?.industry_name || params.name || ''
            // 控制太长的标签换行
            return name.length > 12 ? name.slice(0, 12) + '...' : name
          },
          color: '#2c3e50',
          fontSize: 11
        },
        labelLine: { length: 14, length2: 8 },
        emphasis: {
          itemStyle: {
            shadowBlur: 18,
            shadowColor: 'rgba(0,0,0,0.25)',
            borderColor: '#fff',
            borderWidth: 1
          }
        },
        data: outerData,
        animationType: 'scale',
        animationEasing: 'cubicOut'
      }
    ]
  }

  chartInstance.setOption(option, true)
  // 点击扇区时向外发出事件，父组件可用来联动星云图
  chartInstance.off('click')
  chartInstance.on('click', (params) => {
    const raw = params.data?.raw || {}
    const industryId = raw.id ?? raw.industry_name ?? params.name
    emit('sectorClick', { industryId, raw })
  })
  // 监听 echarts item hover 事件并向外发出 sectorHover/sectorOut
  chartInstance.off('mouseover')
  chartInstance.on('mouseover', (params) => {
    const raw = params.data?.raw || {}
    if (raw && Object.keys(raw).length) {
      emit('sectorHover', raw)
    }
  })
  chartInstance.off('mouseout')
  chartInstance.on('mouseout', () => {
    emit('sectorOut')
  })
  // use zrender to reliably detect pointer enter/leave over the chart drawing area
  let zr = null
  try {
    zr = chartInstance.getZr()
  } catch (e) {
    zr = null
  }
  if (zr) {
    let localHover = false
    zr.on('mousemove', () => {
      if (!localHover) {
        localHover = true
        emit('hoverStart')
      }
    })
    zr.on('mouseout', () => {
      if (localHover) {
        localHover = false
        emit('hoverEnd')
      }
    })
  }
  // 确保在样式更新后触发一次 resize，使图表按新容器尺寸渲染
  setTimeout(() => {
    if (chartInstance) chartInstance.resize()
  }, 50)
}

// 反向高亮：响应父组件传入的 selectedIndustry / highlightedJob
let _lastHighlightedIndex = null
watch(() => props.selectedIndustry, (val) => {
  if (!chartInstance) return
  try {
    if (_lastHighlightedIndex !== null) {
      chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: _lastHighlightedIndex })
      chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 1, dataIndex: _lastHighlightedIndex })
      _lastHighlightedIndex = null
    }
    if (!val) return
    const idx = (props.data || []).findIndex(d => (d.id != null && d.id === val) || d.industry_name === val || d.company_type === val)
    if (idx >= 0) {
      chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: idx })
      chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 1, dataIndex: idx })
      _lastHighlightedIndex = idx
    }
  } catch (e) {
    // ignore
  }
})

watch(() => props.highlightedJob, (job) => {
  if (!job || !chartInstance) return
  const target = job.industry_id || job.industryId || job.industry_name || job.industryName
  if (target) {
    // let selectedIndustry prop handle visual highlight; chart reacts to prop changes
  }
})
// pulse highlight helper
function pulseHighlight(idx, times = 2, interval = 420) {
  if (!chartInstance || idx == null || idx < 0) return
  let i = 0
  function tick() {
    if (!chartInstance) return
    chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: idx })
    chartInstance.dispatchAction({ type: 'highlight', seriesIndex: 1, dataIndex: idx })
    setTimeout(() => {
      if (!chartInstance) return
      chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: idx })
      chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 1, dataIndex: idx })
      i++
      if (i < times) setTimeout(tick, interval)
    }, Math.floor(interval / 2))
  }
  tick()
}

// focus/zoom helper exposed to parent
function focusOnIndustry(industryId) {
  if (!industryId || !chartInstance) return
  const idx = (props.data || []).findIndex(d => (d.id != null && d.id === industryId) || d.industry_name === industryId || d.company_type === industryId)
  if (idx < 0) return
  // pulse highlight for emphasis
  pulseHighlight(idx, 2, 480)
  // smooth zoom by temporarily increasing zoomFactor
  const target = Math.min(1.3, Math.max(1.05, zoomFactor.value * 1.18))
  const prev = zoomFactor.value
  zoomFactor.value = target
  applyZoomOption()
  setTimeout(() => {
    zoomFactor.value = prev
    applyZoomOption()
  }, 900)
}

// allow parent to call focusOnIndustry via ref
defineExpose({ focusOnIndustry })

watch(() => props.data, () => {
  renderChart()
}, { deep: true })

watch([width, height], () => {
  if (chartInstance) {
    chartInstance.resize()
  }
})

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
  if (chartRef.value) {
    chartRef.value.addEventListener('pointerenter', onChartPointerEnter)
    chartRef.value.addEventListener('pointerleave', onChartPointerLeave)
  }
})

function handleResize() {
  if (chartInstance) chartInstance.resize()
}

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (chartRef.value) {
    chartRef.value.removeEventListener('pointerenter', onChartPointerEnter)
    chartRef.value.removeEventListener('pointerleave', onChartPointerLeave)
  }
})

function onChartPointerEnter() {
  emit('hoverStart')
}
function onChartPointerLeave() {
  emit('hoverEnd')
}
</script>

<style scoped>
.rose-nested-polar {
  width: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible !important;
  z-index: 999999 !important;
  pointer-events: auto !important;
}
.chart-container {
  width: 100%;
  height: 560px;
}
.chart-container {
  /* 覆盖全局 chart.css 的白色卡片样式，使本组件不被包裹 */
  margin-top: 0 !important;
  border: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
  overflow: visible !important;
  max-width: none !important;
  width: 100% !important;
  z-index: 2;
}
.rose-wrapper .rose-chart .chart-container {
  width: 80vw !important;
  max-width: 1100px !important;
  margin: 0 auto !important;
}
.chart-title {
  margin-bottom: 10px;
}
.chart-description {
  margin-bottom: 10px;
}
.zoom-controls {
  position: absolute;
  right: 18px;
  top: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000000 !important;
  pointer-events: auto !important;
}
.zoom-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: rgba(0,0,0,0.08);
  color: #0b4a8a;
  font-size: 18px;
  cursor: pointer;
  backdrop-filter: blur(4px);
}
.zoom-btn:hover { background: rgba(0,0,0,0.12); }

/* 隐藏 overlay 热门卡片，避免遮挡标签 */
.hot-cards { display: none !important; pointer-events: none !important; }
/* 中心按钮已移除 */
.hot-cards {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0; /* ensure hot-cards background does not cover chart labels */
}
.hot-card {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 300px;
  max-width: 32vw;
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.96), rgba(236, 247, 255, 0.92));
  backdrop-filter: blur(8px) saturate(110%);
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 16px;
  box-shadow: 0 10px 28px rgba(24, 144, 255, 0.15), 0 2px 10px rgba(2, 40, 80, 0.06);
  padding: 16px 18px;
  color: #0d1b2a;
  pointer-events: auto;
  z-index: 1;
  transition: transform 160ms ease, box-shadow 180ms ease, background 200ms ease;
}
.hot-card:hover {
  transform: translateY(calc(-50% - 2px));
  box-shadow: 0 14px 36px rgba(24, 144, 255, 0.2), 0 6px 14px rgba(2, 32, 64, 0.08);
}
.hot-card.left { left: 20px; }
.hot-card.right { right: 20px; }
.hot-card-title {
  position: relative;
  font-weight: 800;
  font-size: 15px;
  margin-bottom: 12px;
  line-height: 1.2;
  padding-left: 12px;
  color: #0b4a8a;
}
.hot-card-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 2px;
  bottom: 2px;
  width: 4px;
  border-radius: 4px;
  background: linear-gradient(180deg, #91d5ff 0%, #1890ff 100%);
  box-shadow: 0 0 0 2px rgba(145, 213, 255, 0.18) inset;
}
.hot-card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px dashed rgba(11, 74, 138, 0.12);
}
.hot-card-row:last-child { border-bottom: none; }
.hot-card-row span { color: #4a6b8a; }
.hot-card-row b { color: #0d1b2a; font-weight: 800; }
</style>


