<template>
  <div class="boxplot-chart">
    <div v-if="!filters.experience || !filters.education" class="info-tip">
      <p>💡 请在上方的3D图表中点击柱体，选择工作经验和学历要求</p>
    </div>
    
    <div class="filter-section">
      <div class="filter-group">
        <label>工作经验：</label>
        <div class="selected-value" :class="{ 'selected': filters.experience, 'not-selected': !filters.experience }">
          {{ filters.experience || '未选择 - 点击3D图表柱体' }}
        </div>
      </div>
      
      <div class="filter-group">
        <label>学历要求：</label>
        <div class="selected-value" :class="{ 'selected': filters.education, 'not-selected': !filters.education }">
          {{ filters.education || '未选择 - 点击3D图表柱体' }}
        </div>
      </div>
      
      <div class="filter-group">
        <label>城市筛选：</label>
        <select 
          v-model="filtersCity" 
          class="filter-select"
          :disabled="!filters.experience || !filters.education"
        >
          <option value="">全部城市</option>
          <option v-for="city in availableCities" :key="city" :value="city">{{ city }}</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>公司类型：</label>
        <select 
          v-model="filtersCompanyType" 
          class="filter-select"
          :disabled="!filters.experience || !filters.education"
        >
          <option value="">全部类型</option>
          <option v-for="type in availableCompanyTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>视图类型：</label>
        <select v-model="viewType" class="filter-select">
          <option value="city">按城市分布</option>
          <option value="company_type">按公司类型分布</option>
        </select>
      </div>
      
      <div class="filter-info">
        <span v-if="filtersCity" class="filter-tag">
          📍 {{ filtersCity }}
          <button @click="filtersCity = ''" class="clear-btn">✕</button>
        </span>
        <span v-if="filtersCompanyType" class="filter-tag">
          🏢 {{ filtersCompanyType }}
          <button @click="filtersCompanyType = ''" class="clear-btn">✕</button>
        </span>
      </div>
    </div>
    
    <div v-show="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div ref="chartContainer" id="boxplot-container" class="chart-container" :class="{ 'loading-state': loading }">
    <div v-show="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, onMounted, nextTick, watch, queuePostFlushCb, computed } from 'vue'
import * as echarts from 'echarts'
import { getBoxplotData } from '@/api/salary3dApi.js'

