<template>
  <div class="heatmap-container">
    <div class="heatmap-header">
      <div>
        <h3>{{ currentTitle }}</h3>
        <p class="heatmap-meta">
          城市等级：{{ currentPayload?.tierName ?? '—' }}
          <span class="separator">|</span>
          城市数量：{{ currentPayload?.cityCount ?? '--' }}
        </p>
      </div>
      <div class="heatmap-metric">
        <span class="metric-tag">度量：{{ metricLabelMap[metric] || metric }}</span>
        <span class="metric-tag">Y轴：{{ dimensionLabel }}</span>
      </div>
    </div>

    <div v-if="displayError" class="heatmap-error">
      {{ displayError }}
    </div>

    <div v-else class="heatmap-chart-wrapper">
      <div v-if="displayLoading" class="heatmap-loading">加载中...</div>
      <div v-else-if="!currentPayload" class="heatmap-empty">暂无数据</div>
      <!-- 容器始终存在，使用 v-show 控制显示，确保 ref 能获取到 -->
      <div v-show="currentPayload" ref="chartRef" class="heatmap-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import { useHeatmapData } from '../../composables/useHeatmapData';

const metricLabelMap = {
  job_count: '职位数量',
  industry_ratio: '行业占比',
  location_quotient: '区位商',
};

// 统一为偏蓝紫的清爽配色，与仪表盘整体风格一致
const metricColorMap = {
  // 职位数量：由浅蓝到深蓝
  job_count: ['#e0f2ff', '#90c4ff', '#3b82f6', '#1d4ed8'],
  // 行业占比：青蓝渐变
  industry_ratio: ['#e0f7fa', '#80deea', '#22c1c3', '#0f766e'],
  // 区位商：蓝紫渐变
  location_quotient: ['#ede9fe', '#a5b4fc', '#6366f1', '#4c1d95'],
};

const emit = defineEmits(['city-click']);

const props = defineProps({
  tier: {
    type: String,
    default: 'first_tier',
  },
  metric: {
    type: String,
    default: 'job_count',
  },
  dimensionLabel: {
    type: String,
    default: '公司类型',
  },
  dataset: {
    type: Object,
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
});

const chartRef = ref(null);
let chartInstance = null;

const { loading: internalLoading, error: internalError, heatmapPayload, loadHeatmap } =
  useHeatmapData();

const currentPayload = computed(() => props.dataset ?? heatmapPayload.value);

const displayLoading = computed(() =>
  props.loading === null ? internalLoading.value : props.loading,
);

const displayError = computed(() =>
  props.error === null ? internalError.value : props.error,
);

const currentTitle = computed(
  () => currentPayload.value?.title ?? '城市等级矩形热力图',
);

// 检查容器是否有有效尺寸且可见
const hasValidSize = (element) => {
  if (!element) return false;
  // 检查元素是否可见（display 不为 none）
  const style = window.getComputedStyle(element);
  if (style.display === 'none' || style.visibility === 'hidden') {
    return false;
  }
  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
};

const ensureChartInstance = () => {
  if (!chartRef.value) {
    return null;
  }
  
  // 如果实例不存在，创建新实例
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }
  
  return chartInstance;
};

const getVisualRange = (data = []) => {
  if (!data.length) {
    return { min: 0, max: 1 };
  }
  const values = data
    .map((item) => Number.isFinite(item.value) ? item.value : 0)
    .filter((val) => val !== undefined && val !== null);
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return { min: 0, max: max || 1 };
  }
  return { min, max };
};

const formatTooltip = (params) => {
  // params.data 格式: [xIndex, yIndex, value, item]
  const dataArray = Array.isArray(params?.data) ? params.data : [];
  const info = dataArray[3] || params?.data;
  if (!info || typeof info !== 'object') {
    return '';
  }

  const detail = info.detail_info || {};
  const formatPercent = (val) =>
    val === undefined || val === null ? '--' : `${(Number(val) * 100).toFixed(1)}%`;
  
  // 如果是"其他"类别，显示原始值
  const displayValue = info.isOther && info.originalValue !== undefined 
    ? info.originalValue 
    : info.value;

  return `
    <div class="heatmap-tooltip">
      <div class="tooltip-title">
        ${info.y || '--'} @ ${info.x || '--'}
        ${info.isOther ? '<span style="color: #999; font-size: 12px;">（其他类别）</span>' : ''}
      </div>
      <div class="tooltip-row"><span>值：</span><strong>${displayValue ?? '--'}</strong></div>
      <div class="tooltip-row"><span>行业占比：</span><strong>${formatPercent(
        detail.industry_ratio,
      )}</strong></div>
      <div class="tooltip-row"><span>区位商：</span><strong>${detail.location_quotient ?? '--'}</strong></div>
      <div class="tooltip-row"><span>平均学历：</span><strong>${detail.avg_education_rank ?? '--'}</strong></div>
      <div class="tooltip-row"><span>平均经验：</span><strong>${detail.avg_experience_rank ?? '--'}</strong></div>
      <div class="tooltip-row"><span>城市公司数：</span><strong>${detail.company_count_in_city ?? '--'}</strong></div>
      <div class="tooltip-row"><span>全国同类职位：</span><strong>${detail.national_job_count ?? '--'}</strong></div>
    </div>
  `;
};

