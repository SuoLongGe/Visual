<template>
  <div class="q5-tab">
    <!-- 第 1 页：两个图表并排显示 -->
    <div v-if="currentPage === 1">
      <div class="charts-container">
        <!-- 视图1：Math-Based 多维 Icon 柱状图 -->
        <div class="chart-section chart-left">
          <h2>Math-Based 多维 Icon 柱状图</h2>
          <p class="chart-description">
            展示职位在招聘数量、学历要求、经验要求等维度的综合排名
            <br/>
            <strong>💡 提示：鼠标悬浮于任意柱体时，将显示详细信息（职位名称、招聘数量、平均学历要求、平均经验年限）</strong>
          </p>
          
          <div class="api-section">
            <!--<div style="margin-bottom: 8px; font-size: 14px; color: #666;">
              💡 系统已优化：支持数据缓存，首次加载后自动保存，第二次及以后加载速度大幅提升
            </div>-->
            <button class="btn" @click="handleLoadChart" :disabled="loading">
              {{ loading ? '加载中...' : (chartData ? '重新加载职位排名数据' : '加载职位排名数据') }}
            </button>
            
            <div v-if="error" class="error-message">
              <p>加载失败: {{ error }}</p>
            </div>
            
            <MultiIconBarChart 
              v-if="chartData?.data?.jobs"
              :data="chartData.data.jobs"
              :loading="loading"
              :error="error"
            />
            
            <div v-if="!chartData && !loading && !error" class="empty-state">
              <p>点击上方按钮加载数据</p>
            </div>
          </div>
        </div>

        <!-- 视图2：连续型进度条图 -->
        <div class="chart-section chart-right">
          <h2>Math-Based 多维进度条图（连续型）</h2>
          <p class="chart-description">
            展示职位在招聘数量、学历要求、经验要求等维度的连续型综合排名
            <br/>
            <strong>💡 提示：鼠标悬浮于任意进度条时，将显示详细信息（职位名称、招聘数量、平均学历要求、平均经验年限）</strong>
          </p>
          
          <div class="api-section">
            <button class="btn" @click="handleLoadChart" :disabled="loading">
              {{ loading ? '加载中...' : '加载职位排名数据' }}
            </button>
            
            <div v-if="error" class="error-message">
              <p>加载失败: {{ error }}</p>
            </div>
            
            <ContinuousProgressBarChart 
              v-if="chartData?.data?.jobs"
              :data="chartData.data.jobs"
              :loading="loading"
              :error="error"
            />
            
            <div v-if="!chartData && !loading && !error" class="empty-state">
              <p>点击上方按钮加载数据</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第 2 页：行业双环嵌套玫瑰极坐标图（ECharts） -->
    <div v-else-if="currentPage === 2">
      <div class="chart-section chart-full">
        <h2>行业双环嵌套玫瑰极坐标图</h2>
        <p class="chart-description">
          内环：角度均匀分配各行业；半径表示行业招聘总数（归一化 0~10）；颜色深浅映射平均薪资（浅红→深红）。
          <br/>
          外环：与内环角度对齐；半径为平均学历要求（0~1 映射 0~10）；颜色深浅映射经验要求（浅绿→深绿）。
          <br/>
          <strong>💡 提示：鼠标悬浮某行业，动态展示其详细信息</strong>
        </p>

        <div class="api-section">
          <!--<button class="btn" @click="handleLoadIndustryRose" :disabled="roseLoading">
            {{ roseLoading ? '加载中...' : '加载行业玫瑰图数据' }}
          </button>-->

          <div v-if="roseError" class="error-message">
            <p>加载失败: {{ roseError }}</p>
          </div>

            <div v-if="roseData && roseData.data && roseData.data.industries" class="nebula-vertical">
             <!-- 上：玫瑰图 + 左侧 Top2 卡片 -->
              <div class="rose-section">
                <div class="top-cards-sidebar">
                  <!-- 调试信息 -->
                  <!--<div style="font-size:10px;color:#666;padding:4px;margin-bottom:8px;background:#f0f8ff;border-radius:3px;max-width:200px;word-break:break-all;">
                    调试: roseData={{ !!roseData }}, data={{ !!roseData?.data }}, industries={{ roseData?.data?.industries?.length || 'N/A' }}, topTwo={{ topTwo?.length }}, loading={{ roseLoading }}
                  </div>-->
                  <!-- 显示Top2卡片，如果没有数据则显示占位符 -->
                  <div v-if="topTwo && topTwo.length > 0" v-for="(it, idx) in topTwo" :key="idx" class="top-card-small">
                    <div class="top-card-title">{{ it.industry_name || it.company_type || '行业' }}</div>
                    <div class="top-card-row">招聘总数: <b>{{ formatNum(it.national_job_count || it.count || it.records) }}</b></div>
                    <div class="top-card-row">平均薪资: <b>{{ formatNum(it.avg_median_salary || it.median_salary || it.salary) }}</b></div>
                    <div class="top-card-row">经验: <b>{{ formatFloat(it.avg_experience_rank) }}</b></div>
                  </div>
                  <!-- 数据加载中或无数据的占位符 -->
                  <div v-else class="top-card-small placeholder">
                    <div class="top-card-title">{{ roseLoading ? '数据加载中...' : '暂无数据' }}</div>
                    <div class="top-card-row">招聘总数: <b>--</b></div>
                    <div class="top-card-row">平均薪资: <b>--</b></div>
                    <div class="top-card-row">经验: <b>--</b></div>
                  </div>
                </div>
                <div class="rose-wrapper">
          <RoseNestedPolar
                  class="rose-chart"
                  ref="roseRef"
            :data="roseData.data.industries"
                  :selectedIndustry="selectedIndustry"
                  :highlightedJob="selectedJob"
            title="行业双环嵌套玫瑰图"
                  @sectorClick="onSectorClick"
                  @sectorHover="onSectorHover"
                  @sectorOut="onSectorOut"
                  @hoverStart="onRoseHoverStart"
                  @hoverEnd="onRoseHoverEnd"
                />
                </div>
              </div>

            <!-- 下：星云 + 侧栏，星云铺满可用空间 -->
            <div class="nebula-row">
              <div class="nebula-chart-wrapper" :class="{ 'nebula-disabled': roseHover, 'nebula-zoomed': nebulaZoom }">
                <IndustryNebula
                  :industries="roseData.data.industries"
                  :filterIndustry="selectedIndustry"
                  :interactive="!roseHover"
                  :fogEnabled="nebulaControls.fogEnabled"
                  :heatIntensity="nebulaControls.heatIntensity"
                  :footprintDecay="nebulaControls.footprintDecay"
                  :terrainMode="nebulaControls.terrainMode"
                  :terrainSmooth="nebulaControls.terrainSmooth"
                  @industryEnter="onIndustryEnter"
                  @selectJob="onSelectJob"
                  @hoverIndustry="onNebulaHover"
                  class="nebula-chart"
                />
              </div>

              <div class="info-panel">
                <div class="nebula-controls" style="margin-bottom:12px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                    <label style="font-size:13px;color:#234">迷雾 (Fog)</label>
                    <input type="checkbox" v-model="nebulaControls.fogEnabled" />
                  </div>
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                    <label style="font-size:13px;color:#234;flex:1">热力强度</label>
                    <input type="range" min="0.2" max="3" step="0.1" v-model.number="nebulaControls.heatIntensity" />
                    <div style="width:40px;text-align:right">{{ nebulaControls.heatIntensity.toFixed(1) }}</div>
                  </div>
                  <div style="display:flex;align-items:center;gap:8px;">
                    <label style="font-size:13px;color:#234;flex:1">足迹衰减</label>
                    <input type="range" min="0.0" max="0.2" step="0.01" v-model.number="nebulaControls.footprintDecay" />
                    <div style="width:40px;text-align:right">{{ nebulaControls.footprintDecay.toFixed(2) }}</div>
                  </div>
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
                    <label style="font-size:13px;color:#234">地形热力模式</label>
                    <input type="checkbox" v-model="nebulaControls.terrainMode" />
                  </div>
                  <div style="display:flex;align-items:center;gap:8px;margin-top:6px;">
                    <label style="font-size:13px;color:#234;flex:1">平滑强度</label>
                    <input type="range" min="0" max="1" step="0.05" v-model.number="nebulaControls.terrainSmooth" />
                    <div style="width:40px;text-align:right">{{ nebulaControls.terrainSmooth.toFixed(2) }}</div>
                  </div>
                  <div style="margin-top:12px;">
                    <div style="font-size:13px;color:#234;margin-bottom:6px;">颜色 → 平均薪资（低 → 高）</div>
                    <div :style="{ height: '10px', borderRadius: '6px', background: 'linear-gradient(to right,' + salaryColorStops(12) + ')' }"></div>
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-top:6px;color:#567;">
                      <div>{{ formatNum(salaryExtent[0]) }}</div>
                      <div>{{ formatNum(salaryExtent[1]) }}</div>
                    </div>
                    <!--<div style="margin-top:8px;font-size:13px;color:#234;">面积 → 招聘总数（小 → 大）</div>
                    <div style="display:flex;align-items:center;gap:12px;margin-top:6px;">
                      <div style="display:flex;flex-direction:column;align-items:center;">
                        <div :style="{ width: mapCountToPx(countExtent[0]) + 'px', height: mapCountToPx(countExtent[0]) + 'px', borderRadius: '50%', background: '#eee' }"></div>
                        <div style="font-size:11px;color:#777;margin-top:4px;">{{ countExtent[0] }}</div>
                      </div>
                      <div style="display:flex;flex-direction:column;align-items:center;">
                        <div :style="{ width: mapCountToPx(countExtent[1]) + 'px', height: mapCountToPx(countExtent[1]) + 'px', borderRadius: '50%', background: '#eee' }"></div>
                        <div style="font-size:11px;color:#777;margin-top:4px;">{{ countExtent[1] }}</div>
                      </div>
                    </div>-->
                  </div>
                </div>
                  <div v-if="selectedJob" class="job-detail">
                  <h3>{{ selectedJob.job_title || selectedJob.name || '职位详情' }}</h3>
                  <p>行业: {{ selectedJob.industry_name || selectedJob.industryName || '-' }}</p>
                  <p>招聘数量: {{ formatNum(selectedJob.count || selectedJob.records || selectedJob.num) }}</p>
                  <p>平均薪资: {{ formatNum(selectedJob.median_salary || selectedJob.salary || '-') }}</p>
                  <p>经验要求: {{ formatFloat(selectedJob.experience_rank || selectedJob.avg_experience_rank || '-') }}</p>
                  <div style="display:flex;gap:8px;margin-top:8px;">
                    <button class="btn" @click="() => { /* 可扩展：跳转到详情 */ }">查看职位详情</button>
                    <button class="btn" @click="() => focusNebula(selectedJob.industry_id || selectedJob.industryId || selectedJob.industry_name || selectedJob.industryName)">定位到星云</button>
                  </div>
                </div>
                <!-- hoverIndustry no longer controls the side panel; only selectedIndustry/currentIndustryData does -->
                <div v-else-if="currentIndustryData" class="industry-detail">
                  <h3>{{ currentIndustryData.industry_name || currentIndustryData.company_type || '行业详情' }}</h3>
                  <p>招聘总数: {{ formatNum(currentIndustryData.national_job_count) }}</p>
                  <p>平均薪资: {{ formatNum(currentIndustryData.avg_median_salary) }}</p>
                  <p>平均经验: {{ formatFloat(currentIndustryData.avg_experience_rank) }}</p>
                  <p>平均学历(归一化): {{ formatFloat(currentIndustryData.avg_education_rank_normalized) }}</p>
                  <h4>Top 5 职位（按招聘数量）</h4>
                  <ul class="top-jobs">
                    <li v-for="(job, idx) in getTopByCount(currentIndustryData)" :key="idx" style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
                      <span>{{ job.name || job.job_title }} <span class="tag">{{ job.count || job.records || '' }}</span></span>
                      <button class="btn" @click="() => onSelectJob(job)" style="padding:6px 8px;font-size:12px;">显示职位</button>
                    </li>
                  </ul>
                </div>
                <div v-else class="industry-list">
                  <h4>热门行业 Top 2（按招聘总数）</h4>
                  <div v-if="topTwo && topTwo.length">
                    <div v-for="(it, idx) in topTwo" :key="idx" class="top-card">
                      <div class="top-card-title">{{ it.industry_name || it.company_type || '行业' }}</div>
                      <div class="top-card-row">招聘总数: <b>{{ formatNum(it.national_job_count || it.count || it.records) }}</b></div>
                      <div class="top-card-row">平均薪资: <b>{{ formatNum(it.avg_median_salary || it.median_salary || it.salary) }}</b></div>
                      <div class="top-card-row">经验: <b>{{ formatFloat(it.avg_experience_rank) }}</b></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="!roseData && !roseLoading && !roseError" class="empty-state">
            <p>点击上方按钮加载数据</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页按钮 -->
    <div class="pager">
      <button class="btn" :disabled="currentPage === 1" @click="goPrev">上一页</button>
      <span class="page-indicator">第 {{ currentPage }} / 2 页</span>
      <button class="btn" :disabled="currentPage === 2" @click="goNext">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useFetchData, useCachedFetchData } from '@/utils/fetchData.js'
