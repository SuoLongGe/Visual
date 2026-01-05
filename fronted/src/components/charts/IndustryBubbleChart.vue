<template>
  <div :class="['industry-bubble-container', { 'fullscreen': isFullscreen }]">
    <div class="industry-bubble-header">
      <div class="title-block">
        <h3>行业规模与区位商多维度气泡图</h3>
        <p class="subtitle">
          横轴：行业在全国的职位占比；纵轴：区位商（产业集聚度）；气泡大小：本地岗位数；颜色：城市等级。
        </p>
      </div>
      <div class="controls">
        <div class="control-group">
          <span class="control-label">城市等级</span>
          <div class="tier-filters">
            <button
              v-for="tier in tierOptions"
              :key="tier.value"
              type="button"
              :class="['tier-pill', { active: activeTiers.includes(tier.value) }]"
              @click="toggleTier(tier.value)"
            >
              {{ tier.label }}
            </button>
          </div>
        </div>
        <div class="control-group">
          <span class="control-label">行业高亮</span>
          <select v-model="selectedIndustry">
            <option value="">全部行业</option>
            <option
              v-for="name in industryOptions"
              :key="name"
              :value="name"
            >
              {{ name }}
            </option>
          </select>
        </div>
        <button 
          type="button" 
          class="fullscreen-btn"
          @click="toggleFullscreen"
          :title="isFullscreen ? '退出全屏' : '全屏显示'"
        >
          <svg v-if="!isFullscreen" class="icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
          </svg>
          <svg v-else class="icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="errorToShow" class="industry-bubble-error">
      {{ errorToShow }}
    </div>

    <div v-else class="industry-bubble-chart-wrapper">
      <div v-if="loadingToShow" class="industry-bubble-loading">加载中...</div>
      <div v-else-if="!hasData" class="industry-bubble-empty">
        暂无气泡图数据
      </div>
      <div v-else ref="chartRef" class="industry-bubble-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import { useIndustryBubble } from '../../composables/useIndustryBubble';

const props = defineProps({
  cityTiers: {
    type: Array,
    default: () => ['first_tier', 'second_tier', 'third_tier', 'other'],
  },
  industryFilter: {
    type: String,
    default: null,
  },
  autoFetch: {
    type: Boolean,
    default: true,
  },
});

const chartRef = ref(null);
let chartInstance = null;

// Fullscreen state
const isFullscreen = ref(false);

const { loading, error, bubblePayload, loadIndustryBubble } = useIndustryBubble();

const loadingToShow = computed(() => loading.value);
const errorToShow = computed(() => error.value);

const bubbleData = computed(() => bubblePayload.value?.bubbleData ?? []);
const hasData = computed(
  () => !!bubblePayload.value && Array.isArray(bubbleData.value) && bubbleData.value.length > 0,
);

// 城市等级交互筛选
const tierOptions = [
  { value: 'first_tier', label: '一线' },
  { value: 'second_tier', label: '二线' },
  { value: 'third_tier', label: '三线' },
  { value: 'other', label: '其他' },
];

const activeTiers = ref([...props.cityTiers]);

watch(
  () => props.cityTiers,
  (val) => {
    if (Array.isArray(val) && val.length) {
      activeTiers.value = [...val];
    }
  },
  { immediate: true, deep: true },
);

const toggleTier = (tier) => {
  const current = new Set(activeTiers.value);
  if (current.has(tier)) {
    // 至少保留一个分级，避免全空
    if (current.size === 1) return;
    current.delete(tier);
  } else {
    current.add(tier);
  }
  activeTiers.value = Array.from(current);
};

// 行业高亮筛选
const selectedIndustry = ref('');
const industryOptions = computed(() => bubblePayload.value?.industryList ?? []);

const filteredBubbleData = computed(() => {
  if (!bubbleData.value || !bubbleData.value.length) return [];

  return bubbleData.value.filter((item) => {
    const tierOk = activeTiers.value.includes(item.city_tier || 'other');
    if (!tierOk) return false;

    if (!selectedIndustry.value) return true;
    return item.industry_label === selectedIndustry.value;
  });
});

// 颜色映射与现有页面保持一致的蓝/青/紫+灰色系
const tierColorMap = {
  first_tier: '#3b82f6', // 蓝
  second_tier: '#22c1c3', // 青
  third_tier: '#f97316', // 橙，提升与一线的对比度
  other: '#9ca3af', // 灰
};