// 渲染重试计数器，避免无限重试
let renderRetryCount = 0;
const MAX_RETRY_COUNT = 20; // 最多重试20次（约2秒）

const renderChart = () => {
  const payload = currentPayload.value;
  if (!payload) {
    renderRetryCount = 0; // 重置计数器
    return;
  }

  // 确保图表容器存在且有有效尺寸
  if (!chartRef.value) {
    if (renderRetryCount < MAX_RETRY_COUNT) {
      renderRetryCount++;
      // 使用更长的延迟，确保 DOM 已更新
      setTimeout(() => {
        if (currentPayload.value) {
          renderChart();
        }
      }, 150);
    } else {
      console.error('图表容器创建失败，已达到最大重试次数');
      renderRetryCount = 0;
    }
    return;
  }

  // 检查容器尺寸
  if (!hasValidSize(chartRef.value)) {
    if (renderRetryCount < MAX_RETRY_COUNT) {
      renderRetryCount++;
      // 使用 requestAnimationFrame 等待下一帧
      requestAnimationFrame(() => {
        setTimeout(() => {
          if (currentPayload.value && chartRef.value && hasValidSize(chartRef.value)) {
            renderChart();
          }
        }, 50);
      });
    } else {
      console.error('图表容器尺寸无效，已达到最大重试次数');
      renderRetryCount = 0;
    }
    return;
  }

  // 重置计数器，准备渲染
  renderRetryCount = 0;

  const chart = ensureChartInstance();
  if (!chart) {
    console.warn('图表实例创建失败');
    return;
  }

  const xAxis = payload.xAxis ?? [];
  const yAxis = payload.yAxis ?? [];
  
  // 分离"其他"类别和具体类别的数据
  const otherCategoryData = [];
  const normalCategoryData = [];
  
  (payload.heatmapData ?? []).forEach((item) => {
    if (item.y === '其他') {
      otherCategoryData.push(item);
    } else {
      normalCategoryData.push(item);
    }
  });

  // 计算具体类别的数值范围（排除"其他"）
  const { min: normalMin, max: normalMax } = getVisualRange(normalCategoryData);
  const { min: allMin, max: allMax } = getVisualRange(payload.heatmapData);
  
  // 将"其他"类别的值映射到具体类别的最大值范围内，但标记为特殊类型
  const normalizedOtherData = otherCategoryData.map((item) => {
    const xIndex = xAxis.indexOf(item.x);
    const yIndex = yAxis.indexOf(item.y);
    if (xIndex === -1 || yIndex === -1) {
      return null;
    }
    // "其他"类别使用特殊标记值：normalMax + 1，用于视觉区分
    // 实际显示时使用 normalizedValue（映射到正常范围内）
    const normalizedValue = normalMax > 0 
      ? Math.min(item.value ?? 0, normalMax * 1.2) // 限制在正常范围的120%
      : item.value ?? 0;
    return [xIndex, yIndex, normalizedValue, { ...item, isOther: true, originalValue: item.value }];
  }).filter(Boolean);

  const normalizedNormalData = normalCategoryData.map((item) => {
    const xIndex = xAxis.indexOf(item.x);
    const yIndex = yAxis.indexOf(item.y);
    if (xIndex === -1 || yIndex === -1) {
      return null;
    }
    return [xIndex, yIndex, item.value ?? 0, { ...item, isOther: false }];
  }).filter(Boolean);

  const seriesData = [...normalizedNormalData, ...normalizedOtherData];

  // 使用具体类别的范围作为主要映射范围
  const visualMin = normalMin;
  const visualMax = normalMax > 0 ? normalMax : 1;

  // 根据数据量动态调整配置
  const xAxisCount = xAxis.length;
  const yAxisCount = yAxis.length;
  
  // 动态计算 grid 边距，给标签更多空间
  const gridLeft = Math.max(120, yAxisCount * 2 + 80); // Y轴标签空间
  const gridBottom = Math.max(80, xAxisCount * 2 + 60); // X轴标签空间
  
  // 动态计算标签显示间隔，避免重叠
  const xAxisInterval = xAxisCount > 30 ? Math.floor(xAxisCount / 30) : 0; // X轴超过30个时显示部分
  const yAxisInterval = yAxisCount > 50 ? Math.floor(yAxisCount / 50) : 0; // Y轴超过50个时显示部分
  
  // 动态调整字体大小
  const xAxisFontSize = xAxisCount > 40 ? 10 : xAxisCount > 20 ? 11 : 12;
  const yAxisFontSize = yAxisCount > 50 ? 10 : yAxisCount > 30 ? 11 : 12;
  
  // 动态调整 X 轴旋转角度
  const xAxisRotate = xAxisCount > 40 ? 75 : xAxisCount > 30 ? 60 : 45;

  // 调试信息
  console.log('热力图数据:', {
    xAxisCount,
    yAxisCount,
    normalDataCount: normalizedNormalData.length,
    otherDataCount: normalizedOtherData.length,
    normalRange: { min: normalMin, max: normalMax },
    allRange: { min: allMin, max: allMax },
    visualRange: { min: visualMin, max: visualMax },
    gridLeft,
    gridBottom,
  });

  if (seriesData.length === 0) {
    console.warn('热力图数据为空');
    return;
  }

  // 在 setOption 之前再次确认容器有有效尺寸
  if (!hasValidSize(chartRef.value)) {
    if (renderRetryCount < MAX_RETRY_COUNT) {
      renderRetryCount++;
      requestAnimationFrame(() => {
        setTimeout(() => {
          if (currentPayload.value && chartRef.value && hasValidSize(chartRef.value)) {
          renderChart();
        }
        }, 100);
      });
      return;
    }
  }

  // 动态调整容器高度，根据 Y 轴标签数量
  const minHeight = 520;
  const calculatedHeight = Math.max(minHeight, yAxisCount * 12 + 200); // 每个标签约12px高度
  if (chartRef.value) {
    chartRef.value.style.height = `${calculatedHeight}px`;
  }

  chart.setOption(
    {
      tooltip: {
        trigger: 'item',
        formatter: formatTooltip,
        extraCssText: 'max-width:260px;',
      },
      grid: {
        top: 40,
        left: gridLeft,
        right: 60, // 收紧右侧留白，让图表横向更宽
        bottom: gridBottom,
      },
      xAxis: {
        type: 'category',
        data: xAxis,
        splitArea: {
          show: true,
        },
        axisLabel: {
          rotate: xAxisRotate, // 动态旋转角度
          interval: xAxisInterval, // 动态间隔
          fontSize: xAxisFontSize, // 动态字体大小
          formatter: (value) => {
            // 如果标签太长，截断显示
            const maxLength = xAxisCount > 40 ? 6 : 8;
            if (value && value.length > maxLength) {
              return value.substring(0, maxLength) + '...';
            }
            return value;
          },
          margin: 8, // 标签与轴的距离
        },
      },
      yAxis: {
        type: 'category',
        data: yAxis,
        splitArea: {
          show: true,
        },
        axisLabel: {
          interval: yAxisInterval, // 动态间隔
          fontSize: yAxisFontSize, // 动态字体大小
          rotate: yAxisCount > 50 ? -15 : 0, // 标签多时轻微旋转
          formatter: (value) => {
            // 如果标签太长，截断显示
            if (value && value.length > 12) {
              return value.substring(0, 12) + '...';
            }
            return value;
          },
          margin: 8, // 标签与轴的距离
        },
      },
      // 添加缩放交互，方便在城市/类别较多时放大查看
      dataZoom: [
        {
          type: 'slider',
          show: xAxisCount > 15,
          xAxisIndex: 0,
          start: 0,
          end: xAxisCount > 0 ? Math.min(100, (15 / xAxisCount) * 100) : 100,
          height: 18,
          bottom: 40,
        },
        {
          type: 'inside',
          xAxisIndex: 0,
        },
        {
          type: 'slider',
          show: yAxisCount > 20,
          yAxisIndex: 0,
          start: 0,
          end: yAxisCount > 0 ? Math.min(100, (20 / yAxisCount) * 100) : 100,
          width: 14,
          right: 40,
        },
        {
          type: 'inside',
          yAxisIndex: 0,
        },
      ],
      visualMap: [
        {
          // 具体类别的颜色映射
          min: visualMin,
          max: visualMax,
          calculable: true,
          orient: 'vertical',
          right: 10,
          top: 'center',
          text: ['高', '低'],
          inRange: {
            color: metricColorMap[props.metric] ?? metricColorMap.job_count,
          },
          dimension: 2,
          seriesIndex: 0, // 只应用于第一个 series（正常类别）
        },
        {
          // "其他"类别的灰色映射
          min: visualMin,
          max: visualMax,
          calculable: false,
          show: false, // 隐藏控制器
          inRange: {
            color: ['#f5f5f5', '#e0e0e0', '#c0c0c0'], // 浅灰色渐变
          },
          dimension: 2,
          seriesIndex: 1, // 只应用于第二个 series（其他类别）
        },
      ],
      series: [
        {
          // 正常类别的数据
          name: '具体类别',
          type: 'heatmap',
          data: normalizedNormalData,
          label: {
            show: false,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 5,
              shadowColor: 'rgba(0, 0, 0, 0.4)',
            },
          },
        },
        {
          // "其他"类别的数据
          name: '其他类别',
          type: 'heatmap',
          data: normalizedOtherData,
          label: {
            show: false,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 5,
              shadowColor: 'rgba(0, 0, 0, 0.4)',
            },
          },
        },
      ],
    },
    true,
  );

  // 确保图表正确渲染，只在容器有尺寸时调用 resize
  if (hasValidSize(chartRef.value)) {
    // 使用 requestAnimationFrame 确保 DOM 已更新
    requestAnimationFrame(() => {
      if (chartInstance && chartRef.value && hasValidSize(chartRef.value)) {
        chartInstance.resize();
        registerClickHandler();
      }
    });
  }
};