import { getJobRanking } from '@/api/industryApi.js'
import { getIndustryTrendRose } from '@/api/industryApi.js'
import MultiIconBarChart from '@/components/charts/MultiIconBarChart.vue'
import ContinuousProgressBarChart from '@/components/charts/ContinuousProgressBarChart.vue'
import * as d3 from 'd3'
import RoseNestedPolar from '@/components/charts/RoseNestedPolar.vue'
import IndustryNebula from '@/components/charts/IndustryNebula.vue'

const currentPage = ref(1)
const goPrev = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}
const goNext = () => {
  if (currentPage.value < 2) {
    currentPage.value += 1
    // 如果切换到第2页，自动加载玫瑰图数据
    if (currentPage.value === 2) {
      autoLoadRoseData()
    }
  }
}

// 自动加载玫瑰图数据
const autoLoadRoseData = async () => {
  try {
    await handleLoadIndustryRose()
  } catch (err) {
    console.error('自动加载玫瑰图数据失败:', err)
  }
}

// 监听页面变化，当切换到第2页时自动加载数据
watch(currentPage, (newPage) => {
  if (newPage === 2) {
    autoLoadRoseData()
  }
})

// 组件挂载时如果在第2页就自动加载数据
onMounted(() => {
  if (currentPage.value === 2) {
    autoLoadRoseData()
  }
})

