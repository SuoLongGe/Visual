<template>
  <div class="home-tab">
    <!-- 词云背景 -->
    <WordCloudChart 
      v-if="wordcloudData && Object.keys(wordcloudData).length > 0"
      :multi-data="wordcloudData"
      :width="wordcloudWidth"
      :height="wordcloudHeight"
      class="wordcloud-background"
    />
    
    <!-- 主标题区域 -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="main-title">
          <span class="title-line">职数洞见</span>
          <span class="title-subtitle">招聘数据智能分析平台</span>
        </h1>
        <p class="hero-description">
          深度挖掘招聘市场数据，洞察行业趋势，助力职业决策
        </p>
      </div>
      <div class="hero-decoration">
        <div class="floating-shape shape-1"></div>
        <div class="floating-shape shape-2"></div>
        <div class="floating-shape shape-3"></div>
      </div>
    </div>

    <!-- 核心数据指标卡片 -->
    <div class="stats-grid" v-if="!loading && overviewData">
      <div class="stat-card" v-for="(stat, index) in stats" :key="index" :style="{ '--delay': index * 0.1 + 's' }">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">
            <span class="number" :data-target="stat.value">{{ animatedValues[index] || 0 }}</span>
            <span class="unit" v-if="stat.unit">{{ stat.unit }}</span>
          </div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-glow"></div>
      </div>
    </div>

    <!-- 数据预览区域 -->
    <div class="preview-section" v-if="!loading && overviewData">
      <div class="preview-card" @click="switchTab('q1')">
        <div class="preview-header">
          <span class="preview-icon">📊</span>
          <h3>职位差异度分析</h3>
        </div>
        <p class="preview-desc">对比不同职位的薪资、经验、学历要求差异</p>
        <div class="preview-arrow">→</div>
      </div>

      <div class="preview-card" @click="switchTab('q2')">
        <div class="preview-header">
          <span class="preview-icon">👤</span>
          <h3>职位画像分析</h3>
        </div>
        <p class="preview-desc">多维度分析职位特征，构建完整职位画像</p>
        <div class="preview-arrow">→</div>
      </div>

      <div class="preview-card" @click="switchTab('3d-chart')">
        <div class="preview-header">
          <span class="preview-icon">📈</span>
          <h3>薪资多维分析</h3>
        </div>
        <p class="preview-desc">3D可视化薪资分布，探索多维度薪资规律</p>
        <div class="preview-arrow">→</div>
      </div>

      <div class="preview-card" @click="switchTab('q5')">
        <div class="preview-header">
          <span class="preview-icon">🚀</span>
          <h3>行业动态趋势</h3>
        </div>
        <p class="preview-desc">追踪行业发展，发现新兴职位机会</p>
        <div class="preview-arrow">→</div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>正在加载数据...</p>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error-container">
      <p>数据加载失败，请稍后重试</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import WordCloudChart from '@/components/charts/WordCloudChart.vue'

const props = defineProps({
  onSwitchTab: {
    type: Function,
    required: true
  }
})

const loading = ref(false)
const error = ref(null)
const overviewData = ref(null)
const wordcloudData = ref({})
const animatedValues = ref([0, 0, 0, 0])
const wordcloudWidth = ref(window.innerWidth)
const wordcloudHeight = ref(window.innerHeight)

// 写死的概览数据
const staticOverviewData = {
  total_records: 430394,
  statistics: {
    total_cities: 371,
    total_companies: 267243,
    salary_range: {
      min: 1,
      max: 260,
      median: 15
    }
  }
}

