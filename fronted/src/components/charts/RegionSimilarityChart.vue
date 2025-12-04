<template>
  <div class="region-similarity-container">
    <div class="region-similarity-header">
      <div>
        <h3>相似地域招聘画像</h3>
        <p class="subtitle">
          基于行业分布计算城市间的相似度，用于识别招聘结构相近的城市集群。
        </p>
      </div>
    </div>

    <div v-if="errorToShow" class="region-similarity-error">
      {{ errorToShow }}
    </div>

    <div v-else class="region-similarity-chart-wrapper">
      <div v-if="loadingToShow" class="region-similarity-loading">加载中...</div>
      <div v-else-if="!hasData" class="region-similarity-empty">
        <span v-if="!city">
          左侧：点击矩形热力图中的某个城市方块，这里将展示与该城市招聘画像最相似的其它城市。
        </span>
        <span v-else>暂无相似地域数据</span>
      </div>
      <div v-else ref="chartRef" class="region-similarity-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import { useRegionProfile } from '../../composables/useRegionProfile';

const props = defineProps({
  city: {
    type: String,
    default: null,
  },
  autoFetch: {
    type: Boolean,
    default: true,
  },
  topSimilar: {
    type: Number,
    default: 5,
  },
});

const chartRef = ref(null);
let chartInstance = null;

const { loading, error, profile, loadRegionProfile } = useRegionProfile();

const loadingToShow = computed(() => loading.value);
const errorToShow = computed(() => error.value);

const similarRegions = computed(() => profile.value?.similar_regions ?? []);
const hasData = computed(
  () => !!profile.value && Array.isArray(similarRegions.value) && similarRegions.value.length > 0,
);

// 检查容器是否有有效尺寸
const hasValidSize = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

const renderChart = () => {
  if (!hasData.value) return;

  const el = chartRef.value;
  if (!el || !hasValidSize(el)) {
    // 容器还未就绪，稍后重试
    setTimeout(() => {
      if (hasData.value) {
        renderChart();
      }
    }, 100);
    return;
  }

  // 每次重绘前销毁旧实例，避免残留状态
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }

  chartInstance = echarts.init(el);

  const data = [...similarRegions.value].sort(
    (a, b) => Number(b.similarity) - Number(a.similarity),
  );

  const cities = data.map((d) => d.city);
  const values = data.map((d) => Number(d.similarity));

  chartInstance.setOption(
    {
      grid: {
        top: 40,
        left: 80,
        right: 40,
        bottom: 40,
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: 1,
        axisLabel: {
          formatter: (val) => (val * 100).toFixed(0) + '%',
        },
      },
      yAxis: {
        type: 'category',
        data: cities,
        axisLabel: {
          fontSize: 11,
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) =>
          `城市：${params.name}<br/>相似度：${(params.value * 100).toFixed(1)}%`,
      },
      series: [
        {
          type: 'bar',
          data: values,
          barWidth: 18,
          itemStyle: {
            borderRadius: [4, 4, 4, 4],
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#3b82f6' },
              { offset: 1, color: '#93c5fd' },
            ]),
          },
          label: {
            show: true,
            position: 'right',
            formatter: (params) => (params.value * 100).toFixed(1) + '%',
            color: '#374151',
            fontSize: 11,
          },
        },
      ],
    },
    true,
  );
};

const fetchData = () => {
  if (!props.autoFetch || !props.city) return;
  loadRegionProfile(props.city, props.topSimilar).then(() => {
    nextTick(() => {
      renderChart();
    });
  });
};

watch(
  () => props.city,
  (newCity) => {
    if (newCity && props.autoFetch) {
      fetchData();
    }
  },
  { immediate: true },
);

watch(
  () => similarRegions.value,
  (newVal) => {
    if (newVal && newVal.length) {
      nextTick(() => {
        renderChart();
      });
    }
  },
  { deep: true },
);

onMounted(() => {
  if (props.autoFetch && props.city) {
    fetchData();
  } else if (hasData.value) {
    renderChart();
  }
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
.region-similarity-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px 18px 18px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  min-height: 260px;
  display: flex;
  flex-direction: column;
}

.region-similarity-header {
  margin-bottom: 8px;
}

.region-similarity-header h3 {
  margin: 0;
  font-size: 15px;
  color: #111827;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.region-similarity-chart-wrapper {
  position: relative;
  flex: 1;
}

.region-similarity-chart {
  width: 100%;
  height: 220px;
}

.region-similarity-loading,
.region-similarity-empty,
.region-similarity-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  color: #6b7280;
  font-size: 13px;
  text-align: center;
  padding: 16px;
}

.region-similarity-error {
  border-color: #fca5a5;
  color: #b91c1c;
  background: #fef2f2;
}
</style>