// 处理图表点击事件，用于联动城市词云
const registerClickHandler = () => {
  const chart = chartInstance;
  if (!chart) return;

  // 先移除旧的监听，避免重复绑定
  chart.off('click');

  chart.on('click', (params) => {
    const dataArray = Array.isArray(params.data) ? params.data : null;
    const meta = dataArray ? dataArray[3] : null;
    if (!meta) return;

    // 仅按城市联动（使用 x 轴编码）
    emit('city-click', {
      city: meta.x,
      companyType: meta.y,
      value: meta.value,
    });
  });
};

const fetchData = () => {
  if (!props.autoFetch) {
    return;
  }
  loadHeatmap({
    tier: props.tier,
    metric: props.metric,
    dimension_y: 'company_type',
  });
};

watch(
  () => [props.tier, props.metric, props.dataset],
  () => {
    renderRetryCount = 0; // 重置计数器
    if (props.dataset) {
      // 使用多重延迟确保 DOM 完全更新
      nextTick(() => {
        requestAnimationFrame(() => {
          setTimeout(() => {
            renderChart();
          }, 200); // 增加延迟时间
        });
      });
    } else {
      fetchData();
    }
  },
  { immediate: true },
);

watch(
  () => currentPayload.value,
  (newVal, oldVal) => {
    // 只有当数据真正变化时才重新渲染
    if (newVal && newVal !== oldVal) {
      renderRetryCount = 0; // 重置计数器
      nextTick(() => {
        requestAnimationFrame(() => {
          setTimeout(() => {
            renderChart();
          }, 200); // 增加延迟时间
        });
      });
    }
  },
  { deep: true },
);