const props = defineProps({
  experience: {
    type: String,
    default: ''
  },
  education: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:experience', 'update:education'])

// 直接使用 props，不维护独立的 filters 状态，避免响应式更新冲突
const filters = computed(() => ({
  experience: props.experience || '',
  education: props.education || '',
  city: filtersCity.value,
  company_type: filtersCompanyType.value
}))

// 只维护用户选择的筛选条件（city 和 company_type）
const filtersCity = ref('')
const filtersCompanyType = ref('')

const viewType = ref('city')
const chartContainer = ref(null)
const hasData = ref(false)
const loading = ref(false)
const error = ref(null)
const stats = ref(null)
const availableCities = ref([])
const availableCompanyTypes = ref([])
let boxplotChart = null
let resizeHandler = null

// 用于防止重复加载的标记
let isLoading = false
let pendingLoad = false
let isComponentMounted = true // 组件挂载状态
let currentLoadId = 0 // 当前加载请求的 ID，用于取消旧的请求

// 清理图表的辅助函数（只在真正需要清理时调用）
const cleanupChart = () => {
  if (boxplotChart) {
    try {
      boxplotChart.dispose()
    } catch (e) {
      console.warn('清理图表时出错:', e)
    }
    boxplotChart = null
  }
  if (isComponentMounted) {
    hasData.value = false
  }
}

// 监听props变化，自动加载
// 关键：使用 requestAnimationFrame 确保在浏览器完成渲染后再执行
let propsWatchStop = watch([() => props.experience, () => props.education], ([expVal, eduVal], [oldExpVal, oldEduVal]) => {
  // 如果组件已卸载，不执行任何操作
  if (!isComponentMounted) {
    return
  }
  
  // 判断是否是初次加载（oldExpVal 和 oldEduVal 都是 undefined 或空）
  const isInitialLoad = (oldExpVal === undefined && oldEduVal === undefined) || 
                        (!oldExpVal && !oldEduVal)
  
  // 如果任一值为空，清理图表（但不是在初次加载时）
  if (!expVal || !eduVal) {
    // 只有在不是初次加载时才清理（避免初次挂载时清理）
    if (!isInitialLoad) {
      // 使用 requestAnimationFrame 延迟清理，避免在 Vue patch 期间操作
      requestAnimationFrame(() => {
        if (isComponentMounted) {
          cleanupChart()
        }
      })
    }
    return
  }
  
  // 如果两个参数都有了，且值确实改变了，才加载新数据
  // 避免重复加载相同的数据
  const valuesChanged = isInitialLoad || expVal !== oldExpVal || eduVal !== oldEduVal
  
  if (!valuesChanged) {
    return
  }
  
  // 取消之前的待处理加载
  pendingLoad = false
  
  // 使用 requestAnimationFrame 确保在浏览器完成渲染后再执行
  // 这样 Vue 的所有 DOM 更新都已经完成
  requestAnimationFrame(() => {
    if (!isComponentMounted || !chartContainer.value) {
      // 如果容器还不存在，延迟重试
      requestAnimationFrame(() => {
        if (!isComponentMounted || !chartContainer.value) return
        if (!isLoading && props.experience && props.education) {
          handleLoad()
        }
      })
      return
    }
    
    // 再次使用 requestAnimationFrame 确保完全稳定
    requestAnimationFrame(() => {
      if (!isComponentMounted || !chartContainer.value) return
      
      // 检查加载状态，避免重复加载
      if (!isLoading && props.experience && props.education) {
        handleLoad()
      }
    })
  })
}, { immediate: true, flush: 'post' })

// 监听视图类型变化
watch(viewType, () => {
  if (!isComponentMounted) return
  if (hasData.value && props.experience && props.education && !isLoading) {
    handleLoad()
  }
})

// 监听城市筛选变化 - 自动刷新
let cityWatchStop = watch(() => filtersCity.value, (newVal, oldVal) => {
  if (!isComponentMounted) return
  // 只有在已有数据且城市确实改变时才刷新
  if (hasData.value && props.experience && props.education && newVal !== oldVal && !isLoading) {
    handleLoad()
  }
})

// 监听公司类型筛选变化 - 自动刷新
let companyTypeWatchStop = watch(() => filtersCompanyType.value, (newVal, oldVal) => {
  if (!isComponentMounted) return
  // 只有在已有数据且公司类型确实改变时才刷新
  if (hasData.value && props.experience && props.education && newVal !== oldVal && !isLoading) {
    handleLoad()
  }
})

const handleLoad = async () => {
  // 防止重复加载
  if (isLoading) {
    console.log('正在加载中，跳过重复请求')
    return
  }
  
  // 检查组件是否仍然挂载
  if (!isComponentMounted) {
    console.warn('组件已卸载，取消加载')
    return
  }
  
  // 生成新的请求 ID
  const loadId = ++currentLoadId
  
  // 等待 Vue 完成当前更新周期，确保 DOM 稳定
  await nextTick()
  if (!isComponentMounted || !chartContainer.value) {
    console.warn('组件已卸载或容器不存在，取消加载')
    return
  }
  
  // 检查是否有更新的请求
  if (loadId !== currentLoadId) {
    console.log('有更新的请求，取消当前请求')
    return
  }
  
  try {
    // 验证必填参数
    if (!props.experience || !props.education) {
      if (isComponentMounted && loadId === currentLoadId) {
        await nextTick()
        if (isComponentMounted && loadId === currentLoadId) {
          error.value = '请先点击3D图表中的柱体选择工作经验和学历要求'
        }
      }
      return
    }
    
    // 再次检查组件状态和容器
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      return
    }
    
    // 设置加载状态（在确保组件状态后）
    // 直接设置，因为已经改为 v-show，不会导致 DOM 元素添加/移除
    isLoading = true
    if (isComponentMounted && loadId === currentLoadId && chartContainer.value && chartContainer.value.isConnected) {
      loading.value = true
      error.value = null
    } else {
      isLoading = false
      return
    }
    
    // 等待响应式更新完成
    await nextTick()
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      isLoading = false
      if (isComponentMounted && loadId === currentLoadId) {
        loading.value = false
      }
      return
    }
    
    // 获取全部数据（不带city和company_type筛选）以获取完整的选项列表
    const allDataFilters = {
      experience: props.experience,
      education: props.education
    }
    const allDataResponse = await getBoxplotData(allDataFilters)
    
    // 再次检查容器和组件状态（可能在异步操作期间被销毁）
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('组件已卸载或图表容器在加载过程中被销毁，取消渲染')
      isLoading = false
      if (isComponentMounted && loadId === currentLoadId) {
        loading.value = false
      }
      return
    }
    
    // 记录 API 响应，便于调试
    console.log('箱线图 API 响应:', {
      experience: props.experience,
      education: props.education,
      code: allDataResponse.code,
      hasData: !!allDataResponse.data,
      city_data_length: allDataResponse.data?.city_data?.length || 0,
      company_type_data_length: allDataResponse.data?.company_type_data?.length || 0,
      response: allDataResponse
    })
    
    if (allDataResponse.code !== 200) {
      console.error('获取箱线图数据失败:', {
        code: allDataResponse.code,
        message: allDataResponse.message,
        experience: props.experience,
        education: props.education
      })
      if (isComponentMounted && loadId === currentLoadId) {
        error.value = allDataResponse.message || '获取数据失败'
      }
      isLoading = false
      if (isComponentMounted && loadId === currentLoadId) {
        loading.value = false
      }
      return
    }
    
    // 检查数据格式
    if (!allDataResponse.data) {
      console.error('API 返回数据格式错误: data 字段不存在', allDataResponse)
      if (isComponentMounted && loadId === currentLoadId) {
        error.value = '数据格式错误：缺少 data 字段'
      }
      isLoading = false
      if (isComponentMounted && loadId === currentLoadId) {
        loading.value = false
      }
      return
    }
    
    // 更新可用的城市和公司类型（从全部数据中获取）
    if (isComponentMounted && loadId === currentLoadId) {
      availableCities.value = allDataResponse.data.cities || []
      availableCompanyTypes.value = allDataResponse.data.company_types || []
    }
    
    // 检查是否有数据
    const hasCityData = allDataResponse.data.city_data && allDataResponse.data.city_data.length > 0
    const hasCompanyTypeData = allDataResponse.data.company_type_data && allDataResponse.data.company_type_data.length > 0
    
    if (!hasCityData && !hasCompanyTypeData) {
      console.warn('该组合没有数据，将显示"暂无数据":', {
        experience: props.experience,
        education: props.education,
        city_data: allDataResponse.data.city_data,
        company_type_data: allDataResponse.data.company_type_data,
        full_response: allDataResponse
      })
      // 即使没有数据，也继续执行，让 renderBoxplot 显示"暂无数据"
    }
    
    // 如果有筛选条件，获取筛选后的数据用于显示
    let displayDataResponse = allDataResponse
    if (filtersCity.value || filtersCompanyType.value) {
      displayDataResponse = await getBoxplotData({
        experience: props.experience,
        education: props.education,
        city: filtersCity.value,
        company_type: filtersCompanyType.value
      })
      
      // 再次检查容器和组件状态
      if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
        console.warn('组件已卸载或图表容器在加载过程中被销毁，取消渲染')
        isLoading = false
        if (isComponentMounted && loadId === currentLoadId) {
          loading.value = false
        }
        return
      }
      
      if (displayDataResponse.code !== 200) {
        if (isComponentMounted && loadId === currentLoadId) {
          error.value = displayDataResponse.message || '获取筛选数据失败'
        }
        isLoading = false
        if (isComponentMounted && loadId === currentLoadId) {
          loading.value = false
        }
        return
      }
    }
    
    const response = displayDataResponse
    
    // 等待 Vue 完成当前更新周期，确保容器稳定
    await nextTick()
    
    // 检查容器和组件状态（在设置响应式值之前）
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('组件已卸载或图表容器在更新后被销毁，取消渲染')
      isLoading = false
      pendingLoad = false
      if (isComponentMounted && loadId === currentLoadId) {
        loading.value = false
      }
      return
    }
    
    // 再次等待一个更新周期，确保所有响应式更新都已完成
    await nextTick()
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      return
    }
    
    // 渲染图表（此时数据已经获取成功，容器也存在且稳定）
    // 先渲染图表，不设置响应式数据
    console.log('准备渲染箱线图，数据:', {
      experience: props.experience,
      education: props.education,
      city_data_length: response.data?.city_data?.length || 0,
      company_type_data_length: response.data?.company_type_data?.length || 0,
      viewType: viewType.value,
      container: chartContainer.value,
      containerWidth: chartContainer.value?.offsetWidth,
      containerHeight: chartContainer.value?.offsetHeight
    })
    
    // 确保容器有尺寸后再渲染
    if (!chartContainer.value || !chartContainer.value.offsetWidth || !chartContainer.value.offsetHeight) {
      console.warn('容器尺寸为 0，等待容器准备好...')
      // 等待容器准备好
      await new Promise(resolve => {
        let retries = 0
        const checkContainer = () => {
          if (chartContainer.value && chartContainer.value.offsetWidth && chartContainer.value.offsetHeight) {
            resolve()
          } else if (retries < 10) {
            retries++
            requestAnimationFrame(checkContainer)
          } else {
            console.error('容器在 10 次重试后仍然没有尺寸')
            resolve() // 即使失败也继续，让 renderBoxplot 处理
          }
        }
        requestAnimationFrame(checkContainer)
      })
    }
    
    // 再次检查组件状态
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('在等待容器准备好后，组件状态检查失败')
      return
    }
    
    renderBoxplot(response.data)
    
    // 等待 ECharts 完成 DOM 操作和 Vue 完成图表渲染相关的 DOM 更新
    await nextTick()
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('在等待 nextTick 后，组件状态检查失败，取消后续操作')
      return
    }
    
    // 再次等待，确保 ECharts 的 DOM 操作不会与 Vue 的更新冲突
    await nextTick()
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('在第二次 nextTick 后，组件状态检查失败，取消后续操作')
      return
    }
    
    // 然后计算统计数据（这会设置 stats.value）
    calculateStats(response.data)
    
    // 等待 Vue 完成 stats 的响应式更新
    await nextTick()
    if (!isComponentMounted || !chartContainer.value || !chartContainer.value.isConnected || loadId !== currentLoadId) {
      console.warn('在计算统计数据后，组件状态检查失败，取消后续操作')
      return
    }
    
    // 最后设置 hasData（使用 queuePostFlushCb 确保在所有更新完成后设置）
    queuePostFlushCb(() => {
      if (isComponentMounted && chartContainer.value && chartContainer.value.isConnected && loadId === currentLoadId) {
        hasData.value = true
        console.log('箱线图渲染完成，hasData 已设置为 true')
      } else {
        console.warn('在设置 hasData 时，组件状态检查失败')
      }
    })
  } catch (err) {
    console.error('加载箱线图失败:', err)
    if (isComponentMounted && loadId === currentLoadId) {
      error.value = err.message || '加载失败'
    }
  } finally {
    // 使用 nextTick 确保在 Vue 完成 DOM 更新后再设置响应式值
    await nextTick()
    // 只有在组件仍然挂载且是当前请求时才设置响应式值
    if (isComponentMounted && loadId === currentLoadId) {
      isLoading = false
      loading.value = false
      pendingLoad = false
    } else if (loadId !== currentLoadId) {
      // 如果不是当前请求，只重置 isLoading 标志
      isLoading = false
    }
  }
}

