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
          v-model="filters.city" 
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
          v-model="filters.company_type" 
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
        <span v-if="filters.city" class="filter-tag">
          📍 {{ filters.city }}
          <button @click="filters.city = ''" class="clear-btn">✕</button>
        </span>
        <span v-if="filters.company_type" class="filter-tag">
          🏢 {{ filters.company_type }}
          <button @click="filters.company_type = ''" class="clear-btn">✕</button>
        </span>
      </div>
    </div>
    
    <div v-if="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div ref="chartContainer" id="boxplot-container" class="chart-container" :class="{ 'loading-state': loading }">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>正在加载数据...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, onMounted, nextTick, watch } from 'vue'
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

const filters = ref({
  experience: '',
  education: '',
  city: '',
  company_type: ''
})

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

// 监听props变化，更新filters并自动加载
watch(() => props.experience, (val) => {
  if (val) {
    filters.value.experience = val
    // 如果两个参数都有了，延迟加载（确保容器已准备好）
    if (filters.value.experience && filters.value.education) {
      pendingLoad = true
      nextTick(() => {
        if (pendingLoad && !isLoading && chartContainer.value) {
          pendingLoad = false
          handleLoad()
        }
      })
    }
  }
}, { immediate: true })

watch(() => props.education, (val) => {
  if (val) {
    filters.value.education = val
    // 如果两个参数都有了，延迟加载（确保容器已准备好）
    if (filters.value.experience && filters.value.education) {
      pendingLoad = true
      nextTick(() => {
        if (pendingLoad && !isLoading && chartContainer.value) {
          pendingLoad = false
          handleLoad()
        }
      })
    }
  }
}, { immediate: true })

// 监听视图类型变化
watch(viewType, () => {
  if (hasData.value && filters.value.experience && filters.value.education && !isLoading) {
    handleLoad()
  }
})

// 监听城市筛选变化 - 自动刷新
const cityWatchStop = watch(() => filters.value.city, (newVal, oldVal) => {
  // 只有在已有数据且城市确实改变时才刷新
  if (hasData.value && filters.value.experience && filters.value.education && newVal !== oldVal && !isLoading) {
    handleLoad()
  }
})

// 监听公司类型筛选变化 - 自动刷新
const companyTypeWatchStop = watch(() => filters.value.company_type, (newVal, oldVal) => {
  // 只有在已有数据且公司类型确实改变时才刷新
  if (hasData.value && filters.value.experience && filters.value.education && newVal !== oldVal && !isLoading) {
    handleLoad()
  }
})

const handleLoad = async () => {
  // 防止重复加载
  if (isLoading) {
    console.log('正在加载中，跳过重复请求')
    return
  }
  
  try {
    // 验证必填参数
    if (!filters.value.experience || !filters.value.education) {
      error.value = '请先点击3D图表中的柱体选择工作经验和学历要求'
      return
    }
    
    // 检查容器是否存在
    if (!chartContainer.value) {
      console.warn('图表容器不存在，等待容器准备...')
      // 等待容器准备好
      await nextTick()
      if (!chartContainer.value) {
        console.warn('图表容器仍未准备好，跳过加载')
        return
      }
    }
    
    isLoading = true
    loading.value = true
    error.value = null
    
    // 获取全部数据（不带city和company_type筛选）以获取完整的选项列表
    const allDataFilters = {
      experience: filters.value.experience,
      education: filters.value.education
    }
    const allDataResponse = await getBoxplotData(allDataFilters)
    
    // 再次检查容器（可能在异步操作期间被销毁）
    if (!chartContainer.value) {
      console.warn('图表容器在加载过程中被销毁，取消渲染')
      return
    }
    
    if (allDataResponse.code !== 200) {
      error.value = allDataResponse.message || '获取数据失败'
      return
    }
    
    // 更新可用的城市和公司类型（从全部数据中获取）
    availableCities.value = allDataResponse.data.cities || []
    availableCompanyTypes.value = allDataResponse.data.company_types || []
    
    // 如果有筛选条件，获取筛选后的数据用于显示
    let displayDataResponse = allDataResponse
    if (filters.value.city || filters.value.company_type) {
      displayDataResponse = await getBoxplotData(filters.value)
      
      // 再次检查容器
      if (!chartContainer.value) {
        console.warn('图表容器在加载过程中被销毁，取消渲染')
        return
      }
      
      if (displayDataResponse.code !== 200) {
        error.value = displayDataResponse.message || '获取筛选数据失败'
        return
      }
    }
    
    const response = displayDataResponse
    
    // 设置数据标记，让容器显示
    hasData.value = true
    
    // 等待 DOM 更新
    await nextTick()
    
    // 再次检查容器
    if (!chartContainer.value) {
      console.warn('图表容器在DOM更新后被销毁，取消渲染')
      return
    }
    
    // 再次等待确保容器已渲染
    setTimeout(() => {
      // 最终检查容器
      if (!chartContainer.value) {
        console.warn('图表容器在延迟后被销毁，取消渲染')
        return
      }
      renderBoxplot(response.data)
      calculateStats(response.data)
    }, 100)
  } catch (err) {
    console.error('加载箱线图失败:', err)
    error.value = err.message || '加载失败'
  } finally {
    isLoading = false
    loading.value = false
    pendingLoad = false
  }
}

