import apiClient from './apiClient';

const DEFAULT_PARAMS = {
  tier: 'first_tier',
  metric: 'job_count',
  dimension_y: 'company_type',
};

export function getCityTierHeatmap(params = {}) {
  const query = {
    ...DEFAULT_PARAMS,
    ...params,
  };

  return apiClient.get('/charts/heatmap/city-tier', {
    params: query,
  });
}

