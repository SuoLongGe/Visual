import apiClient from './apiClient';

export function getCityWordcloud(city, topN = 10) {
  return apiClient.get('/charts/wordcloud/city', {
    params: {
      city,
      top_n: topN,
    },
  });
}


