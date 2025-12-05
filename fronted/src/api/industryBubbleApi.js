import apiClient from './apiClient';

const DEFAULT_PARAMS = {
    city_tiers: [],
    industry_filter: null,
};

export function getIndustryLocationBubble(params = {}) {
    const query = {
        ...DEFAULT_PARAMS,
        ...params,
    };

    return apiClient.get('/charts/bubble/industry-location', {
        params: query,
    });
}


