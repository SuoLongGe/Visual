<template>
  <div class="q2-tab">
    <div class="page-header">
      <h2>职位画像分析</h2>
      <div class="layout-toggle">
        <button 
          :class="['layout-btn', { active: layoutMode === 'grid' }]"
          @click="layoutMode = 'grid'"
          title="网格布局"
        >
          <span>⊞</span> 网格
        </button>
        <button 
          :class="['layout-btn', { active: layoutMode === 'tabs' }]"
          @click="layoutMode = 'tabs'"
          title="标签页布局"
        >
          <span>☰</span> 标签
        </button>
      </div>
    </div>
    
    <!-- 标签页模式 -->
    <div v-if="layoutMode === 'tabs'" class="view-tabs">
      <button 
        :class="['view-tab', { active: currentView === 'parallel' }]"
        @click="currentView = 'parallel'"
      >
        视图一：平行坐标图
      </button>
      <button 
        :class="['view-tab', { active: currentView === 'sankey' }]"
        @click="currentView = 'sankey'"
      >
        视图二：桑基图
      </button>
      <button 
        :class="['view-tab', { active: currentView === 'nested' }]"
        @click="currentView = 'nested'"
      >
        视图三：嵌套柱状图
      </button>
    </div>
    
    <!-- 网格布局模式 -->
    <div v-if="layoutMode === 'grid'" class="grid-layout-wrapper">
      <!-- 统一职位选择器 -->
      <div class="unified-job-selector">
        <div class="selector-header">
          <h3>🎯 统一职位选择</h3>
          <p class="selector-hint">在此输入职位，自动同步到所有视图</p>
        </div>
        <div class="selector-body">
          <div class="unified-inputs">
            <div class="input-group">
              <label>职位1</label>
              <input v-model="unifiedJobs[0]" type="text" placeholder="例如：数据分析师" class="unified-input" />
            </div>
            <div class="input-group">
              <label>职位2</label>
              <input v-model="unifiedJobs[1]" type="text" placeholder="例如：算法工程师" class="unified-input" />
            </div>
            <div class="input-group">
              <label>职位3</label>
              <input v-model="unifiedJobs[2]" type="text" placeholder="例如：机器学习工程师" class="unified-input" />
            </div>
          </div>
          <div class="unified-actions">
            <button @click="syncToAllViews" :disabled="!hasUnifiedJobs" class="unified-btn unified-btn-sync">
              <span>🔄</span> 同步到所有视图
            </button>
            <button @click="loadAllViews" :disabled="!hasUnifiedJobs" class="unified-btn unified-btn-load">
              <span>⚡</span> 一键生成全部
            </button>
            <button @click="clearAllJobs" class="unified-btn unified-btn-clear">
              <span>🗑️</span> 清空全部
            </button>
          </div>
        </div>
      </div>

      <!-- 三个视图 -->
      <div class="grid-layout">
      <!-- 视图一：平行坐标图 -->
      <div class="grid-item" @drop="handleDrop($event, 'parallel')" @dragover.prevent>
        <div class="grid-header">
          <span class="grid-title">📊 平行坐标图</span>
          <button class="expand-btn" @click="expandView('parallel')" title="展开">⤢</button>
        </div>
        <div class="grid-content-compact">
          <div class="compact-controls">
            <div class="compact-inputs">
              <div class="draggable-input-wrapper">
                <input 
                  v-model="selectedJobs[0]" 
                  type="text" 
                  placeholder="职位1" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, selectedJobs[0])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="selectedJobs[1]" 
                  type="text" 
                  placeholder="职位2" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, selectedJobs[1])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="selectedJobs[2]" 
                  type="text" 
                  placeholder="职位3" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, selectedJobs[2])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
            </div>
            <div class="compact-actions">
              <button @click="loadData" :disabled="!hasValidJobs" class="compact-btn compact-btn-primary">生成</button>
              <button @click="clearSelection" class="compact-btn compact-btn-secondary">清除</button>
            </div>
          </div>
          <div class="compact-chart">
            <PositionParallelChart 
              :data="chartData?.data"
              :loading="loading"
              :error="error"
            />
          </div>
        </div>
      </div>
      
      <!-- 视图二：桑基图 -->
      <div class="grid-item" @drop="handleDrop($event, 'sankey')" @dragover.prevent>
        <div class="grid-header">
          <span class="grid-title">🔀 桑基图</span>
          <button class="expand-btn" @click="expandView('sankey')" title="展开">⤢</button>
        </div>
        <div class="grid-content-compact">
          <div class="compact-controls">
            <div class="compact-mode">
              <label><input type="radio" v-model="sankeyMode" value="all" @change="handleModeChange" /> 整体</label>
              <label><input type="radio" v-model="sankeyMode" value="compare" @change="handleModeChange" /> 对比</label>
            </div>
            <div v-if="sankeyMode === 'compare'" class="compact-inputs">
              <div class="draggable-input-wrapper">
                <input 
                  v-model="sankeyJobs[0]" 
                  type="text" 
                  placeholder="职位1" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, sankeyJobs[0])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="sankeyJobs[1]" 
                  type="text" 
                  placeholder="职位2" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, sankeyJobs[1])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="sankeyJobs[2]" 
                  type="text" 
                  placeholder="职位3" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, sankeyJobs[2])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
            </div>
            <div class="compact-actions">
              <button @click="loadSankeyData" class="compact-btn compact-btn-primary">生成</button>
              <button @click="clearSankeySelection" class="compact-btn compact-btn-secondary">清除</button>
            </div>
          </div>
          <div class="compact-chart">
            <SankeyChart 
              :data="sankeyData?.data"
              :loading="sankeyLoading"
              :error="sankeyError"
            />
          </div>
        </div>
      </div>
      
      <!-- 视图三：嵌套柱状图 -->
      <div class="grid-item grid-item-full" @drop="handleDrop($event, 'nested')" @dragover.prevent>
        <div class="grid-header">
          <span class="grid-title">📈 嵌套柱状图</span>
          <button class="expand-btn" @click="expandView('nested')" title="展开">⤢</button>
        </div>
        <div class="grid-content-compact grid-content-wide">
          <div class="compact-controls">
            <div class="compact-inputs">
              <div class="draggable-input-wrapper">
                <input 
                  v-model="nestedJobs[0]" 
                  type="text" 
                  placeholder="职位1" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, nestedJobs[0])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="nestedJobs[1]" 
                  type="text" 
                  placeholder="职位2" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, nestedJobs[1])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
              <div class="draggable-input-wrapper">
                <input 
                  v-model="nestedJobs[2]" 
                  type="text" 
                  placeholder="职位3" 
                  class="compact-input draggable-input"
                  draggable="true"
                  @dragstart="handleDragStart($event, nestedJobs[2])"
                />
                <span class="drag-handle">⋮⋮</span>
              </div>
            </div>
            <div class="compact-actions">
              <button @click="loadNestedData(null)" :disabled="!hasValidNestedJobs" class="compact-btn compact-btn-primary">生成</button>
              <button v-if="selectedDetailJob" @click="backToMacro" class="compact-btn compact-btn-warning">返回宏观</button>
              <button @click="clearNestedSelection" class="compact-btn compact-btn-secondary">清除</button>
            </div>
          </div>
          <div class="compact-chart">
            <NestedBarChart 
              :data="nestedData?.data"
              :loading="nestedLoading"
              :error="nestedError"
              @selectJob="handleSelectDetailJob"
            />
          </div>
        </div>
      </div>
    </div>
    </div>
    
    <!-- 标签页模式 - 视图一：平行坐标图 -->
    <div v-if="layoutMode === 'tabs' && currentView === 'parallel'" class="view-content">
      <p class="chart-description">
        从多角度展示职位画像，包括薪资待遇、技能要求、行业集中度、职业热度四个维度。
        <br/>
        <strong>💡 提示：请选择最多3个职位进行对比分析</strong>
      </p>
    
    <!-- 职位选择区域 -->
    <div class="job-selector">
      <div class="selector-group">
        <label>职位1：</label>
        <input 
          v-model="selectedJobs[0]" 
          type="text" 
          class="job-input"
          placeholder="输入职位名称"
          @input="handleJobInput(0)"
        />
      </div>
      <div class="selector-group">
        <label>职位2：</label>
        <input 
          v-model="selectedJobs[1]" 
          type="text" 
          class="job-input"
          placeholder="输入职位名称（可选）"
          @input="handleJobInput(1)"
        />
      </div>
      <div class="selector-group">
        <label>职位3：</label>
        <input 
          v-model="selectedJobs[2]" 
          type="text" 
          class="job-input"
          placeholder="输入职位名称（可选）"
          @input="handleJobInput(2)"
        />
      </div>
      <div class="selector-actions">
        <button 
          class="btn btn-primary" 
          @click="loadData"
          :disabled="loading || !hasValidJobs"
        >
          {{ loading ? '加载中...' : '生成平行坐标图' }}
        </button>
        <button 
          class="btn btn-secondary" 
          @click="clearSelection"
          :disabled="loading"
        >
          清除选择
        </button>
      </div>
    </div>
    
      <!-- 图表区域 -->
      <div class="chart-section">
        <PositionParallelChart 
          :data="chartData?.data"
          :loading="loading"
          :error="error"
        />
      </div>
    </div>
    
    <!-- 标签页模式 - 视图二：桑基图 -->
    <div v-if="layoutMode === 'tabs' && currentView === 'sankey'" class="view-content">
      <p class="chart-description">
        展示职位特征到薪资结果的流动路径，揭示技能要求、行业特性、市场需求与薪酬结果之间的转化关系。
        <br/>
        <strong>💡 提示：可选择整体模式查看所有职位，或对比模式查看特定职位</strong>
      </p>
      
      <!-- 模式选择 -->
      <div class="mode-selector">
        <div class="mode-group">
          <label>
            <input 
              type="radio" 
              v-model="sankeyMode" 
              value="all"
              @change="handleModeChange"
            />
            整体模式（展示所有职位）
          </label>
          <label>
            <input 
              type="radio" 
              v-model="sankeyMode" 
              value="compare"
              @change="handleModeChange"
            />
            对比模式（选择特定职位）
          </label>
        </div>
        
        <!-- 维度选择 -->
        <div class="dimension-selector">
          <div class="dimension-title">选择维度（至少2个）：</div>
          <div class="dimension-group">
            <label>
              <input 
                type="checkbox" 
                v-model="selectedDimensions" 
                value="skill_level"
              />
              技能要求
            </label>
            <label>
              <input 
                type="checkbox" 
                v-model="selectedDimensions" 
                value="industry_spread"
              />
              行业分布
            </label>
            <label>
              <input 
                type="checkbox" 
                v-model="selectedDimensions" 
                value="market_demand"
              />
              市场需求
            </label>
          </div>
          <div v-if="selectedDimensions.length < 2" class="dimension-hint">
            ⚠️ 请至少选择2个维度
          </div>
        </div>
        
        <!-- 对比模式下的职位选择 -->
        <div v-if="sankeyMode === 'compare'" class="job-selector">
          <div class="selector-group">
            <label>职位1：</label>
            <input 
              v-model="sankeyJobs[0]" 
              type="text" 
              class="job-input"
              placeholder="输入职位名称"
            />
          </div>
          <div class="selector-group">
            <label>职位2：</label>
            <input 
              v-model="sankeyJobs[1]" 
              type="text" 
              class="job-input"
              placeholder="输入职位名称（可选）"
            />
          </div>
          <div class="selector-group">
            <label>职位3：</label>
            <input 
              v-model="sankeyJobs[2]" 
              type="text" 
              class="job-input"
              placeholder="输入职位名称（可选）"
            />
          </div>
        </div>
        
        <div class="selector-actions">
          <button 
            class="btn btn-primary" 
            @click="loadSankeyData"
            :disabled="sankeyLoading || selectedDimensions.length < 2 || (sankeyMode === 'compare' && !hasValidSankeyJobs)"
          >
            {{ sankeyLoading ? '加载中...' : '生成桑基图' }}
          </button>
          <button 
            class="btn btn-secondary" 
            @click="clearSankeySelection"
            :disabled="sankeyLoading"
          >
            清除
          </button>
        </div>
      </div>
      
      <!-- 桑基图区域 -->
      <div class="chart-section">
        <SankeyChart 
          :data="sankeyData?.data"
          :loading="sankeyLoading"
          :error="sankeyError"
          :emptyMessage="sankeyMode === 'all' ? '点击【生成桑基图】查看整体数据' : '请选择职位并点击【生成桑基图】'"
        />
      </div>
    </div>
    
    <!-- 标签页模式 - 视图三：嵌套柱状图 -->
    <div v-if="layoutMode === 'tabs' && currentView === 'nested'" class="view-content">
      <p class="chart-description">
        多维度嵌套柱状图，柱子高度表示综合技能分数，内部点状图密集度表示行业集中度。
        <br/>
        <strong>💡 提示：鼠标悬停查看详细信息（薪资、经验、学历、行业集中度），点击柱子查看薪资分布详情</strong>
      </p>
      
      <!-- 职位选择 -->
      <div class="job-selector">
        <div class="selector-group">
          <label>职位1：</label>
          <input 
            v-model="nestedJobs[0]" 
            type="text" 
            class="job-input"
            placeholder="输入职位名称"
          />
        </div>
        <div class="selector-group">
          <label>职位2：</label>
          <input 
            v-model="nestedJobs[1]" 
            type="text" 
            class="job-input"
            placeholder="输入职位名称（可选）"
          />
        </div>
        <div class="selector-group">
          <label>职位3：</label>
          <input 
            v-model="nestedJobs[2]" 
            type="text" 
            class="job-input"
            placeholder="输入职位名称（可选）"
          />
        </div>
        
        <div class="selector-actions">
          <button 
            class="btn btn-primary" 
            @click="loadNestedData(null)"
            :disabled="nestedLoading || !hasValidNestedJobs"
          >
            {{ nestedLoading ? '加载中...' : '生成柱状图' }}
          </button>
          <button 
            class="btn btn-secondary" 
            @click="clearNestedSelection"
            :disabled="nestedLoading"
          >
            清除
          </button>
          <button 
            v-if="selectedDetailJob"
            class="btn btn-secondary" 
            @click="backToMacro"
            :disabled="nestedLoading"
          >
            返回宏观对比
          </button>
        </div>
      </div>
      
      <!-- 嵌套柱状图区域 -->
      <div class="chart-section">
        <NestedBarChart 
          :data="nestedData?.data"
          :loading="nestedLoading"
          :error="nestedError"
          @selectJob="handleSelectDetailJob"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFetchData } from '@/utils/fetchData.js'