// 写死的词云数据
const staticWordcloudData = {
  jobs: [
    { name: 'Java开发工程师', value: 70, count: 5000 },
    { name: 'Python开发工程师', value: 65, count: 4500 },
    { name: '前端开发工程师', value: 60, count: 4000 },
    { name: '产品经理', value: 55, count: 3500 },
    { name: 'UI设计师', value: 50, count: 3000 },
    { name: '数据分析师', value: 48, count: 2800 },
    { name: '测试工程师', value: 45, count: 2500 },
    { name: '运营专员', value: 42, count: 2200 },
    { name: '销售经理', value: 40, count: 2000 },
    { name: '项目经理', value: 38, count: 1800 },
    { name: 'Android开发', value: 35, count: 1500 },
    { name: 'iOS开发', value: 33, count: 1300 },
    { name: '算法工程师', value: 30, count: 1100 },
    { name: '运维工程师', value: 28, count: 900 },
    { name: '架构师', value: 25, count: 700 },
    { name: '技术总监', value: 22, count: 500 },
    { name: '市场专员', value: 20, count: 400 },
    { name: 'HR专员', value: 18, count: 300 },
    { name: '财务专员', value: 16, count: 250 },
    { name: '行政助理', value: 15, count: 200 },
    { name: '商务拓展', value: 14, count: 180 },
    { name: '客户经理', value: 13, count: 150 },
    { name: '内容运营', value: 12, count: 120 },
    { name: '新媒体运营', value: 11, count: 100 },
    { name: '平面设计师', value: 10, count: 80 },
    { name: '交互设计师', value: 10, count: 75 },
    { name: '视觉设计师', value: 10, count: 70 },
    { name: '后端开发', value: 10, count: 65 },
    { name: '全栈开发', value: 10, count: 60 },
    { name: 'PHP开发', value: 10, count: 55 },
    { name: 'C++开发', value: 10, count: 50 },
    { name: 'Go开发', value: 10, count: 45 },
    { name: 'Node.js开发', value: 10, count: 40 },
    { name: 'React开发', value: 10, count: 35 },
    { name: 'Vue开发', value: 10, count: 30 },
    { name: 'Angular开发', value: 10, count: 25 },
    { name: '小程序开发', value: 10, count: 20 }
  ],
  education: [
    { name: '本科', value: 60, count: 200000 },
    { name: '大专', value: 50, count: 150000 },
    { name: '硕士', value: 45, count: 50000 },
    { name: '高中/中专', value: 35, count: 20000 },
    { name: '博士', value: 30, count: 5000 },
    { name: '初中', value: 25, count: 3000 },
    { name: '小学', value: 20, count: 1000 },
    { name: '博士后', value: 15, count: 500 }
  ],
  experience: [
    { name: '1-3年', value: 60, count: 150000 },
    { name: '3-5年', value: 55, count: 100000 },
    { name: '1年以下', value: 50, count: 80000 },
    { name: '5-7年', value: 45, count: 50000 },
    { name: '应届毕业生', value: 40, count: 30000 },
    { name: '7-10年', value: 35, count: 15000 },
    { name: '10年以上', value: 30, count: 5000 },
    { name: '无经验', value: 25, count: 2000 }
  ],
  salary: [
    { name: '15-25K', value: 60, count: 100000 },
    { name: '10-15K', value: 55, count: 80000 },
    { name: '25-35K', value: 50, count: 60000 },
    { name: '5-10K', value: 45, count: 50000 },
    { name: '35-50K', value: 40, count: 30000 },
    { name: '0-5K', value: 35, count: 20000 },
    { name: '50K+', value: 30, count: 10000 }
  ],
  city: [
    { name: '北京', value: 70, count: 50000 },
    { name: '上海', value: 65, count: 45000 },
    { name: '深圳', value: 60, count: 40000 },
    { name: '杭州', value: 55, count: 35000 },
    { name: '广州', value: 50, count: 30000 },
    { name: '成都', value: 45, count: 25000 },
    { name: '南京', value: 40, count: 20000 },
    { name: '武汉', value: 38, count: 18000 },
    { name: '西安', value: 35, count: 15000 },
    { name: '苏州', value: 33, count: 13000 },
    { name: '重庆', value: 30, count: 11000 },
    { name: '天津', value: 28, count: 9000 },
    { name: '长沙', value: 25, count: 7000 },
    { name: '郑州', value: 22, count: 5000 },
    { name: '青岛', value: 20, count: 4000 },
    { name: '大连', value: 18, count: 3000 },
    { name: '厦门', value: 16, count: 2500 },
    { name: '合肥', value: 15, count: 2000 },
    { name: '济南', value: 14, count: 1800 },
    { name: '福州', value: 13, count: 1500 },
    { name: '无锡', value: 12, count: 1200 },
    { name: '宁波', value: 11, count: 1000 },
    { name: '东莞', value: 10, count: 800 },
    { name: '佛山', value: 10, count: 700 },
    { name: '昆明', value: 10, count: 600 },
    { name: '沈阳', value: 10, count: 500 },
    { name: '石家庄', value: 10, count: 400 },
    { name: '哈尔滨', value: 10, count: 300 },
    { name: '长春', value: 10, count: 250 },
    { name: '南昌', value: 10, count: 200 },
    { name: '太原', value: 10, count: 150 },
    { name: '贵阳', value: 10, count: 120 },
    { name: '南宁', value: 10, count: 100 },
    { name: '海口', value: 10, count: 80 },
    { name: '兰州', value: 10, count: 60 },
    { name: '银川', value: 10, count: 50 },
    { name: '西宁', value: 10, count: 40 },
    { name: '乌鲁木齐', value: 10, count: 30 },
    { name: '拉萨', value: 10, count: 20 }
  ],
  company_type: [
    { name: '互联网/IT', value: 60, count: 100000 },
    { name: '金融/银行', value: 55, count: 80000 },
    { name: '制造业', value: 50, count: 60000 },
    { name: '房地产', value: 45, count: 50000 },
    { name: '教育/培训', value: 40, count: 40000 },
    { name: '医疗/健康', value: 35, count: 30000 },
    { name: '零售/贸易', value: 30, count: 20000 },
    { name: '物流/运输', value: 28, count: 15000 },
    { name: '能源/化工', value: 25, count: 12000 },
    { name: '建筑/工程', value: 22, count: 10000 },
    { name: '媒体/广告', value: 20, count: 8000 },
    { name: '餐饮/酒店', value: 18, count: 6000 },
    { name: '咨询/服务', value: 16, count: 5000 },
    { name: '电子/通信', value: 15, count: 4000 },
    { name: '汽车/机械', value: 14, count: 3000 },
    { name: '服装/纺织', value: 13, count: 2500 },
    { name: '食品/饮料', value: 12, count: 2000 },
    { name: '旅游/娱乐', value: 11, count: 1500 },
    { name: '农业/林业', value: 10, count: 1000 },
    { name: '环保/新能源', value: 10, count: 800 },
    { name: '航空航天', value: 10, count: 600 },
    { name: '船舶/海洋', value: 10, count: 400 },
    { name: '矿业/冶金', value: 10, count: 300 },
    { name: '电力/水利', value: 10, count: 250 },
    { name: '公共事业', value: 10, count: 200 },
    { name: '非营利组织', value: 10, count: 150 },
    { name: '政府机构', value: 10, count: 100 },
    { name: '科研院所', value: 10, count: 80 },
    { name: '其他', value: 10, count: 50 }
  ]
}

