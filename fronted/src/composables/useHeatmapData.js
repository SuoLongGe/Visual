import { ref } from 'vue';
import { getCityTierHeatmap } from '../api/heatmapApi';

export function useHeatmapData() {
  const loading = ref(false);
  const error = ref(null);
  const heatmapPayload = ref(null);

  const loadHeatmap = async ({
    tier = 'first_tier',
    metric = 'job_count',
    dimension_y = 'company_type',
  } = {}) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await getCityTierHeatmap({ tier, metric, dimension_y });
      const payload = response?.data ?? response ?? null;

      if (!payload) {
        throw new Error('未获取到热力图数据');
      }

      heatmapPayload.value = {
        tier: payload.tier,
        tierName: payload.tier_name,
        metric: payload.metric,
        cityCount: payload.city_count,
        title: payload.title,
        xAxis: payload.dimensions?.x_axis ?? [],
        yAxis: payload.dimensions?.y_axis ?? [],
        heatmapData: payload.heatmap_data ?? [],
      };

      return heatmapPayload.value;
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      heatmapPayload.value = null;
      return null;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    heatmapPayload,
    loadHeatmap,
  };
}

