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

        <!-- 三维柱状图 -->
        <div v-if="activeTab === '3d-chart'" class="tab-content active">
          <Q3Tab />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Q3Tab from './tabs/Q3Tab.vue'

const activeTab = ref('overview')

const tabs = [
  { id: '3d-chart', label: 'Q3' }
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

