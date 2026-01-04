<template>
  <div class="wordcloud-container">
    <div class="wordcloud-header">
      <div>
        <h3>城市行业词云</h3>
        <p class="wordcloud-meta">
          城市编码：{{ displayCity || '—' }}
        </p>
        <p class="wordcloud-meta hint">
          <span v-if="!displayCity">
            左侧：点击矩形热力图中的某个城市方块，这里将展示该城市的行业分布词云（按职业数量占比放大字体）。
          </span>
          <span v-else>
            当前展示的是所选城市的主导行业词云，词语越大，说明该行业在该城市的职位占比越高。
          </span>
        </p>
      </div>
    </div>

    <div v-if="errorToShow" class="wordcloud-error">
      {{ errorToShow }}
    </div>

    <div v-else class="wordcloud-chart-wrapper">
      <div v-if="loadingToShow" class="wordcloud-loading">加载中...</div>
      <div v-else-if="!wordsToShow.length" class="wordcloud-empty">暂无词云数据</div>
      <div v-else ref="chartRef" class="wordcloud-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import 'echarts-wordcloud';
import { useCityWordcloud } from '../../composables/useCityWordcloud';

const props = defineProps({
  city: {
    type: String,
    default: null,
  },
  words: {
    type: Array,
    default: null,
  },
  loading: {
    type: Boolean,
    default: null,
  },
  error: {
    type: String,
    default: null,
  },
  autoFetch: {
    type: Boolean,
    default: true,
  },
  topN: {
    type: Number,
    default: 10,
  },
});

const chartRef = ref(null);
let chartInstance = null;

const {
  loading: internalLoading,
  error: internalError,
  words: internalWords,
  currentCity,
  loadWordcloud,
} = useCityWordcloud();

const loadingToShow = computed(() =>
  props.loading === null ? internalLoading.value : props.loading,
);

const errorToShow = computed(() =>
  props.error === null ? internalError.value : props.error,
);

const wordsToShow = computed(() => props.words ?? internalWords.value ?? []);

const displayCity = computed(() => props.city ?? currentCity.value);

// 检查容器是否有有效尺寸
const hasValidSize = (element) => {
  if (!element) return false;
  const style = window.getComputedStyle(element);
  if (style.display === 'none' || style.visibility === 'hidden') {
    return false;
  }
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

// 简化：每次渲染时销毁旧实例并重新创建，避免在无尺寸时反复 resize
const renderChart = () => {
  if (!wordsToShow.value || !wordsToShow.value.length) {
    return;
  }

  const el = chartRef.value;
  if (!el || !hasValidSize(el)) {
    // 容器还没布局好，稍后再试
    setTimeout(() => {
      renderChart();
    }, 100);
    return;
  }

  // 销毁旧实例
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }

  // 创建新实例
  chartInstance = echarts.init(el);

  const seriesData = wordsToShow.value.map((item) => ({
    name: item.name,
    value: item.value,
  }));

  chartInstance.setOption(
    {
      tooltip: {
        show: true,
        formatter: (params) =>
          `${params.name}<br/>权重：${(params.value * 100).toFixed(1)}%`,
      },
      series: [
        {
          type: 'wordCloud',
          shape: 'circle',
          gridSize: 8,
          sizeRange: [14, 48],
          rotationRange: [-45, 45],
          rotationStep: 15,
          drawOutOfBound: false,
          textStyle: {
            color: () =>
              `rgb(${Math.round(Math.random() * 160)}, ${Math.round(
                Math.random() * 160,
              )}, ${Math.round(Math.random() * 160)})`,
          },
          emphasis: {
            textStyle: {
              shadowBlur: 10,
              shadowColor: '#333',
            },
          },
          data: seriesData,
        },
      ],
    },
    true,
  );

  // 确保在容器有尺寸时再调整大小
  // 不主动调用 resize，避免在容器尺寸变化瞬间触发 echarts-gl 的错误
};

const fetchData = () => {
  if (!props.autoFetch || !props.city) return;
  loadWordcloud(props.city, props.topN);
};

watch(
  () => props.city,
  (newCity) => {
    if (newCity) {
      fetchData();
    }
  },
  { immediate: true },
);

watch(
  () => wordsToShow.value,
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
  } else if (wordsToShow.value && wordsToShow.value.length) {
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
.wordcloud-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px 20px 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: box-shadow 0.15s ease-in-out;
}

.wordcloud-container:hover {
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}

.wordcloud-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.wordcloud-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1f2937;
}

.wordcloud-meta {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.wordcloud-meta.hint {
  margin-top: 2px;
  line-height: 1.5;
}

.wordcloud-chart-wrapper {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.wordcloud-chart {
  width: 100%;
  flex: 1;
  min-height: 200px;
}

.wordcloud-loading,
.wordcloud-empty,
.wordcloud-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
  padding: 20px;
}

.wordcloud-error {
  border-color: #fca5a5;
  color: #b91c1c;
  background: #fef2f2;
}
</style>



