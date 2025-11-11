
<template>
  <div class="dashboard">
    <div class="container">
      <!-- 标签页导航 -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="content">

        <!-- Q1 职位差异度分析 -->
        <div v-if="activeTab === 'q1'" class="tab-content active">
          <Q1Tab />
        </div>

        <!-- 三维柱状图 -->
        <div v-if="activeTab === '3d-chart'" class="tab-content active">
          <Q3Tab />
        </div>
        
                <!-- Q5 行业发展动态与新兴职位 -->
        <div v-if="activeTab === 'q5'" class="tab-content active">
          <Q5Tab />
        </div>
        
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Q1Tab from './tabs/Q1Tab.vue'
import Q3Tab from './tabs/Q3Tab.vue'
import Q5Tab from './tabs/Q5Tab.vue'
  
const activeTab = ref('q1')

const tabs = [
  { id: 'q1', label: 'Q1' },
  { id: '3d-chart', label: 'Q3' },
  { id: 'q5', label: 'Q5' }
]
</script>

<style scoped>
.dashboard {
  padding: 0 20px 40px;
}

.container {
  margin: 0 auto;
}

.content {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  min-height: 500px;
}
</style>


<template>
  <div class="dashboard">
    <div class="container">
      <!-- 标签页导航 -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="content">

        <!-- Q1 职位差异度分析 -->
        <div v-if="activeTab === 'q1'" class="tab-content active">
          <Q1Tab />
        </div>

        <!-- 三维柱状图 -->
        <div v-if="activeTab === '3d-chart'" class="tab-content active">
          <Q3Tab />
        </div>
        
                <!-- Q5 行业发展动态与新兴职位 -->
        <div v-if="activeTab === 'q5'" class="tab-content active">
          <Q5Tab />
        </div>
        
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Q1Tab from './tabs/Q1Tab.vue'
import Q3Tab from './tabs/Q3Tab.vue'
import Q5Tab from './tabs/Q5Tab.vue'
  
const activeTab = ref('q1')

const tabs = [
  { id: 'q1', label: 'Q1' },
  { id: '3d-chart', label: 'Q3' },
  { id: 'q5', label: 'Q5' }
]
</script>

<style scoped>
.dashboard {
  padding: 0 20px 40px;
}

.container {
  margin: 0 auto;
}

.content {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  min-height: 500px;
}
</style>