const { data: chartData, loading, error, execute } = useCachedFetchData(getJobRanking, 'jobRankingData', 7 * 24 * 60 * 60 * 1000) // 7天缓存
const { data: roseData, loading: roseLoading, error: roseError, execute: executeRose } = useFetchData(getIndustryTrendRose)

const handleLoadChart = async () => {
  try {
    console.log('正在加载职位排名数据...')
    await execute()
    console.log('职位排名数据加载完成')
  } catch (err) {
    console.error('加载职位排名数据失败:', err)
  }
}

const handleLoadIndustryRose = async () => {
  try {
    await executeRose()
  } catch (err) {
    console.error('加载行业玫瑰图数据失败:', err)
  }
}

// compute top two industries by job count for default display
const topTwo = computed(() => {
  const industries = roseData.value?.data?.industries
  if (!industries) return []

  const arr = industries.filter(Boolean).map(i => ({ ...i }))
  if (!arr.length) return []

  arr.sort((a, b) => {
    const av = Number(a?.national_job_count ?? a?.count ?? a?.records) || 0
    const bv = Number(b?.national_job_count ?? b?.count ?? b?.records) || 0
    return bv - av
  })

  return arr.slice(0, 2)
})

// 联动状态：选中的行业 / 职位
const selectedIndustry = ref(null)
const selectedJob = ref(null)
const roseHover = ref(false)
const roseRef = ref(null)
const nebulaZoom = ref(false)
const nebulaControls = ref({
  fogEnabled: true,
  heatIntensity: 1.0,
  footprintDecay: 0.06,
  terrainMode: false,
  terrainSmooth: 0.6
})
const selectedIndustryRaw = ref(null)