import { getParallelCoordinatesData, getSankeyData, getNestedBarData } from '@/api/positionApi.js'
import PositionParallelChart from '@/components/charts/PositionParallelChart.vue'
import SankeyChart from '@/components/charts/SankeyChart.vue'
import NestedBarChart from '@/components/charts/NestedBarChart.vue'

// 布局模式切换
const layoutMode = ref('tabs') // 'tabs' 或 'grid'

// 视图切换
const currentView = ref('parallel')

// 统一职位管理
const unifiedJobs = ref(['', '', ''])

// 检查是否有统一职位
const hasUnifiedJobs = computed(() => {
  return unifiedJobs.value.some(job => job && job.trim())
})

// 同步职位到所有视图
const syncToAllViews = () => {
  selectedJobs.value = [...unifiedJobs.value]
  sankeyJobs.value = [...unifiedJobs.value]
  nestedJobs.value = [...unifiedJobs.value]
}

// 一键生成所有视图
const loadAllViews = async () => {
  syncToAllViews()
  
  // 如果有职位输入，自动切换桑基图为对比模式
  if (hasUnifiedJobs.value) {
    sankeyMode.value = 'compare'
  }
  
  // 并行加载所有视图
  const promises = []
  
  if (hasValidJobs.value) {
    promises.push(loadData())
  }
  
  // 桑基图：有职位时用对比模式，否则用整体模式
  if (hasValidSankeyJobs.value) {
    promises.push(loadSankeyData())
  }
  
  if (hasValidNestedJobs.value) {
    promises.push(loadNestedData(null))
  }
  
  try {
    await Promise.all(promises)
    console.log('所有视图加载完成')
  } catch (err) {
    console.error('加载视图失败', err)
  }
}

