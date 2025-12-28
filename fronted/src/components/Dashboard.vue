<template>
  <div class="dashboard">
    <div class="container">
      <!-- 顶部导航区域：标题 + 标签 -->
      <div class="top-nav">
        <div class="nav-title" @click="switchTab('home')">
          <h1>多维度招聘数据分析</h1>
        </div>
        <div class="tabs-wrapper">
          <div class="tabs-container">
            <div class="tabs-background"></div>
            <button
              v-for="(tab, index) in tabs"
              :key="tab.id"
              :class="['tab-button', { active: activeTab === tab.id }]"
              @click="switchTab(tab.id)"
              :style="{ '--index': index }"
            >
              <span class="tab-label">{{ tab.label }}</span>
              <span class="tab-ripple" v-if="activeTab === tab.id"></span>
            </button>
            <!-- 活动指示器 -->
            <div class="active-indicator" :style="getIndicatorStyle()"></div>
          </div>
        </div>
      </div>

      <!-- 内容区域 - 玻璃态效果 -->
      <div class="content-wrapper">
      <div class="content-glass" :class="{ 'home-background': activeTab === 'home', 'no-card': activeTab === 'q5' }">
          <!-- 内容切换动画 -->
          <transition name="fade-slide" mode="out-in">
            <!-- 首页 -->
            <div v-if="activeTab === 'home'" key="home" class="tab-content">
              <HomeTab :on-switch-tab="switchTab" />
            </div>

            <!-- Q1 职位差异度分析 -->
            <div v-else-if="activeTab === 'q1'" key="q1" class="tab-content">
              <Q1Tab />
            </div>

            <!-- Q2 职位画像分析 -->
            <div v-else-if="activeTab === 'q2'" key="q2" class="tab-content">
              <Q2Tab />
            </div>

            <!-- 三维柱状图 -->
            <div v-else-if="activeTab === '3d-chart'" key="3d-chart" class="tab-content">
              <Q3Tab />
            </div>

                  <!-- Q4 城市等级热力图 -->
            <div v-else-if="activeTab === 'q4'" key="q4" class="tab-content active">
              <HeatmapTab />
            </div>

            <!-- Q5 行业发展动态与新兴职位 -->
            <div v-else-if="activeTab === 'q5'" key="q5" class="tab-content">
              <Q5Tab />
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import HomeTab from './tabs/HomeTab.vue'
import Q1Tab from './tabs/Q1Tab.vue'
import Q2Tab from './tabs/Q2Tab.vue'
import Q3Tab from './tabs/Q3Tab.vue'
import HeatmapTab from './tabs/HeatmapTab.vue'
import Q5Tab from './tabs/Q5Tab.vue'
  
const activeTab = ref('home')

const tabs = [
  { id: 'q1', label: '职位差异度分析' },
  { id: 'q2', label: '职位画像分析' },
  { id: '3d-chart', label: '薪资多维分析' },
  { id: 'q4', label: '地域数据分析' },
  { id: 'q5', label: '行业动态趋势' }
]

// 切换标签
const switchTab = (tabId) => {
  activeTab.value = tabId
}

// 计算活动指示器位置
const getIndicatorStyle = () => {
  const activeIndex = tabs.findIndex(tab => tab.id === activeTab.value)
  
  // 如果当前在首页，隐藏指示器
  if (activeTab.value === 'home' || activeIndex === -1) {
    return {
      opacity: '0',
      pointerEvents: 'none'
    }
  }
  
  const width = 100 / tabs.length
  const left = activeIndex * width
  
  return {
    width: `${width}%`,
    left: `${left}%`,
    opacity: '1'
  }
}
</script>

<style scoped>
.dashboard {
  padding: 0;
  position: relative;
  min-height: 100vh;
}

.container {
  max-width: 100%;
  margin: 0 auto;
  width: 100%;
}

/* 顶部导航 - 固定在浏览器顶部 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.nav-title {
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-title:hover {
  opacity: 0.8;
  transform: translateX(-2px);
}

.nav-title h1 {
  font-size: 1.4em;
  font-weight: 600;
  color: #2c3e50;
  text-shadow: none;
  white-space: nowrap;
  margin: 0;
  transition: color 0.3s ease;
}

.nav-title:hover h1 {
  color: #d97757;
}

/* 标签页容器 */
.tabs-wrapper {
  flex: 1;
  position: relative;
}