const renderBoxplot = (data) => {
  // 检查组件状态和容器
  if (!isComponentMounted) {
    console.warn('组件已卸载，跳过渲染')
    return
  }
  
  if (!chartContainer.value) {
    console.warn('箱线图容器不存在，跳过渲染')
    return
  }
  
  // 保存容器引用，避免在清理过程中容器被替换
  const container = chartContainer.value
  if (!container || !container.isConnected) {
    console.warn('箱线图容器无效或已从 DOM 移除，跳过渲染')
    return
  }
  
  // 检查容器尺寸，ECharts 需要容器有尺寸才能初始化
  const containerWidth = container.offsetWidth || container.clientWidth
  const containerHeight = container.offsetHeight || container.clientHeight
  
  if (!containerWidth || !containerHeight) {
    console.warn('容器尺寸为 0，无法初始化图表:', {
      offsetWidth: container.offsetWidth,
      offsetHeight: container.offsetHeight,
      clientWidth: container.clientWidth,
      clientHeight: container.clientHeight
    })
    return
  }
  
  // 只有在确认能够创建新图表后，才清理旧图表
  // 这样可以避免在清理后无法创建新图表的情况
  let oldChart = null
  if (boxplotChart) {
    oldChart = boxplotChart
    // 先检查旧图表是否还在使用这个容器
    try {
      const oldDom = oldChart.getDom && oldChart.getDom()
      if (oldDom === container) {
        // 如果旧图表还在使用这个容器，先清理
        try {
          oldChart.dispose()
        } catch (e) {
          console.warn('清理旧图表时出错:', e)
        }
      }
    } catch (e) {
      console.warn('检查旧图表时出错:', e)
    }
    boxplotChart = null // 清空引用
  }
  
  // 初始化新图表
  try {
    console.log('开始初始化 ECharts 图表，容器尺寸:', {
      width: containerWidth,
      height: containerHeight,
      container: container
    })
    
    boxplotChart = echarts.init(container)
    
    if (!boxplotChart) {
      console.error('图表初始化返回 null，容器:', container)
      // 如果初始化失败，恢复旧图表（如果有）
      boxplotChart = oldChart
      return
    }
    
    // 验证图表实例是否有效
    try {
      const chartDom = boxplotChart.getDom && boxplotChart.getDom()
      if (!chartDom) {
        console.error('图表实例的 DOM 为空')
        boxplotChart.dispose()
        boxplotChart = null
        boxplotChart = oldChart
        return
      }
      console.log('图表初始化成功，实例 ID:', boxplotChart.id)
    } catch (e) {
      console.error('验证图表实例时出错:', e)
      if (boxplotChart) {
        try {
          boxplotChart.dispose()
        } catch (disposeErr) {
          console.warn('清理无效图表实例时出错:', disposeErr)
        }
      }
      boxplotChart = null
      boxplotChart = oldChart
      return
    }
  } catch (e) {
    console.error('初始化图表失败，错误详情:', {
      error: e,
      message: e.message,
      stack: e.stack,
      container: container,
      containerWidth: containerWidth,
      containerHeight: containerHeight
    })
    // 如果初始化失败，恢复旧图表（如果有）
    boxplotChart = oldChart
    return
  }
  
  // 只有在成功创建新图表后，才清理旧图表
  if (oldChart) {
    try {
      // 检查图表实例是否仍然有效
      if (oldChart.getDom && oldChart.getDom()) {
        oldChart.dispose()
      }
    } catch (e) {
      console.warn('清理旧图表时出错:', e)
    }
  }
  
  // 根据视图类型选择数据
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    console.warn('数据源为空:', {
      viewType: viewType.value,
      city_data: data.city_data,
      company_type_data: data.company_type_data
    })
    boxplotChart.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          fontSize: 16,
          color: '#999'
        }
      }
    })
    return
  }
  
  // 验证数据格式并准备箱线图数据
  // ECharts箱线图数据格式：[min, Q1, median, Q3, max]
  const boxplotData = []
  const categories = []
  const validItems = []
  
  for (const item of dataSource) {
    if (!item || !item.stats) {
      console.warn('数据项格式错误，缺少 stats 字段:', item)
      continue
    }
    
    const stats = item.stats
    if (typeof stats.min !== 'number' || 
        typeof stats.q1 !== 'number' || 
        typeof stats.median !== 'number' || 
        typeof stats.q3 !== 'number' || 
        typeof stats.max !== 'number') {
      console.warn('数据项 stats 格式错误:', item)
      continue
    }
    
    boxplotData.push([stats.min, stats.q1, stats.median, stats.q3, stats.max])
    categories.push(item.name || '未知')
    validItems.push(item)
  }
  
  if (boxplotData.length === 0) {
    console.warn('没有有效的数据项')
    boxplotChart.setOption({
      title: {
        text: '数据格式错误',
        left: 'center',
        top: 'center',
        textStyle: {
          fontSize: 16,
          color: '#f56c6c'
        }
      }
    })
    return
  }
  
  // 使用有效的数据项
  const dataSourceForTooltip = validItems
  
  // 构建标题文本
  let titleText = viewType.value === 'city' ? '不同城市薪资分布分析' : '不同公司类型薪资分布分析'
  let subtitleParts = [`${props.experience} × ${props.education}`]
  if (filtersCity.value) {
    subtitleParts.push(`城市: ${filtersCity.value}`)
  }
  if (filtersCompanyType.value) {
    subtitleParts.push(`公司: ${filtersCompanyType.value}`)
  }
  
  const option = {
    backgroundColor: '#fafafa',
    title: {
      text: titleText,
      subtext: subtitleParts.join(' | '),
      left: 'center',
      top: 15,
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      subtextStyle: {
        fontSize: 13,
        color: '#7f8c8d'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      borderColor: '#67C23A',
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 13
      },
      formatter: function(params) {
        const index = params.dataIndex
        const item = dataSourceForTooltip[index]
        if (!item || !item.stats) return ''
        
        const stats = item.stats
        const iqr = (stats.q3 - stats.q1).toFixed(2)
        const range = (stats.max - stats.min).toFixed(2)
        
        return `
          <div style="padding: 12px;">
            <div style="font-size: 15px; font-weight: bold; margin-bottom: 10px; color: #67C23A; border-bottom: 2px solid #67C23A; padding-bottom: 6px;">
              ${item.name}
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span>📊 样本数量：</span>
              <strong style="color: #409EFF;">${stats.count} 个</strong>
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span>⬇️ 最小值：</span>
              <strong>${stats.min}K</strong>
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span style="color: #E6A23C;">📦 下四分位(Q1)：</span>
              <strong style="color: #E6A23C;">${stats.q1}K</strong>
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span style="color: #F56C6C;">🎯 中位数：</span>
              <strong style="color: #F56C6C; font-size: 15px;">${stats.median}K</strong>
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span style="color: #E6A23C;">📦 上四分位(Q3)：</span>
              <strong style="color: #E6A23C;">${stats.q3}K</strong>
            </div>
            <div style="margin: 6px 0; display: flex; justify-content: space-between;">
              <span>⬆️ 最大值：</span>
              <strong>${stats.max}K</strong>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 11px;">
              <div style="color: #aaa;">四分位距(IQR): ${iqr}K</div>
              <div style="color: #aaa;">全距(Range): ${range}K</div>
            </div>
          </div>
        `
      }
    },
    grid: {
      left: '12%',
      right: '8%',
      bottom: '18%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      name: viewType.value === 'city' ? '城市' : '公司类型',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        fontSize: 15,
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      axisLabel: {
        rotate: categories.length > 8 ? -45 : 0,
        interval: 0,
        fontSize: 13,
        color: '#555',
        fontWeight: '500',
        margin: 15
      },
      axisLine: {
        lineStyle: {
          color: '#666',
          width: 2
        }
      },
      axisTick: {
        lineStyle: {
          color: '#666',
          width: 1.5
        },
        length: 6
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: 'rgba(200, 200, 200, 0.2)',
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '薪资(千元)',
      nameTextStyle: {
        fontSize: 15,
        fontWeight: 'bold',
        color: '#2c3e50'
      },
      axisLabel: {
        formatter: '{value}K',
        fontSize: 12,
        color: '#555'
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: '#666',
          width: 2
        }
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: '#666'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(200, 200, 200, 0.25)',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '薪资分布',
        type: 'boxplot',
        data: boxplotData.map((item, index) => ({
          value: item,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(84, 112, 198, 0.85)' },
                { offset: 0.5, color: 'rgba(84, 112, 198, 0.7)' },
                { offset: 1, color: 'rgba(84, 112, 198, 0.95)' }
              ]
            },
            borderColor: '#2c3e50',
            borderWidth: 2,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5
          }
        })),
        boxWidth: ['40%', '80%'],
        emphasis: {
          itemStyle: {
            borderColor: '#E6A23C',
            borderWidth: 3,
            shadowBlur: 15,
            shadowOffsetY: 8
          },
          scale: true
        },
        animationDuration: 1500,
        animationEasing: 'cubicOut',
        animationDelay: function(idx) {
          return idx * 100
        }
      },
      // 添加散点图显示中位数
      {
        name: '中位数',
        type: 'scatter',
        data: dataSource.map((item, index) => [index, item.stats.median]),
        symbolSize: 12,
        symbol: 'pin',
        itemStyle: {
          color: '#F56C6C',
          borderColor: '#fff',
          borderWidth: 2,
          shadowColor: 'rgba(245, 108, 108, 0.5)',
          shadowBlur: 10
        },
        emphasis: {
          itemStyle: {
            color: '#FF5252',
            shadowBlur: 15
          },
          scale: true,
          scaleSize: 15
        },
        label: {
          show: true,
          formatter: function(params) {
            return params.value[1].toFixed(1) + 'K'
          },
          position: 'top',
          fontSize: 11,
          fontWeight: 'bold',
          color: '#F56C6C',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: [3, 6],
          borderRadius: 3,
          borderColor: '#F56C6C',
          borderWidth: 1
        },
        animationDuration: 1000,
        animationDelay: function(idx) {
          return idx * 100 + 800
        }
      },
      // 添加中位数平均线
      {
        name: '',
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: {
            color: '#67C23A',
            type: 'dashed',
            width: 2
          },
          label: {
            show: true,
            position: 'end',
            formatter: function() {
              const avgMedian = dataSourceForTooltip.reduce((sum, item) => sum + item.stats.median, 0) / dataSourceForTooltip.length
              return `中位数: ${avgMedian.toFixed(1)}K`
            },
            fontSize: 11,
            color: '#67C23A',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            padding: [3, 6],
            borderRadius: 3
          },
          data: [{
            name: '',
            yAxis: dataSourceForTooltip.reduce((sum, item) => sum + item.stats.median, 0) / dataSourceForTooltip.length
          }]
        }
      }
    ]
  }
  
  try {
    boxplotChart.setOption(option, true)
  } catch (e) {
    console.error('设置图表选项失败:', e)
    return
  }
  
  // 窗口大小改变时重新调整图表
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  
  resizeHandler = () => {
    // 检查图表和容器是否还存在
    if (boxplotChart && chartContainer.value) {
      try {
        boxplotChart.resize()
      } catch (e) {
        console.warn('调整图表大小时出错:', e)
      }
    }
  }
  
  window.addEventListener('resize', resizeHandler)
}