// 清空所有职位
const clearAllJobs = () => {
  unifiedJobs.value = ['', '', '']
  selectedJobs.value = ['', '', '']
  sankeyJobs.value = ['', '', '']
  nestedJobs.value = ['', '', '']
  chartData.value = null
  sankeyData.value = null
  nestedData.value = null
}

// ========== 视图一：平行坐标图 ==========
// 职位选择
const selectedJobs = ref(['', '', ''])

// 数据获取
const { data: chartData, loading, error, execute } = useFetchData(() => {
  const validJobs = selectedJobs.value.filter(job => job && job.trim())
  if (validJobs.length === 0) {
    throw new Error('请至少选择一个职位')
  }
  return getParallelCoordinatesData(validJobs)
})

// 检查是否有有效的职位选择
const hasValidJobs = computed(() => {
  return selectedJobs.value.some(job => job && job.trim())
})

// 处理职位输入
const handleJobInput = (index) => {
  // 可以在这里添加实时验证或其他逻辑
}

// 加载数据
const loadData = async () => {
  const validJobs = selectedJobs.value.filter(job => job && job.trim())
  if (validJobs.length === 0) {
    alert('请至少选择一个职位')
    return
  }
  if (validJobs.length > 3) {
    alert('最多只能选择3个职位')
    return
  }
  
  try {
    console.log('Q2Tab: 开始加载数据，职位:', validJobs)
    const response = await execute()
    console.log('Q2Tab: 数据加载成功', {
      response,
      chartData: chartData.value,
      data: chartData.value?.data
    })
  } catch (err) {
    console.error('Q2Tab: 加载数据失败', err)
    alert('加载数据失败: ' + (err.message || '未知错误'))
  }
}