// 检查容器是否有有效尺寸
const hasValidSize = (el) => {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return false;
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

const jitterCache = new Map();

const getJitter = (key, axis = 'x') => {
  if (!key) return 0;
  const cacheKey = `${axis}_${key}`;
  if (!jitterCache.has(cacheKey)) {
    const base = key
      .split('')
      .reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
    const offset = (base % 7) - 3; // -3 ~ +3
    jitterCache.set(cacheKey, offset);
  }
  const raw = jitterCache.get(cacheKey);
  const scale = axis === 'x' ? 0.002 : 0.0015;
  return raw * scale;
};

const buildSeriesData = () => {
  if (!filteredBubbleData.value || !filteredBubbleData.value.length) return [];

  // 找一个大致的 scale，让气泡大小在视觉上适中
  const maxLocalJobs = filteredBubbleData.value.reduce(
    (max, item) => Math.max(max, Number(item.local_job_count || 0)),
    0,
  );

  const sizeScale = maxLocalJobs > 0 ? 60 / Math.sqrt(maxLocalJobs) : 10;

  return filteredBubbleData.value.map((item) => {
    const baseX = Number(item.national_job_percentage || 0);
    const baseY = Number(item.location_quotient || 0);
    const x = baseX + getJitter(item.city, 'x');
    const y = baseY + getJitter(item.city, 'y');
    const localJobs = Number(item.local_job_count || 0);
    const tier = item.city_tier || 'other';

    const isHighlighted =
      !selectedIndustry.value || item.industry_label === selectedIndustry.value;

    return {
      value: [x, y, localJobs],
      symbolSize: Math.max(8, Math.sqrt(localJobs) * sizeScale),
      itemStyle: {
        color: tierColorMap[tier] || tierColorMap.other,
        opacity: isHighlighted ? 0.95 : 0.18,
      },
      emphasis: {
        scale: 1.15,
      },
      // meta 信息用于 tooltip
      meta: item,
    };
  });
};

const renderChart = () => {
  if (!hasData.value) return;

  const el = chartRef.value;
  if (!el || !hasValidSize(el)) {
    setTimeout(() => {
      if (hasData.value) {
        renderChart();
      }
    }, 120);
    return;
  }

  // 销毁旧实例
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }

  chartInstance = echarts.init(el);

  const seriesData = buildSeriesData();

  chartInstance.setOption(
    {
      grid: {
        top: 56,
        left: 60,
        right: 32,
        bottom: 56,
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          filterMode: 'weakFilter',
          zoomLock: false,
          minSpan: 5,
        },
        {
          type: 'inside',
          yAxisIndex: 0,
          filterMode: 'weakFilter',
          zoomLock: false,
          minSpan: 5,
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          height: 18,
          bottom: 20,
          handleSize: 12,
          brushSelect: true,
        },
        {
          type: 'slider',
          yAxisIndex: 0,
          width: 14,
          right: 6,
          handleSize: 12,
        },
      ],
      tooltip: {
        trigger: 'item',
        borderWidth: 0,
        backgroundColor: 'rgba(17, 24, 39, 0.92)',
        textStyle: {
          color: '#e5e7eb',
          fontSize: 12,
        },
        formatter: (params) => {
          const meta = params.data?.meta || {};
          const tierMap = {
            first_tier: '一线城市',
            second_tier: '二线城市',
            third_tier: '三线城市',
            other: '其他城市',
          };
          const tierName = tierMap[meta.city_tier] || '未知';

          const pct = Number(meta.national_job_percentage || 0) * 100;
          const lq = Number(meta.location_quotient || 0);
          const localJobs = Number(meta.local_job_count || 0);

          return [
            `<div><strong>${meta.industry_label || '—'}</strong></div>`,
            `<div>城市：${meta.city || '—'}（${tierName}）</div>`,
            `<div>本地岗位数：${localJobs}</div>`,
            `<div>行业全国岗位数：${meta.national_job_count ?? '—'}</div>`,
            `<div>行业全国占比：${pct.toFixed(2)}%</div>`,
            `<div>区位商：${lq.toFixed(2)}</div>`,
          ].join('<br/>');
        },
      },
      xAxis: {
        type: 'value',
        name: '全国职位占比',
        nameLocation: 'middle',
        nameGap: 28,
        axisLabel: {
          formatter: (val) => (val * 100).toFixed(1) + '%',
          color: '#4b5563',
        },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: '#e5e7eb',
          },
        },
      },
      yAxis: {
        type: 'value',
        name: '区位商（产业集聚度）',
        nameLocation: 'middle',
        nameGap: 42,
        axisLabel: {
          color: '#4b5563',
        },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: '#e5e7eb',
          },
        },
      },
      legend: {
        top: 8,
        right: 12,
        itemWidth: 12,
        itemHeight: 12,
        textStyle: {
          fontSize: 11,
          color: '#4b5563',
        },
        data: [
          { name: '一线城市', itemStyle: { color: tierColorMap.first_tier } },
          { name: '二线城市', itemStyle: { color: tierColorMap.second_tier } },
          { name: '三线城市', itemStyle: { color: tierColorMap.third_tier } },
          { name: '其他城市', itemStyle: { color: tierColorMap.other } },
        ],
      },
      series: [
        {
          type: 'scatter',
          data: seriesData,
          symbol: 'circle',
          emphasis: {
            focus: 'series',
          },
        },
      ],
    },
    true,
  );
};

const fetchData = () => {
  if (!props.autoFetch) return;
  loadIndustryBubble({
    cityTiers: props.cityTiers,
    industryFilter: props.industryFilter,
  }).then(() => {
    nextTick(() => {
      renderChart();
    });
  });
};