// 计算统计数据
const stats = computed(() => {
  if (!overviewData.value) return []
  
  const data = overviewData.value.statistics || {}
  const salary = data.salary_range || {}
  
  return [
    {
      icon: '💼',
      label: '总职位数',
      value: overviewData.value.total_records || 0,
      unit: '个',
      format: 'number'
    },
    {
      icon: '💰',
      label: '平均薪资',
      value: salary.median || 0,
      unit: 'K',
      format: 'number'
    },
    {
      icon: '🏙️',
      label: '覆盖城市',
      value: data.total_cities || 0,
      unit: '座',
      format: 'number'
    },
    {
      icon: '🏢',
      label: '合作企业',
      value: data.total_companies || 0,
      unit: '家',
      format: 'number'
    }
  ]
})

// 数字动画
const animateNumber = (index, target) => {
  const duration = 2000
  const steps = 60
  const increment = target / steps
  let current = 0
  const timer = setInterval(() => {
    current += increment
    if (current >= target) {
      current = target
      clearInterval(timer)
    }
    animatedValues.value[index] = Math.floor(current)
  }, duration / steps)
}

// 更新词云尺寸
const updateWordcloudSize = () => {
  wordcloudWidth.value = window.innerWidth
  wordcloudHeight.value = window.innerHeight
}

// 初始化数据（使用写死的数据，无需API调用）
const initData = () => {
  // 直接使用写死的数据
  overviewData.value = staticOverviewData
  wordcloudData.value = staticWordcloudData
  
  // 更新词云尺寸
  updateWordcloudSize()
  
  // 启动数字动画
  nextTick(() => {
    stats.value.forEach((stat, index) => {
      setTimeout(() => {
        animateNumber(index, stat.value)
      }, index * 200)
    })
  })
}

// 窗口大小改变时更新词云尺寸
let resizeTimer = null
const handleResize = () => {
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    updateWordcloudSize()
  }, 300)
}