// 清除选择
const clearSelection = () => {
  selectedJobs.value = ['', '', '']
  chartData.value = null
}

// ========== 视图二：桑基图 ==========
// 桑基图模式
const sankeyMode = ref('all')
const sankeyJobs = ref(['', '', ''])
const sankeyData = ref(null)
const sankeyLoading = ref(false)
const sankeyError = ref(null)
// 选择的维度（默认全选）
const selectedDimensions = ref(['skill_level', 'industry_spread', 'market_demand'])

// 检查是否有有效的桑基图职位选择
const hasValidSankeyJobs = computed(() => {
  return sankeyJobs.value.some(job => job && job.trim())
})

// 处理模式变化
const handleModeChange = () => {
  sankeyData.value = null
  sankeyError.value = null
}

// 加载桑基图数据
const loadSankeyData = async () => {
  try {
    // 验证维度选择
    if (selectedDimensions.value.length < 2) {
      alert('请至少选择2个维度')
      return
    }
    
    sankeyLoading.value = true
    sankeyError.value = null
    
    let validJobs = []
    if (sankeyMode.value === 'compare') {
      validJobs = sankeyJobs.value.filter(job => job && job.trim())
      if (validJobs.length === 0) {
        alert('对比模式下请至少选择一个职位')
        sankeyLoading.value = false
        return
      }
    }
    
    console.log('Q2Tab: 开始加载桑基图数据', {
      mode: sankeyMode.value,
      jobs: validJobs,
      dimensions: selectedDimensions.value
    })
    
    const response = await getSankeyData(sankeyMode.value, validJobs, selectedDimensions.value)
    sankeyData.value = response
    
    console.log('Q2Tab: 桑基图数据加载成功', response)
  } catch (err) {
    console.error('Q2Tab: 加载桑基图数据失败', err)
    sankeyError.value = err.message || '加载数据失败'
    alert('加载桑基图数据失败: ' + (err.message || '未知错误'))
  } finally {
    sankeyLoading.value = false
  }
}

