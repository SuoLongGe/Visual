<template>
  <div class="q3-tab">
    <!-- 顶部：三维柱状图和箱线图并排 -->
    <div class="top-section">
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
    
    <!-- 视图3：交互式平行坐标图 + 散点图矩阵 -->
    <div class="radar-section full-width">
      <h2>交互式多维可视化</h2>
      <p class="chart-description">
        <strong>🎯 参考 FLINAView 设计的多视图协同可视化系统</strong>
        <br/>• <strong>平行坐标图</strong>：展示6个维度的完整关系，支持在任意轴上拖动刷选数据
        <br/>• <strong>散点图矩阵</strong>：展示关键维度对的分布，支持框选数据点
        <br/>• <strong>视图联动</strong>：所有视图同步高亮和过滤，鼠标悬停查看详情
        <br/>• <strong>交互操作</strong>：在轴上拖动刷选 | 在散点图上框选 | 点击选择单个数据 | 清除选择按钮
      </p>
      
      <div class="api-section">
        <InteractiveParallelCoordinates 
          :data="parallelData?.data"
          :loading="parallelLoading"
          :error="parallelError"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFetchData } from '@/utils/fetchData.js'
import { get3DSalaryData, getParallelCoordinatesData } from '@/api/salary3dApi.js'
import Chart3D from '@/components/charts/Chart3D.vue'
import BoxplotChart from '@/components/charts/BoxplotChart.vue'
import InteractiveParallelCoordinates from '@/components/charts/InteractiveParallelCoordinates.vue'

const { data: chartData, loading, error, execute } = useFetchData(get3DSalaryData)
const { data: parallelData, loading: parallelLoading, error: parallelError, execute: executeParallel } = useFetchData(getParallelCoordinatesData)
const selectedExperience = ref('')
const selectedEducation = ref('')

// 组件挂载时自动加载数据
onMounted(async () => {
  try {
    console.log('Q3Tab 开始加载数据...')
    // 并行加载所有图表的数据
    const results = await Promise.all([
      execute(),
      executeParallel()
    ])
    console.log('Q3Tab 数据加载完成:', {
      chart3D: chartData.value,
      parallel: parallelData.value
    })
    // 重置选择
    selectedExperience.value = ''
    selectedEducation.value = ''
  } catch (err) {
    console.error('自动加载图表数据失败:', err)
  }
})

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
  flex-direction: column;
  gap: 30px;
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

.q3-tab .top-section {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

.boxplot-section {
  padding-top: 0;
  border-top: none;
  border-left: 2px solid #e0e0e0;
  padding-left: 30px;
}

.radar-section {
  width: 100%;
  margin-top: 30px;
  padding-top: 30px;
  border-top: 2px solid #e0e0e0;
  min-height: 800px;
}

.radar-section.full-width {
  width: 100%;
}


/* 响应式设计：小屏幕时改为纵向布局 */
@media (max-width: 1200px) {
  .q3-tab .top-section {
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