watch(
  () => [props.cityTiers, props.industryFilter],
  () => {
    if (props.autoFetch) {
      fetchData();
    }
  },
  { deep: true, immediate: true },
);

watch(
  () => bubbleData.value,
  (val) => {
    if (val && val.length) {
      nextTick(() => {
        renderChart();
      });
    }
  },
  { deep: true },
);

// Fullscreen functionality
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  
  if (isFullscreen.value) {
    // Enter fullscreen
    document.body.style.overflow = 'hidden';
  } else {
    // Exit fullscreen
    document.body.style.overflow = '';
  }
  
  // Resize chart to fit new container size
  nextTick(() => {
    if (chartInstance) {
      chartInstance.resize();
    }
  });
};

// Handle ESC key to exit fullscreen
const handleEscKey = (e) => {
  if (e.key === 'Escape' && isFullscreen.value) {
    toggleFullscreen();
  }
};

// 当城市分级或行业高亮筛选变化时，基于已加载数据做前端重绘
watch(
  () => [filteredBubbleData.value, selectedIndustry.value, activeTiers.value],
  () => {
    if (hasData.value) {
      nextTick(() => {
        renderChart();
      });
    }
  },
  { deep: true },
);

onMounted(() => {
  if (props.autoFetch) {
    fetchData();
  } else if (hasData.value) {
    renderChart();
  }
  
  // Add ESC key listener for fullscreen
  window.addEventListener('keydown', handleEscKey);
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  
  // Remove ESC key listener and clean up body overflow
  window.removeEventListener('keydown', handleEscKey);
  document.body.style.overflow = '';
});
</script>

<style scoped>
.industry-bubble-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px 20px 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  min-height: 380px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease-in-out;
}

.industry-bubble-container:not(.fullscreen):hover {
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}

.industry-bubble-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  margin: 0;
  border-radius: 0;
  max-width: none;
  padding: 88px 32px 32px 32px; /* 顶部留出88px给固定导航栏 */
}

.industry-bubble-container.fullscreen .industry-bubble-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.industry-bubble-container.fullscreen .industry-bubble-chart {
  height: calc(100vh - 228px); /* 减去顶部导航栏(88px)、容器padding(88px+32px)和header高度 */
}

.industry-bubble-container.fullscreen .industry-bubble-chart-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.industry-bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.industry-bubble-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1f2937;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.title-block {
  max-width: 420px;
}

.controls {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.industry-bubble-container.fullscreen .controls {
  background-color: #f9fafb;
  padding: 12px 16px;
  border-radius: 8px;
  gap: 20px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.control-label {
  color: #4b5563;
  font-weight: 500;
}

.tier-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tier-pill {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background-color: #f9fafb;
  color: #4b5563;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  flex-shrink: 0;
}

.tier-pill:hover {
  background-color: #e5efff;
  border-color: #bfdbfe;
  color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
}

.tier-pill:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
}

.tier-pill.active {
  background-color: #e0f2ff;
  border-color: #3b82f6;
  color: #1d4ed8;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.25);
  font-weight: 500;
}

.tier-pill.active:hover {
  background-color: #bfdbfe;
  border-color: #2563eb;
  color: #1e40af;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.control-group select {
  min-width: 180px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  background-color: #fff;
  color: #111827;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
}

.control-group select:hover {
  border-color: #9ca3af;
  background-color: #f9fafb;
}

.control-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.fullscreen-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: #fff;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  flex-shrink: 0;
}

.fullscreen-btn:hover {
  background-color: #f3f4f6;
  border-color: #9ca3af;
  color: #1f2937;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.fullscreen-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.industry-bubble-container.fullscreen .fullscreen-btn {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.industry-bubble-container.fullscreen .fullscreen-btn:hover {
  background-color: #2563eb;
  border-color: #2563eb;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.3);
}

.industry-bubble-container.fullscreen .fullscreen-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 6px rgba(59, 130, 246, 0.2);
}

.fullscreen-btn .icon {
  width: 20px;
  height: 20px;
}

.industry-bubble-chart-wrapper {
  position: relative;
  flex: 1;
}

.industry-bubble-chart {
  width: 100%;
  height: 320px;
}

.industry-bubble-loading,
.industry-bubble-empty,
.industry-bubble-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  color: #6b7280;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.industry-bubble-error {
  border-color: #fca5a5;
  color: #b91c1c;
  background: #fef2f2;
}

/* 响应式支持 - 移动端全屏模式 */
@media (max-width: 768px) {
  .industry-bubble-container.fullscreen {
    padding: 80px 16px 16px 16px; /* 移动端导航栏可能不同 */
  }
  
  .industry-bubble-container.fullscreen .industry-bubble-chart {
    height: calc(100vh - 200px);
  }
  
  .industry-bubble-container.fullscreen .controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .industry-bubble-container.fullscreen .control-group {
    width: 100%;
  }
  
  .industry-bubble-container.fullscreen .control-group select {
    width: 100%;
  }
}
</style>