const calculateStats = (data) => {
  if (!isComponentMounted) {
    return
  }
  
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    if (isComponentMounted) {
      // 使用 queuePostFlushCb 确保在 Vue 更新队列清空后设置
      queuePostFlushCb(() => {
        if (isComponentMounted) {
          stats.value = null
        }
      })
    }
    return
  }
  
  let totalCount = 0
  let totalSalary = 0
  
  dataSource.forEach(item => {
    if (item.stats) {
      totalCount += item.stats.count
      totalSalary += item.stats.median * item.stats.count
    }
  })
  
  if (isComponentMounted) {
    // 使用 queuePostFlushCb 确保在 Vue 更新队列清空后设置
    queuePostFlushCb(() => {
      if (isComponentMounted) {
        stats.value = {
          total_count: totalCount,
          avg_salary: totalCount > 0 ? (totalSalary / totalCount).toFixed(2) : '0'
        }
      }
    })
  }
}

// 组件挂载后，如果有待处理的加载请求，执行它
onMounted(() => {
  // 确保组件已挂载
  isComponentMounted = true
  
  // 如果 props 已经有值，等待容器准备好后加载
  if (props.experience && props.education && chartContainer.value) {
    nextTick(() => {
      if (isComponentMounted && pendingLoad && !isLoading) {
        pendingLoad = false
        handleLoad()
      }
    })
  }
})