// legend / mapping helpers
const salaryExtent = computed(() => {
  const arr = (roseData?.data?.industries || []).map(d => Number(d.avg_median_salary) || 0)
  if (!arr.length) return [0, 1]
  return [Math.min(...arr), Math.max(...arr)]
})
const countExtent = computed(() => {
  const arr = (roseData?.data?.industries || []).map(d => Number(d.national_job_count || d.count || d.records) || 0)
  if (!arr.length) return [0, 1]
  return [Math.min(...arr), Math.max(...arr)]
})
function salaryColorStops(n = 6) {
  const [minS, maxS] = salaryExtent.value
  const stops = []
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const color = d3.interpolateMagma(t)
    stops.push(`${color} ${Math.round(t*100)}%`)
  }
  return stops.join(', ')
}
function mapCountToPx(v) {
  const [minC, maxC] = countExtent.value
  const raw = Number(v) || 0
  const t = maxC > minC ? (raw - minC) / (maxC - minC) : 0.5
  const minPx = 8, maxPx = 64
  return Math.round(minPx + (maxPx - minPx) * Math.sqrt(Math.max(0, Math.min(1, t))))
}

function onSectorClick(payload) {
  // payload: { industryId, raw }
  selectedIndustry.value = payload.industryId
  // semantic transition: fade/scale rose and zoom nebula
  nebulaZoom.value = true
  // add class to rose to shrink/fade
  const roseEl = document.querySelector('.rose-wrapper')
  if (roseEl) roseEl.classList.add('rose-transitioning')
  focusNebula(payload.industryId)
  setTimeout(() => {
    nebulaZoom.value = false
    if (roseEl) roseEl.classList.remove('rose-transitioning')
  }, 900)
}

