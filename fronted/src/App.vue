<template>
  <div class="app">
    <Header />
    <Dashboard />
  </div>
</template>

<script setup>
import Header from './components/Header.vue'
import Dashboard from './components/Dashboard.vue'
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>

