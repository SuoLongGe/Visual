<template>
  <div class="app">
    <Dashboard />
  </div>
</template>

<script setup>
import Dashboard from './components/Dashboard.vue'
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: #000000;
  position: relative;
  overflow-x: hidden;
}

/* 添加微妙的网格背景 */
.app::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(217, 119, 87, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(217, 119, 87, 0.05) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
  z-index: 0;
}

.app::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 20% 50%, rgba(217, 119, 87, 0.08) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(217, 119, 87, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

/* 确保内容在背景之上 */
.app > * {
  position: relative;
  z-index: 1;
}
</style>