function onIndustryEnter(rawIndustry) {
  // nebula 发来行业进入事件
  selectedIndustry.value = rawIndustry.id ?? rawIndustry.industry_name ?? null
  // store raw object for direct display
  selectedIndustryRaw.value = rawIndustry
  // clear hover override so info panel shows the entered industry
  hoverIndustry.value = null
}

function onSelectJob(job) {
  selectedJob.value = job
  // 也把所属行业同步为选中
  if (job && job.industry_id) selectedIndustry.value = job.industry_id
  // 反向联动：让玫瑰高亮并短暂放大；并滚动到星云、触发聚焦
  try {
    if (roseRef && roseRef.value && selectedIndustry.value) {
      roseRef.value.focusOnIndustry(selectedIndustry.value)
    }
  } catch (e) { /* ignore */ }
  focusNebula(selectedIndustry.value)
}

function focusNebula(indust) {
  if (!indust) return
  selectedIndustry.value = indust
  const el = document.querySelector('.nebula-chart-wrapper')
  if (el && el.scrollIntoView) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function onRoseHoverStart() {
  roseHover.value = true
}
function onRoseHoverEnd() {
  roseHover.value = false
}

const currentIndustryData = computed(() => {
  if (selectedIndustryRaw.value) return selectedIndustryRaw.value
  if (!roseData?.data?.industries || !selectedIndustry.value) return null
  return roseData.data.industries.find(i => {
    return i.id === selectedIndustry.value || i.industry_name === selectedIndustry.value || i.company_type === selectedIndustry.value
  }) || null
})

function formatNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString() : '-'
}
function formatFloat(v, d = 2) {
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(d) : '-'
}

// 新增：玫瑰扇区 hover 显示（不触发地图）
const hoverIndustry = ref(null)
function onSectorHover(raw) {
  hoverIndustry.value = raw
}
function onSectorOut() {
  hoverIndustry.value = null
}
function onNebulaHover(raw) {
  hoverIndustry.value = raw
}
function getTopByCount(industry) {
  if (!industry || !Array.isArray(industry.top_jobs)) return []
  return [...industry.top_jobs].sort((a, b) => {
    const av = Number(a.count || a.records || 0)
    const bv = Number(b.count || b.records || 0)
    return bv - av
  }).slice(0, 5)
}
function getEmergingJobs(industry) {
  if (!industry || !Array.isArray(industry.top_jobs)) return []
  const emergings = industry.top_jobs.filter(j => Boolean(j.is_emerging) || (Number(j.score) || 0) > 0.8 || (Number(j.count) || 0) > 200)
  if (emergings.length) return emergings.slice(0, 5)
  // fallback to top by count if no explicit emerging flag
  return getTopByCount(industry)
}
</script>

<style scoped>
.q5-tab {
  width: 100%;
}

.charts-container {
  display: flex;
  gap: 20px;
  width: 100%;
}

.chart-section {
  flex: 1;
  min-width: 0; /* 防止flex子项溢出 */
}