const renderBoxplot = (data) => {
  // 检查容器是否存在
  if (!chartContainer.value) {
    console.warn('箱线图容器不存在，跳过渲染')
    return
  }
  
  const container = chartContainer.value
  if (!container) {
    console.error('箱线图容器不存在')
    return
  }
  
  // 清理旧图表
  if (boxplotChart) {
    try {
      boxplotChart.dispose()
    } catch (e) {
      console.warn('清理旧图表时出错:', e)
    }
    boxplotChart = null
  }
  
  // 初始化新图表
  try {
    boxplotChart = echarts.init(container)
  } catch (e) {
    console.error('初始化图表失败:', e)
    return
  }
  
  // 根据视图类型选择数据
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    boxplotChart.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center'
      }
    })
    return
  }
  
  // 准备箱线图数据
  // ECharts箱线图数据格式：[min, Q1, median, Q3, max]
  const boxplotData = dataSource.map(item => {
    const stats = item.stats
    return [stats.min, stats.q1, stats.median, stats.q3, stats.max]
  })
  const categories = dataSource.map(item => item.name)
  
  // 构建标题文本
  let titleText = viewType.value === 'city' ? '不同城市薪资分布分析' : '不同公司类型薪资分布分析'
  let subtitleParts = [`${filters.value.experience} × ${filters.value.education}`]
  if (filters.value.city) {
    subtitleParts.push(`城市: ${filters.value.city}`)
  }
  if (filters.value.company_type) {
    subtitleParts.push(`公司: ${filters.value.company_type}`)
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
        const item = dataSource[index]
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
      // 添加平均线
      {
        name: '平均值',
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
            position: 'end',
            formatter: function() {
              const totalMedian = dataSource.reduce((sum, item) => sum + item.stats.median, 0) / dataSource.length
              return `平均: ${totalMedian.toFixed(1)}K`
            },
            fontSize: 11,
            color: '#67C23A',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            padding: [3, 6],
            borderRadius: 3
          },
          data: [{
            yAxis: dataSource.reduce((sum, item) => sum + item.stats.median, 0) / dataSource.length
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
  const dataSource = viewType.value === 'city' ? data.city_data : data.company_type_data
  
  if (!dataSource || dataSource.length === 0) {
    stats.value = null
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
  
  stats.value = {
    total_count: totalCount,
    avg_salary: totalCount > 0 ? (totalSalary / totalCount).toFixed(2) : '0'
  }
}

// 组件挂载后，如果有待处理的加载请求，执行它
onMounted(() => {
  // 如果 props 已经有值，等待容器准备好后加载
  if (props.experience && props.education && chartContainer.value) {
    nextTick(() => {
      if (pendingLoad && !isLoading) {
        pendingLoad = false
        handleLoad()
      }
    })
  }
})

onUnmounted(() => {
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

