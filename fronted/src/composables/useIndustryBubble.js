import { ref } from 'vue';
import { getIndustryLocationBubble } from '../api/industryBubbleApi';

export function useIndustryBubble() {
    const loading = ref(false);
    const error = ref(null);
    const bubblePayload = ref(null);

    const loadIndustryBubble = async ({ cityTiers = [], industryFilter = null } = {}) => {
        loading.value = true;
        error.value = null;

        try {
            const response = await getIndustryLocationBubble({
                city_tiers: cityTiers,
                industry_filter: industryFilter,
            });
            const payload = response?.data ?? response ?? null;

            if (!payload) {
                throw new Error('未获取到多维度气泡图数据');
            }

            bubblePayload.value = {
                nationalTotalJobs: payload.national_total_jobs ?? 0,
                bubbleData: payload.bubble_data ?? [],
                industryList: payload.industry_list ?? [],
                cityTierList: payload.city_tier_list ?? [],
            };

            return bubblePayload.value;
        } catch (err) {
            error.value = err instanceof Error ? err.message : String(err);
            bubblePayload.value = null;
            return null;
        } finally {
            loading.value = false;
        }
    };

    return {
        loading,
        error,
        bubblePayload,
        loadIndustryBubble,
    };
}