.chart-left,
.chart-right {
  display: flex;
  flex-direction: column;
}
.chart-full {
  margin-top: 30px;
}
.nebula-container {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.nebula-container > * {
  flex: 1 1 0;
}
.nebula-chart {
  min-width: 300px;
  max-width: 100%;
  flex: 1 1 600px;
}
.rose-chart {
  flex: 0 0 420px; /* 保证玫瑰图有固定可见宽度 */
  min-width: 360px;
  max-width: 48%;
}
.info-panel {
  width: 320px;
  padding: 12px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.industry-list .top-card { background: linear-gradient(180deg,#fff,#fafafa); border-radius:8px; padding:10px; margin-bottom:8px; border:1px solid #eef3f6 }
.industry-list .top-card-title { font-weight:700; color:#0b4a8a; margin-bottom:6px }
.industry-list .top-card-row { font-size:13px; color:#445; margin:4px 0 }
.info-panel h3 { margin: 0 0 8px; font-size: 16px; color: #0b4a8a }
.info-panel p { margin: 6px 0; color: #455; font-size: 13px }
.top-jobs { padding-left: 16px; margin: 8px 0 }
.top-jobs .tag { background: #f0f0f0; padding: 2px 6px; border-radius: 6px; margin-left: 8px; font-size:12px }
.job-detail .btn { margin-top:8px; width:100% }
.nebula-vertical { display:flex; flex-direction:column; gap:18px; width:100%; align-items:stretch; }
.rose-section { display: flex; gap: 16px; align-items: flex-start; width: 100%; margin-bottom: 24px; }
.top-cards-sidebar { flex: 0 0 220px; display: flex; flex-direction: column; gap: 12px; }
.top-card-small { background: linear-gradient(180deg,#fff,#fafafa); border-radius:8px; padding:10px; border:1px solid #eef3f6; font-size: 12px; }
.top-card-small .top-card-title { font-weight:700; color:#0b4a8a; margin-bottom:4px; font-size: 13px; }
.top-card-small .top-card-row { margin:2px 0; color:#445; }
.top-card-small.placeholder { background: linear-gradient(180deg,#f9f9f9,#f5f5f5); border:1px dashed #ddd; }
.top-card-small.placeholder .top-card-title { color:#999; }
.top-card-small.placeholder .top-card-row { color:#ccc; }
.rose-wrapper { flex: 1 1 auto; display:block; position:sticky; top:12px; align-self:flex-start; min-height:420px; padding-top:24px; padding-bottom:24px; background:transparent; z-index:40; }
.rose-wrapper .rose-chart { position:relative; left:auto; top:auto; transform:none; width:100%; max-width:1100px; margin:0 auto; background: transparent !important; box-shadow: none !important; border-radius: 0 !important; padding: 0 !important; }
.rose-wrapper .rose-chart .chart-container { height: 460px !important; min-height: 380px; width:100%; background: transparent !important; box-shadow: none !important; border-radius: 0 !important; padding: 0 !important; overflow: visible !important; }
.nebula-row { display:flex; gap:16px; align-items:flex-start; width:100%; }
.nebula-chart-wrapper { flex:1 1 0; min-height:640px; display:flex; justify-content:center; align-items:stretch; }
.nebula-chart-wrapper .nebula-chart { width:100%; height:100%; min-height:640px; display:block; }
.info-panel { flex: 0 0 320px; max-height: 640px; overflow:auto; }
.nebula-disabled .industry-nebula,
.nebula-disabled canvas {
  pointer-events: none !important;
  user-select: none !important;
}

.q5-tab h2 {
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 24px;
}

.chart-description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
  font-size: 14px;
}

.chart-description strong {
  color: #5470c6;
  font-weight: 600;
}

.api-section {
  margin-top: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}


.btn {
  padding: 10px 20px;
  background: #5470c6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s;
  margin-bottom: 20px;
}

.btn:hover:not(:disabled) {
  background: #4558a3;
}

.btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  padding: 15px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c33;
  margin-bottom: 20px;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.pager {
  margin-top: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-indicator {
  color: #666;
  font-size: 14px;
}
@media (max-width: 900px) {
  .rose-section { flex-direction: column; }
  .top-cards-sidebar { flex: none; width: 100%; flex-direction: row; gap: 12px; }
  .top-card-small { flex: 1; }
  .rose-wrapper { flex: none; width: 100%; }
  .nebula-row { flex-direction: column; }
  .info-panel { width: 100%; max-height: none; }
}
.rose-wrapper.rose-transitioning {
  transform-origin: center;
  transition: transform 600ms cubic-bezier(.22,.9,.2,1), opacity 600ms ease;
  transform: scale(0.78);
  opacity: 0.08;
  pointer-events: none;
}
.nebula-chart-wrapper.nebula-zoomed {
  transform-origin: center;
  transition: transform 600ms cubic-bezier(.22,.9,.2,1);
  transform: scale(1.08);
  z-index: 60;
}
</style>

