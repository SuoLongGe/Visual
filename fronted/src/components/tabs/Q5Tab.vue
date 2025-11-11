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
            <button class="btn" @click="handleLoadChart" :disabled="loading">
              {{ loading ? '加载中...' : '加载职位排名数据' }}
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
          <button class="btn" @click="handleLoadIndustryRose" :disabled="roseLoading">
            {{ roseLoading ? '加载中...' : '加载行业玫瑰图数据' }}
          </button>

          <div v-if="roseError" class="error-message">
            <p>加载失败: {{ roseError }}</p>
          </div>

          <RoseNestedPolar
            v-if="roseData?.data?.industries"
            :data="roseData.data.industries"
            title="行业双环嵌套玫瑰图"
          />

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
import { ref } from 'vue'
import { useFetchData } from '@/utils/fetchData.js'
import { getJobRanking } from '@/api/industryApi.js'
import { getIndustryTrendRose } from '@/api/industryApi.js'
import MultiIconBarChart from '@/components/charts/MultiIconBarChart.vue'
import ContinuousProgressBarChart from '@/components/charts/ContinuousProgressBarChart.vue'
import RoseNestedPolar from '@/components/charts/RoseNestedPolar.vue'

const currentPage = ref(1)
const goPrev = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}
const goNext = () => {
  if (currentPage.value < 2) currentPage.value += 1
}

const { data: chartData, loading, error, execute } = useFetchData(getJobRanking)
const { data: roseData, loading: roseLoading, error: roseError, execute: executeRose } = useFetchData(getIndustryTrendRose)

const handleLoadChart = async () => {
  try {
    await execute()
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
</style>