// 监听 loading 状态，确保数据加载完成后渲染
watch(
  () => displayLoading.value,
  (isLoading, wasLoading) => {
    // 从加载中变为加载完成时，重新渲染
    if (wasLoading && !isLoading && currentPayload.value) {
      renderRetryCount = 0; // 重置计数器
      nextTick(() => {
        requestAnimationFrame(() => {
          setTimeout(() => {
            renderChart();
          }, 200); // 增加延迟时间
        });
      });
    }
  },
);

onMounted(() => {
  if (!props.dataset && props.autoFetch) {
    fetchData();
  } else if (props.dataset) {
    nextTick(() => {
      requestAnimationFrame(() => {
        renderChart();
      });
    });
  }
  window.addEventListener('resize', resizeChart);
});

const resizeChart = () => {
  if (chartInstance && chartRef.value && hasValidSize(chartRef.value)) {
    chartInstance.resize();
  }
};

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
.heatmap-container {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 640px;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.heatmap-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2937;
}

.heatmap-meta {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.separator {
  margin: 0 8px;
  color: #d1d5db;
}

.heatmap-metric {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.metric-tag {
  font-size: 12px;
  color: #2563eb;
  background: #e0edff;
  padding: 4px 10px;
  border-radius: 999px;
}

.heatmap-chart-wrapper {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.heatmap-chart {
  width: 100%;
  flex: 1;
  min-height: 520px;
}

.heatmap-loading,
.heatmap-empty,
.heatmap-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
  padding: 20px;
}

.heatmap-error {
  border-color: #fca5a5;
  color: #b91c1c;
  background: #fef2f2;
}

.heatmap-tooltip {
  font-size: 12px;
  color: #1f2937;
  line-height: 1.6;
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tooltip-row span {
  color: #6b7280;
}
</style>

