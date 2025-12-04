import apiClient from './apiClient';

export function getRegionProfile(city, topSimilar = 5) {
  return apiClient.get('/charts/region/profile', {
    params: {
      city,
      top_similar: topSimilar,
    },
  });
}


