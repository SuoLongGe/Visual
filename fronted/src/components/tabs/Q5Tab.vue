<template>
  <div class="q5-tab">
    <!-- 视图1：Math-Based 多维 Icon 柱状图 -->
    <div class="chart-section">
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useFetchData } from '@/utils/fetchData.js'
import { getJobRanking } from '@/api/industryApi.js'
import MultiIconBarChart from '@/components/charts/MultiIconBarChart.vue'

const { data: chartData, loading, error, execute } = useFetchData(getJobRanking)

const handleLoadChart = async () => {
  try {
    await execute()
  } catch (err) {
    console.error('加载职位排名数据失败:', err)
  }
}
</script>

<style scoped>
.q5-tab {
  width: 100%;
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

.chart-section {
  margin-bottom: 0;
}

.api-section {
  margin-top: 20px;
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
</style>