// 清除桑基图选择
const clearSankeySelection = () => {
  sankeyJobs.value = ['', '', '']
  sankeyData.value = null
  sankeyError.value = null
}

// ========== 视图三：嵌套柱状图 ==========
const nestedJobs = ref(['', '', ''])
const nestedData = ref(null)
const nestedLoading = ref(false)
const nestedError = ref(null)
const selectedDetailJob = ref(null)

// 检查是否有有效的嵌套图职位选择
const hasValidNestedJobs = computed(() => {
  return nestedJobs.value.some(job => job && job.trim())
})

// 加载嵌套柱状图数据
const loadNestedData = async (detailJob = null) => {
  try {
    nestedLoading.value = true
    nestedError.value = null
    
    const validJobs = nestedJobs.value.filter(job => job && job.trim())
    if (validJobs.length === 0) {
      alert('请至少选择一个职位')
      nestedLoading.value = false
      return
    }
    
    // 验证 detailJob 参数
    let validDetailJob = null
    if (detailJob && typeof detailJob === 'string' && detailJob.trim()) {
      validDetailJob = detailJob.trim()
    }
    
    console.log('Q2Tab: 开始加载嵌套柱状图数据', {
      jobs: validJobs,
      detailJob: validDetailJob
    })
    
    const response = await getNestedBarData(validJobs, validDetailJob)
    nestedData.value = response
    selectedDetailJob.value = validDetailJob
    
    console.log('Q2Tab: 嵌套柱状图数据加载成功', response)
  } catch (err) {
    console.error('Q2Tab: 加载嵌套柱状图数据失败', err)
    nestedError.value = err.message || '加载数据失败'
    alert('加载嵌套柱状图数据失败: ' + (err.message || '未知错误'))
  } finally {
    nestedLoading.value = false
  }
}

