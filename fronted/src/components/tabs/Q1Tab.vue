<template>
  <div class="q1-tab">
    <!-- 左侧：散点图（占大部分） -->
    <div class="left-section">
      <h2>散点图</h2>
      <p class="chart-description">
        此区域用于展示职位差异度的散点图可视化
      </p>
      <div class="chart-placeholder scatter-chart">
        <div class="placeholder-content">
          <p>散点图区域</p>
          <p class="placeholder-hint">此处将展示职位差异度的散点分布图</p>
        </div>
      </div>
    </div>
    
    <!-- 右侧：上下排列两个图 -->
    <div class="right-section">
      <!-- 雷达图 -->
      <div class="right-chart radar-chart">
        <h3>雷达图</h3>
        <p class="chart-description-small">
          此区域用于展示职位多维度特征的雷达图
        </p>
        <div class="chart-placeholder">
          <div class="placeholder-content">
            <p>雷达图区域</p>
            <p class="placeholder-hint">此处将展示职位的多维度特征雷达图</p>
          </div>
        </div>
      </div>
      
      <!-- 环状图（中心有数字） -->
      <div class="right-chart ring-chart">
        <h3>环状图</h3>
        <p class="chart-description-small">
          此区域用于展示中心有数字的环状图
        </p>
        <div class="chart-placeholder">
          <div class="placeholder-content">
            <p>环状图区域</p>
            <p class="placeholder-hint">此处将展示中心有数字的环状图</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Q1 职位差异度分析标签页
// 包含三个视图：左侧散点图，右侧雷达图和环状图
</script>

<style scoped>
.q1-tab {
  display: flex;
  gap: 30px;
  align-items: stretch;
  min-height: 600px;
}

.q1-tab h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.q1-tab h3 {
  margin-bottom: 15px;
  color: #2c3e50;
  font-size: 18px;
}

.chart-description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
}

.chart-description-small {
  margin-bottom: 15px;
  color: #666;
  line-height: 1.5;
  font-size: 14px;
}

/* 左侧区域：散点图（占大部分） */
.left-section {
  flex: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.scatter-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 右侧区域：上下排列两个图 */
.right-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.right-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.radar-chart {
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 20px;
  box-sizing: border-box;
}

.ring-chart {
  padding-top: 20px;
  box-sizing: border-box;
}

/* 图表占位区域 */
.chart-placeholder {
  flex: 1;
  border: 2px dashed #d0d0d0;
  border-radius: 8px;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

.placeholder-content {
  text-align: center;
  color: #999;
}

.placeholder-content p {
  margin: 5px 0;
}

.placeholder-content p:first-child {
  font-size: 18px;
  font-weight: 600;
  color: #666;
}

.placeholder-hint {
  font-size: 14px;
  color: #aaa;
}

/* 响应式设计：小屏幕时改为纵向布局 */
@media (max-width: 1200px) {
  .q1-tab {
    flex-direction: column;
  }
  
  .right-section {
    flex-direction: row;
    gap: 20px;
  }
  
  .radar-chart {
    border-bottom: none;
    border-right: 2px solid #e0e0e0;
    padding-bottom: 0;
    padding-right: 20px;
  }
  
  .ring-chart {
    padding-top: 0;
    padding-left: 20px;
  }
}
</style>

