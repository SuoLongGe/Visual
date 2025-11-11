<template>
  <div class="rose-nested-polar">
    <h3 v-if="title" class="chart-title">{{ title }}</h3>
    <p v-if="description" class="chart-description">{{ description }}</p>
    <div ref="chartRef" class="chart-container"></div>
    <button class="center-hot-btn" type="button" aria-label="行业大热" @click="onHotClick">
      <span>行业</span>
      <span>大热</span>
    </button>
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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useResizeObserver } from '@/composables/useResizeObserver.js'
import '@/assets/styles/chart.css'

const emit = defineEmits(['hotClick'])

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
})

const chartRef = ref(null)
let chartInstance = null

const { width, height } = useResizeObserver(chartRef)

// 热门卡片可见性
const showHotCards = ref(false)

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

  const industries = props.data.map(d => d.industry_name || d.company_type || '')

  // 角度按行业均匀分布
  const angleCategories = industries

  // 归一化（内环半径：national_job_count -> 0~10）
  const jobCounts = props.data.map(d => d.national_job_count ?? 0)
  const minJobs = Math.min(...jobCounts)
  const maxJobs = Math.max(...jobCounts)
  const innerRadii = props.data.map(d => {
    const v = d.national_job_count ?? 0
    const norm = (v - maxJobs) / ((maxJobs - minJobs) || 1) // 文档给出的公式
    return Math.max(0, 10 * (1 - Math.abs(norm))) // 避免负数，保持0~10范围
  })

  // 内环颜色（薪资：浅红->深红，10级离散）
  const salaries = props.data.map(d => d.avg_median_salary ?? 0)
  const minSal = Math.min(...salaries)
  const maxSal = Math.max(...salaries)
  const innerColors = props.data.map(d => {
    const c = getInnerColorScale(d.avg_median_salary ?? 0, minSal, maxSal)
    return c
  })

  // 外环半径：使用“学历归一化值”（0~1）-> 0~10
  const outerExtend = props.data.map(d => {
    const eduNorm = Number(d.avg_education_rank_normalized)
    const eduColorNorm = Number(d.avg_education_rank) // 颜色用不到，但保留回退逻辑时可参考
    const v = Number.isFinite(eduNorm) ? eduNorm : (Number.isFinite(eduColorNorm) ? eduColorNorm : 0)
    return Math.max(0, Math.min(1, v)) * 10
  })
  // 外环颜色：
  // 优先使用后端分档产出的 outer_ring_color（深蓝到浅蓝的 5 档），
  // 若不存在则回退为连续色带（基于 avg_experience_rank 0~1）
  const outerColors = props.data.map(d => {
    if (d.outer_ring_color) return d.outer_ring_color
    return getOuterColorScale(Number(d.avg_experience_rank ?? 0))
  })

  const innerSeriesData = angleCategories.map((name, idx) => ({
    value: innerRadii[idx] + BASELINE + 4,
    name,
    itemStyle: { color: innerColors[idx] },
    raw: props.data[idx]
  }))

  const outerSeriesData = angleCategories.map((name, idx) => ({
    value: outerExtend[idx] + BASELINE - 4,
    name,
    itemStyle: { color: outerColors[idx] },
    raw: props.data[idx]
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const raw = params.data?.raw || {}
        const name = raw.industry_name || raw.company_type || params.name
        const job = raw.national_job_count ?? '-'
        const sal = raw.avg_median_salary ?? '-'
        // 外环实际采用的归一化数值（学历 0~1），用于tooltip展示
        const eduNorm = Number(raw.avg_education_rank_normalized)
        const usedOuterNorm = Number.isFinite(eduNorm) ? Math.max(0, Math.min(1, eduNorm)) : null
        // 优先显示数据库直接计算的 10 分制均值
        const edu10 = (raw.avg_education_rank_10 != null) ? Number(raw.avg_education_rank_10).toFixed(2) : null
        const exp10 = (raw.avg_experience_rank_10 != null) ? Number(raw.avg_experience_rank_10).toFixed(2) : null
        // 兼容旧值（0~1），如无 10 分制则回退显示 0~1
        const edu = (edu10 != null) ? edu10 : (Number.isFinite(eduNorm) ? eduNorm.toFixed(2) : '-')
        const exp = (exp10 != null) ? exp10 : ((raw.avg_experience_rank != null) ? (Number(raw.avg_experience_rank).toFixed(2)) : '-')
        const outerUsed = (usedOuterNorm != null) ? usedOuterNorm.toFixed(3) : '-'
        const bucket = raw.outer_ring_bucket || '-'
        const ring = params.seriesName
        return [
          `<div style="font-weight:600;margin-bottom:4px;">${name}</div>`,
          `<div>• 所属环：${ring}</div>`,
          `<div>• 招聘总数：${job}</div>`,
          `<div>• 平均薪资：${sal}</div>`,
          `<div>• 平均学历（10分制/回退0-1）：${edu}</div>`,
          `<div>• 经验要求（10分制/回退0-1）：${exp}</div>`,
          `<div>• 外环归一化（0-1）：${outerUsed}</div>`,
          `<div>• 外环分档：${bucket}</div>`
        ].join('')
      }
    },
    angleAxis: {
      type: 'category',
      data: angleCategories,
      startAngle: 90,
      axisLabel: {
        interval: 0,
        fontSize: 11,
        rotate: 35,
        hideOverlap: true,
        formatter: (val) => {
          // 强制显示完整类别名，必要时换行提升可读性
          if (!val) return ''
          const s = String(val)
          return s.length > 8 ? s.slice(0, 8) + '\n' + s.slice(8) : s
        }
      }
    },
    radiusAxis: {
      // 预留空间（内10 + 外10 + 基线2 + 基线2 + padding）
      max: 26,
      axisLabel: { show: true }
    },
    // 放大绘图区，减小中心空白，整体更聚焦
    polar: {
      radius: ['20%', '88%']
    },
    legend: {
      data: ['内环：招聘总数/薪资', '外环：学历/经验'],
      top: 0
    },
    series: [
      {
        name: '内环：招聘总数/薪资',
        type: 'bar',
        coordinateSystem: 'polar',
        roundCap: true,
        barCategoryGap: '10%',
        data: innerSeriesData,
        itemStyle: { opacity: 0.9 },
        emphasis: { focus: 'series' },
        stack: 'total'
      },
      {
        name: '外环：学历/经验',
        type: 'bar',
        coordinateSystem: 'polar',
        roundCap: true,
        barCategoryGap: '10%',
        data: outerSeriesData,
        itemStyle: { opacity: 0.9 },
        emphasis: { focus: 'series' },
        stack: 'total'
      }
    ]
  }

  chartInstance.setOption(option)
}

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
})
</script>

<style scoped>
.rose-nested-polar {
  width: 100%;
  position: relative;
}
.chart-container {
  width: 100%;
  height: 560px;
}
.chart-title {
  margin-bottom: 10px;
}
.chart-description {
  margin-bottom: 10px;
}
.center-hot-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) translateY(22px);
  z-index: 2;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: none;
  color: #fff;
  background: radial-gradient(120px 120px at 30% 30%, #69c0ff, #1890ff);
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.35), inset 0 -6px 12px rgba(0, 32, 64, 0.18);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  user-select: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  letter-spacing: 2px;
  backdrop-filter: blur(2px);
  transition: transform 120ms ease, box-shadow 160ms ease, filter 160ms ease;
}
.center-hot-btn:active {
  transform: translate(-50%, -50%) translateY(16px) scale(0.96);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.28), inset 0 -4px 10px rgba(0, 32, 64, 0.22);
}
.center-hot-btn:hover {
  filter: brightness(1.04);
  box-shadow: 0 10px 28px rgba(24, 144, 255, 0.42), inset 0 -6px 12px rgba(0, 32, 64, 0.16);
}
.hot-cards {
  position: absolute;
  inset: 0;
  pointer-events: none;
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


