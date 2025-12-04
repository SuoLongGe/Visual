import { ref } from 'vue';
import { getCityWordcloud } from '../api/wordcloudApi';

export function useCityWordcloud() {
    const loading = ref(false);
    const error = ref(null);
    const words = ref([]);
    const currentCity = ref(null);

    const loadWordcloud = async (city, topN = 10) => {
        if (!city) {
            error.value = '城市编码不能为空';
            words.value = [];
            currentCity.value = null;
            return null;
        }

        loading.value = true;
        error.value = null;

        try {
            const response = await getCityWordcloud(city, topN);
            const payload = response?.data ?? response ?? null;

            if (!payload) {
                throw new Error('未获取到词云数据');
            }

            currentCity.value = payload.city;
            words.value = payload.words ?? [];

            return {
                city: currentCity.value,
                words: words.value,
            };
        } catch (err) {
            error.value = err instanceof Error ? err.message : String(err);
            words.value = [];
            currentCity.value = null;
            return null;
        } finally {
            loading.value = false;
        }
    };

    return {
        loading,
        error,
        words,
        currentCity,
        loadWordcloud,
    };
}