// 处理选择详细职位
const handleSelectDetailJob = (jobTitle) => {
  console.log('Q2Tab: 选择详细职位', jobTitle, '类型:', typeof jobTitle)
  if (typeof jobTitle === 'string' && jobTitle.trim()) {
    loadNestedData(jobTitle)
  } else {
    console.error('Q2Tab: 无效的职位名称', jobTitle)
  }
}

// 返回宏观对比
const backToMacro = () => {
  selectedDetailJob.value = null
  loadNestedData(null)
}

// 清除嵌套图选择
const clearNestedSelection = () => {
  nestedJobs.value = ['', '', '']
  nestedData.value = null
  nestedError.value = null
  selectedDetailJob.value = null
}

// 展开视图到标签页模式
const expandView = (view) => {
  layoutMode.value = 'tabs'
  currentView.value = view
}

// 拖拽功能
const draggedJob = ref(null)

// 开始拖拽
const handleDragStart = (event, jobValue) => {
  if (jobValue && jobValue.trim()) {
    draggedJob.value = jobValue.trim()
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('text/plain', jobValue.trim())
    
    // 添加拖拽样式
    event.target.style.opacity = '0.5'
  }
}

// 放置到目标视图
const handleDrop = (event, targetView) => {
  event.preventDefault()
  const jobValue = event.dataTransfer.getData('text/plain')
  
  if (!jobValue || !jobValue.trim()) {
    return
  }
  
  // 根据目标视图添加职位到第一个空位
  let targetJobs = null
  switch (targetView) {
    case 'parallel':
      targetJobs = selectedJobs
      break
    case 'sankey':
      // 如果是整体模式，先切换到对比模式
      if (sankeyMode.value === 'all') {
        sankeyMode.value = 'compare'
      }
      targetJobs = sankeyJobs
      break
    case 'nested':
      targetJobs = nestedJobs
      break
  }
  
  if (targetJobs) {
    // 查找第一个空位
    const emptyIndex = targetJobs.value.findIndex(job => !job || !job.trim())
    if (emptyIndex !== -1) {
      targetJobs.value[emptyIndex] = jobValue.trim()
      console.log(`职位 "${jobValue}" 已复制到 ${targetView} 视图`)
    } else {
      // 如果没有空位，替换最后一个
      targetJobs.value[targetJobs.value.length - 1] = jobValue.trim()
      console.log(`职位 "${jobValue}" 已替换 ${targetView} 视图的最后一个位置`)
    }
  }
  
  draggedJob.value = null
}

</script>

<style scoped>
.q2-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.q2-tab h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

/* 布局切换按钮 */
.layout-toggle {
  display: flex;
  gap: 8px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 8px;
}

.layout-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.layout-btn span {
  font-size: 16px;
}

.layout-btn:hover {
  background: rgba(84, 112, 198, 0.1);
  color: #5470c6;
}

.layout-btn.active {
  background: #5470c6;
  color: white;
  box-shadow: 0 2px 6px rgba(84, 112, 198, 0.3);
}

/* 网格布局包装器 */
.grid-layout-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 20px;
}

/* 统一职位选择器 */
.unified-job-selector {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  color: white;
}

.selector-header {
  margin-bottom: 20px;
}

.selector-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.selector-hint {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
  font-weight: 400;
}

.selector-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.unified-inputs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  font-weight: 600;
  opacity: 0.95;
  letter-spacing: 0.5px;
}

.unified-input {
  padding: 12px 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  transition: all 0.3s;
}

.unified-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.unified-input:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.unified-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.25);
  border-color: white;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
}

.unified-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.unified-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.unified-btn span {
  font-size: 16px;
}

.unified-btn-sync {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.unified-btn-sync:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
}

.unified-btn-load {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.unified-btn-load:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(67, 233, 123, 0.4);
}

.unified-btn-clear {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.unified-btn-clear:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(250, 112, 154, 0.4);
}

.unified-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* 网格布局 */
.grid-layout {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 16px;
}

.grid-item {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(84, 112, 198, 0.1);
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 650px;
}

.grid-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #5470c6, #91cc75, #fac858);
  opacity: 0;
  transition: opacity 0.3s;
}

.grid-item:hover::before {
  opacity: 1;
}