.tabs-container {
  position: relative;
  display: flex;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 6px;
  box-shadow: 
    0 2px 12px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.tabs-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(217, 119, 87, 0.1) 0%, rgba(217, 119, 87, 0.05) 100%);
  z-index: 0;
}

/* 标签按钮 */
.tab-button {
  position: relative;
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  color: rgba(44, 62, 80, 0.9);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.tab-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(217, 119, 87, 0.15);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.tab-button:hover::before {
  width: 300px;
  height: 300px;
}

.tab-button:hover {
  color: #d97757;
  transform: translateY(-2px);
}

.tab-button.active {
  color: #d97757;
  font-weight: 600;
}

.tab-label {
  position: relative;
  z-index: 1;
}

/* 活动指示器 */
.active-indicator {
  position: absolute;
  top: 6px;
  height: calc(100% - 12px);
  background: rgba(217, 119, 87, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  box-shadow: 
    0 2px 12px rgba(217, 119, 87, 0.3),
    0 0 0 1px rgba(217, 119, 87, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
  opacity: 1;
}

/* 波纹效果 */
.tab-ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(217, 119, 87, 0.25);
  transform: translate(-50%, -50%);
  animation: ripple 1.5s ease-out infinite;
}

@keyframes ripple {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

/* 内容区域 */
.content-wrapper {
  position: relative;
  margin-top: 88px; /* 为固定导航栏留出空间 */
  padding: 0 10px 10px;
  overflow: visible !important;
}

.content-glass {
  background: #ffffff;
  border-radius: 16px;
  padding: 15px;
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.06);
  min-height: calc(100vh - 200px);
  position: relative;
  overflow: visible;
}

.content-glass.home-background {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.content-glass::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(217, 119, 87, 0.3), 
    transparent
  );
  z-index: 0;
  pointer-events: none;
}

/* 当 Q5 页面显示时，去掉卡片背景让玫瑰图不被包裹 */
.content-glass.no-card {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 40px 0 !important;
  overflow: visible !important;
}
.content-glass.no-card::before { display: none !important; }

.tab-content {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 100%;
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
}

/* 内容切换动画 */
.fade-slide-enter-active {
  transition: opacity 0.3s ease-in;
}

.fade-slide-leave-active {
  transition: opacity 0.2s ease-out;
}

.fade-slide-enter-from {
  opacity: 0;
}

.fade-slide-leave-to {
  opacity: 0;
}

.fade-slide-enter-to,
.fade-slide-leave-from {
  opacity: 1 !important;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-glass {
    padding: 12px;
  }
  
  .tab-button {
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .nav-title h1 {
    font-size: 1.6em;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 0;
  }
  
  .content-wrapper {
    margin-top: 80px; /* 移动端导航栏可能更高 */
  }
  
  .tabs-container {
    flex-direction: column;
    gap: 6px;
    padding: 4px;
  }
  
  .tab-button {
    width: 100%;
    justify-content: flex-start;
    padding: 10px 16px;
  }
  
  .active-indicator {
    display: none;
  }
  
  .content-glass {
    padding: 10px;
    border-radius: 12px;
    min-height: calc(100vh - 180px);
  }
  
  .tab-label {
    flex: 1;
    text-align: left;
  }
  
  .nav-title h1 {
    font-size: 1.4em;
  }
}

@media (max-width: 480px) {
  .tab-button {
    font-size: 12px;
    padding: 8px 12px;
  }
  
  .content-glass {
    padding: 8px;
    min-height: calc(100vh - 160px);
  }
  
  .nav-title h1 {
    font-size: 1.2em;
  }
}

/* 深色模式支持（可选） */
@media (prefers-color-scheme: dark) {
  .content-glass {
    background: rgba(255, 255, 255, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .tabs-container {
    background: rgba(30, 30, 40, 0.3);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .active-indicator {
    background: rgba(255, 255, 255, 0.15);
  }
}
</style>