onUnmounted(() => {
  // 标记组件已卸载，阻止所有后续操作
  isComponentMounted = false
  
  // 清理图表实例
  if (boxplotChart) {
    try {
      boxplotChart.dispose()
    } catch (e) {
      console.warn('销毁图表时出错:', e)
    }
    boxplotChart = null
  }
  
  // 清理事件监听器
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  
  // 清理 watch 监听器
  if (propsWatchStop) {
    propsWatchStop()
    propsWatchStop = null
  }
  
  if (cityWatchStop) {
    cityWatchStop()
    cityWatchStop = null
  }
  
  if (companyTypeWatchStop) {
    companyTypeWatchStop()
    companyTypeWatchStop = null
  }
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 600px;
  margin-top: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.chart-container:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

.chart-container.loading-state {
  pointer-events: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(250, 250, 250, 0.95);
  backdrop-filter: blur(2px);
  z-index: 10;
  border-radius: 12px;
}

.filter-section {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  align-items: flex-end;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-size: 14px;
  color: #495057;
  font-weight: 600;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  min-width: 150px;
  cursor: pointer;
}

.filter-select:hover {
  border-color: #5470c6;
}

.filter-select:focus {
  outline: none;
  border-color: #5470c6;
  box-shadow: 0 0 0 2px rgba(84, 112, 198, 0.2);
}

.selected-value {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
  font-weight: 500;
}

.selected-value.selected {
  border: 2px solid #5470c6;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1565c0;
  box-shadow: 0 2px 6px rgba(84, 112, 198, 0.2);
}

.selected-value.not-selected {
  border: 1px solid #ddd;
  background: #f5f5f5;
  color: #999;
  font-style: italic;
}

.info-tip {
  padding: 15px 20px;
  background: linear-gradient(135deg, #fff9e6 0%, #ffe9a0 100%);
  border: 2px solid #ffc107;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #856404;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.2);
}

.info-tip p {
  margin: 0;
  font-size: 14px;
}

.btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #5470c6 0%, #4558a3 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 6px rgba(84, 112, 198, 0.3);
}

.btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4558a3 0%, #3a4a8e 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(84, 112, 198, 0.4);
}

.btn:disabled {
  background: linear-gradient(135deg, #ccc 0%, #bbb 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.filter-select:disabled {
  background: #f0f0f0;
  color: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.filter-info {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 10px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #5470c6;
  border-radius: 20px;
  font-size: 13px;
  color: #1565c0;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(84, 112, 198, 0.15);
}

.clear-btn {
  background: none;
  border: none;
  color: #1565c0;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  margin: 0;
  line-height: 1;
  transition: color 0.2s;
}

.clear-btn:hover {
  color: #f44336;
}

.loading-overlay p {
  color: #666;
  font-size: 14px;
  margin-top: 15px;
  font-weight: 500;
}

.spinner {
  border: 4px solid rgba(84, 112, 198, 0.1);
  border-top: 4px solid #5470c6;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result.error {
  background: linear-gradient(135deg, #fee 0%, #fdd 100%);
  border: 2px solid #f44336;
  color: #c33;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.2);
}

.result.error pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>


