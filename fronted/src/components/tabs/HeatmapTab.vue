<template>
  <section class="heatmap-tab">
    <header class="tab-header">
      <div>
        <h2>城市等级矩形热力图</h2>
        <p class="subtitle">按城市等级 × 公司类型，洞察多维指标变化</p>
      </div>
      <div class="filters">
        <div class="filter-group">
          <label>城市等级</label>
          <select v-model="selectedTier" @change="handleFilterChange">
            <option
              v-for="tier in tierOptions"
              :key="tier.value"
              :value="tier.value"
            >
              {{ tier.label }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label>度量指标</label>
          <select v-model="selectedMetric" @change="handleFilterChange">
            <option
              v-for="metric in metricOptions"
              :key="metric.value"
              :value="metric.value"
            >
              {{ metric.label }}
            </option>
          </select>
        </div>
      </div>
    </header>

    <div class="info-bar" v-if="heatmapPayload">
      <div class="info-item">
        <span class="label">标题</span>
        <span class="value">{{ heatmapPayload.title }}</span>
      </div>
      <div class="info-item">
        <span class="label">城市等级</span>
        <span class="value">{{ heatmapPayload.tierName }}（{{ heatmapPayload.cityCount }} 座城市）</span>
      </div>
      <div class="info-item">
        <span class="label">提示</span>
        <span class="value">“其他”类别使用灰色显示，数值已归一化处理以避免影响具体类别的颜色对比。</span>
      </div>
      <div class="info-item" v-if="selectedCityCode">
        <span class="label">当前城市</span>
        <span class="value">{{ selectedCityCode }} 的行业词云（前 {{ wordcloudTopN }} 个）</span>
      </div>
    </div>

    <div class="heatmap-content">
      <div class="heatmap-panel">
        <CityTierHeatmap
          :tier="selectedTier"
          :metric="selectedMetric"
          dimension-label="公司类型"
          :dataset="heatmapPayload"
          :loading="loading"
          :error="error"
          :auto-fetch="false"
          @city-click="handleCityClick"
        />
      </div>
      <div class="wordcloud-panel">
        <CityWordcloud
          :city="selectedCityCode"
          :auto-fetch="true"
          :top-n="wordcloudTopN"
        />
        <div class="region-similarity-wrapper">
          <RegionSimilarityChart
            :city="selectedCityCode"
            :auto-fetch="true"
            :top-similar="5"
          />
        </div>
      </div>
    </div>

    <div class="bubble-section">
      <IndustryBubbleChart :auto-fetch="true" />
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue';
import CityTierHeatmap from '../charts/CityTierHeatmap.vue';
import CityWordcloud from '../charts/CityWordcloud.vue';
import RegionSimilarityChart from '../charts/RegionSimilarityChart.vue';
import IndustryBubbleChart from '../charts/IndustryBubbleChart.vue';
import { useHeatmapData } from '../../composables/useHeatmapData';

const tierOptions = [
  { value: 'first_tier', label: '一线城市' },
  { value: 'second_tier', label: '二线城市' },
  { value: 'third_tier', label: '三线城市' },
  { value: 'other', label: '其他城市' },
];

const metricOptions = [
  { value: 'job_count', label: '职位数量' },
  { value: 'industry_ratio', label: '行业占比' },
  { value: 'location_quotient', label: '区位商' },
];

const selectedTier = ref('first_tier');
const selectedMetric = ref('job_count');
const selectedCityCode = ref(null);
const wordcloudTopN = ref(10);

const { loading, error, heatmapPayload, loadHeatmap } = useHeatmapData();

const fetchData = () => {
  loadHeatmap({
    tier: selectedTier.value,
    metric: selectedMetric.value,
    dimension_y: 'company_type',
  });
};

const handleFilterChange = () => {
  fetchData();
};

const handleCityClick = (payload) => {
  if (!payload || !payload.city) return;
  selectedCityCode.value = payload.city;
};

watch(
  () => [selectedTier.value, selectedMetric.value],
  () => {
    fetchData();
  },
  { immediate: true },
);
</script>

<style scoped>
.heatmap-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.tab-header h2 {
  margin: 0;
  font-size: 22px;
  color: #111827;
}

.subtitle {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.filters {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.filter-group label {
  color: #4b5563;
  font-weight: 500;
}

.filter-group select {
  min-width: 160px;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background-color: #fff;
  color: #111827;
}

.info-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}

.label {
  color: #6b7280;
}

.value {
  color: #111827;
  font-weight: 500;
}

.heatmap-content {
  display: grid;
  grid-template-columns: minmax(0, 2.2fr) minmax(0, 1.2fr);
  gap: 16px;
  align-items: stretch;
}

.heatmap-panel,
.wordcloud-panel {
  min-height: 360px;
}

.region-similarity-wrapper {
  margin-top: 12px;
}

.bubble-section {
  margin-top: 18px;
}

.bubble-section :deep(.industry-bubble-container) {
  /* 让气泡图容器自动撑满宽度，高度由自身 min-height 控制 */
}

@media (max-width: 1024px) {
  .heatmap-content {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

