<template>
  <div class="q3-tab">
    <!-- 视图1：三维柱状图 -->
    <div class="chart-section left-section">
      <h2>三维柱状对比图</h2>
      <p class="chart-description">
        展示不同工作经验与学历组合下的平均薪资分布
        X轴：工作经验 | Y轴：学历层次 | Z轴：平均薪资
        <br/>
        <strong>💡 提示：点击3D图表中的柱体，将自动加载对应的箱线图分析</strong>
      </p>
      
      <div class="api-section">
        <button class="btn" @click="handleLoad3DChart" :disabled="loading">
          {{ loading ? '加载中...' : '加载三维柱状图' }}
        </button>
        
        <Chart3D 
          :data="chartData?.data"
          :loading="loading"
          :error="error"
          @bar-click="handleBarClick"
        />
      </div>
    </div>
    
    <!-- 视图2：箱线图 -->
    <div class="boxplot-section right-section">
      <h2>箱线图分析</h2>
      <p class="chart-description">
        在选定条件下（特定 experience × education）展示不同城市与公司类型之间的薪资分布情况
      </p>
      
      <BoxplotChart 
        :experience="selectedExperience"
        :education="selectedEducation"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useFetchData } from '@/utils/fetchData.js'
import { get3DSalaryData } from '@/api/salary3dApi.js'
import Chart3D from '@/components/charts/Chart3D.vue'
import BoxplotChart from '@/components/charts/BoxplotChart.vue'

const { data: chartData, loading, error, execute } = useFetchData(get3DSalaryData)
const selectedExperience = ref('')
const selectedEducation = ref('')

const handleLoad3DChart = async () => {
  try {
    await execute()
    // 重置选择
    selectedExperience.value = ''
    selectedEducation.value = ''
  } catch (err) {
    console.error('加载3D图表失败:', err)
  }
}

const handleBarClick = (data) => {
  // 从3D图表点击事件中获取经验和学历
  selectedExperience.value = data.experience
  selectedEducation.value = data.education
  
  console.log('点击了柱体:', data)
  
  // 可以在这里添加提示或动画效果
  // 例如：显示一个提示消息，说明已选择该组合
}
</script>

<style scoped>
.q3-tab {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

.q3-tab h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.chart-description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
}

.chart-description strong {
  color: #5470c6;
  font-weight: 600;
}

.left-section {
  flex: 1;
  min-width: 0; /* 防止flex子项溢出 */
}

.right-section {
  flex: 1;
  min-width: 0; /* 防止flex子项溢出 */
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

.boxplot-section {
  padding-top: 0;
  border-top: none;
  border-left: 2px solid #e0e0e0;
  padding-left: 30px;
}

/* 响应式设计：小屏幕时改为纵向布局 */
@media (max-width: 1200px) {
  .q3-tab {
    flex-direction: column;
  }
  
  .boxplot-section {
    border-left: none;
    border-top: 2px solid #e0e0e0;
    padding-left: 0;
    padding-top: 30px;
    margin-top: 30px;
  }
}
</style>