// 切换标签
const switchTab = (tabId) => {
  props.onSwitchTab(tabId)
}

onMounted(() => {
  // 直接初始化数据，无需等待API
  initData()
  window.addEventListener('resize', handleResize)
  updateWordcloudSize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeTimer) clearTimeout(resizeTimer)
})
</script>

<style scoped>
.home-tab {
  min-height: calc(100vh - 200px);
  padding: 20px;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.wordcloud-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
}

/* 主标题区域 */
.hero-section {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  padding: 40px 0;
}

.hero-content {
  position: relative;
  z-index: 2;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  padding: 30px;
  border-radius: 20px;
  border: 1px solid rgba(217, 119, 87, 0.2);
}

.main-title {
  margin: 0 0 15px 0;
  font-size: 3.5em;
  font-weight: 700;
  background: linear-gradient(135deg, #d97757 0%, #ff8c69 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 40px rgba(217, 119, 87, 0.5);
  animation: titleGlow 3s ease-in-out infinite;
}

@keyframes titleGlow {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.2); }
}

.title-subtitle {
  display: block;
  font-size: 0.4em;
  font-weight: 300;
  margin-top: 10px;
  opacity: 0.8;
}

.hero-description {
  font-size: 1.2em;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  letter-spacing: 1px;
}

/* 装饰元素 */
.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  pointer-events: none;
}

.floating-shape {
  position: absolute;
  border: 2px solid rgba(217, 119, 87, 0.3);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.shape-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-30px) scale(1.1);
    opacity: 0.5;
  }
}

/* 数据指标卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(217, 119, 87, 0.2);
  border-radius: 16px;
  padding: 25px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideInUp 0.6s ease-out both;
  animation-delay: var(--delay);
  z-index: 1;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card:hover {
  transform: translateY(-8px);
  border-color: rgba(217, 119, 87, 0.6);
  box-shadow: 0 10px 40px rgba(217, 119, 87, 0.3);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #d97757, transparent);
  opacity: 0;
  transition: opacity 0.4s;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(217, 119, 87, 0.2) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
  pointer-events: none;
}

.stat-card:hover .stat-glow {
  width: 300px;
  height: 300px;
}

.stat-icon {
  font-size: 2.5em;
  margin-bottom: 15px;
  filter: drop-shadow(0 0 10px rgba(217, 119, 87, 0.5));
}

.stat-content {
  position: relative;
  z-index: 1;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.number {
  font-size: 2.5em;
  font-weight: 700;
  color: #d97757;
  text-shadow: 0 0 20px rgba(217, 119, 87, 0.5);
  font-variant-numeric: tabular-nums;
}

.unit {
  font-size: 1.2em;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
}

.stat-label {
  font-size: 1em;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 400;
}

/* 预览卡片区域 */
.preview-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 40px;
}

.preview-card {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(217, 119, 87, 0.2);
  border-radius: 16px;
  padding: 25px;
  position: relative;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 1;
}

.preview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(217, 119, 87, 0.1), transparent);
  transition: left 0.6s;
}

.preview-card:hover::before {
  left: 100%;
}

.preview-card:hover {
  transform: translateX(10px);
  border-color: rgba(217, 119, 87, 0.6);
  box-shadow: 0 10px 40px rgba(217, 119, 87, 0.3);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.preview-icon {
  font-size: 2em;
  filter: drop-shadow(0 0 10px rgba(217, 119, 87, 0.5));
}

.preview-header h3 {
  margin: 0;
  font-size: 1.3em;
  color: #d97757;
  font-weight: 600;
}

.preview-desc {
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  margin: 0 0 15px 0;
  font-size: 0.95em;
}

.preview-arrow {
  position: absolute;
  right: 25px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 2em;
  color: #d97757;
  opacity: 0;
  transition: all 0.4s;
}

.preview-card:hover .preview-arrow {
  opacity: 1;
  transform: translateY(-50%) translateX(-5px);
}

/* 加载和错误状态 */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: rgba(255, 255, 255, 0.7);
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(217, 119, 87, 0.2);
  border-top-color: #d97757;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-title {
    font-size: 2.5em;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .preview-section {
    grid-template-columns: 1fr;
  }
  
  .stat-card,
  .preview-card {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 2em;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .number {
    font-size: 2em;
  }
}
</style>

