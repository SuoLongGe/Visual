<template>
  <div class="current-city-card">
    <div class="card-header">
      <h3>当前选中城市</h3>
    </div>
    <div v-if="!city" class="card-empty">
      <p>👈 点击左侧热力图中的城市方块查看详情</p>
    </div>
    <div v-else class="card-content">
      <div class="city-display">
        <div class="city-code">{{ city }}</div>
        <div class="city-name" v-if="cityName">{{ cityName }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  city: {
    type: String,
    default: null,
  },
  cityName: {
    type: String,
    default: null,
  },
  wordcloudTopN: {
    type: Number,
    default: 10,
  },
});
</script>

<style scoped>
.current-city-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  height: 120px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.15s ease-in-out;
}

.current-city-card:hover {
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}

.card-header {
  margin-bottom: 8px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1f2937;
  font-weight: 600;
}

.card-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  background: #f9fafb;
  transition: all 0.15s ease-in-out;
}

.card-empty:hover {
  border-color: #9ca3af;
  background: #f3f4f6;
}

.card-empty p {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
  text-align: center;
  line-height: 1.5;
}

.card-content {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.city-display {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.city-code {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.5px;
  line-height: 1;
}

.city-name {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}
</style>
