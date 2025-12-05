import { ref } from 'vue';
import { getRegionProfile } from '../api/regionProfileApi';

export function useRegionProfile() {
    const loading = ref(false);
    const error = ref(null);
    const profile = ref(null);

    const loadRegionProfile = async (city, topSimilar = 5) => {
        if (!city) {
            error.value = '城市编码不能为空';
            profile.value = null;
            return null;
        }

        loading.value = true;
        error.value = null;

        try {
            const response = await getRegionProfile(city, topSimilar);
            const payload = response?.data ?? response ?? null;

            if (!payload) {
                throw new Error('未获取到地域画像数据');
            }

            profile.value = payload;
            return profile.value;
        } catch (err) {
            error.value = err instanceof Error ? err.message : String(err);
            profile.value = null;
            return null;
        } finally {
            loading.value = false;
        }
    };

    return {
        loading,
        error,
        profile,
        loadRegionProfile,
    };
}