.grid-item:hover {
  box-shadow: 0 8px 32px rgba(84, 112, 198, 0.15);
  transform: translateY(-4px);
  border-color: rgba(84, 112, 198, 0.3);
}

.grid-item-full {
  grid-column: 1 / -1;
}

.grid-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 16px;
  position: relative;
  overflow: hidden;
}

.grid-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-30%, -30%); }
}

.grid-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  letter-spacing: 0.3px;
  z-index: 1;
}

.grid-title::before {
  content: '';
  width: 4px;
  height: 20px;
  background: white;
  border-radius: 2px;
  opacity: 0.8;
}

.expand-btn {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  z-index: 1;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.15) rotate(90deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.grid-content-compact {
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
  overflow: hidden;
}

.grid-content-wide {
  flex: 1;
}

/* 紧凑控制面板 */
.compact-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  align-items: center;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.compact-mode {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 6px 12px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.compact-mode label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #495057;
  cursor: pointer;
  white-space: nowrap;
  font-weight: 500;
  transition: color 0.2s;
}

.compact-mode label:hover {
  color: #667eea;
}

.compact-mode input[type="radio"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #667eea;
}

.compact-inputs {
  display: flex;
  gap: 10px;
  flex: 1;
  min-width: 200px;
}

/* 可拖拽输入框包装器 */
.draggable-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.drag-handle {
  position: absolute;
  left: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 12px;
  cursor: grab;
  user-select: none;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.draggable-input-wrapper:hover .drag-handle {
  opacity: 1;
}

.compact-input {
  flex: 1;
  padding: 8px 12px 8px 24px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  min-width: 80px;
  background: white;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.draggable-input {
  cursor: grab;
}

.draggable-input:active {
  cursor: grabbing;
}

.compact-input:hover {
  border-color: #b8c5e8;
}

.compact-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1), 0 2px 8px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

/* 拖拽时的视觉反馈 */
.grid-item {
  transition: all 0.3s;
}

.grid-item:has(.compact-input:active) {
  opacity: 0.8;
}

.compact-actions {
  display: flex;
  gap: 8px;
}

.compact-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.compact-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.compact-btn:hover::before {
  width: 300px;
  height: 300px;
}

.compact-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.compact-btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.compact-btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.compact-btn-primary:disabled {
  background: linear-gradient(135deg, #ccc 0%, #999 100%);
  cursor: not-allowed;
  opacity: 0.6;
}

.compact-btn-secondary {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #495057;
}

.compact-btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.compact-btn-warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.compact-btn-warning:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
}

.compact-chart {
  flex: 1;
  min-height: 450px;
  overflow: auto;
  border-radius: 12px;
  background: white;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
}

.compact-chart::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.compact-chart::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.compact-chart::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.compact-chart::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #5568d3 0%, #653a8e 100%);
}

/* 视图切换标签 */
.view-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.view-tab {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-size: 15px;
  color: #666;
  transition: all 0.3s;
  font-weight: 500;
}

.view-tab:hover {
  color: #5470c6;
  background: rgba(84, 112, 198, 0.05);
}

.view-tab.active {
  color: #5470c6;
  border-bottom-color: #5470c6;
  font-weight: 600;
}

.view-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 模式选择器 */
.mode-selector {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
}

.mode-group {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
}

.mode-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
}

.mode-group input[type="radio"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

/* 维度选择器 */
.dimension-selector {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.dimension-title {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
}

.dimension-group {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.dimension-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
}

.dimension-group input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.dimension-hint {
  margin-top: 10px;
  font-size: 13px;
  color: #f39c12;
  font-weight: 500;
}

.chart-description {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
}

.chart-description strong {
  color: #5470c6;
  font-weight: 600;
}

.job-selector {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.selector-group label {
  min-width: 60px;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.job-input {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.3s;
}

.job-input:focus {
  outline: none;
  border-color: #5470c6;
  box-shadow: 0 0 0 3px rgba(84, 112, 198, 0.1);
}

.selector-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #5470c6 0%, #4558a3 100%);
  color: white;
  box-shadow: 0 2px 6px rgba(84, 112, 198, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #4558a3 0%, #3a4a8e 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(84, 112, 198, 0.4);
}

.btn-secondary {
  background: #f0f0f0;
  color: #666;
  border: 1px solid #ddd;
}

.btn-secondary:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.chart-section {
  flex: 1;
  min-height: 600px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
</style>

