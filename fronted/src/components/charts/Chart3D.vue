<template>
  <div class="chart-3d">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-if="error" class="result error">
      <pre>{{ error }}</pre>
    </div>
    
    <div v-if="hasData" class="chart-wrapper">
      <div ref="chartContainer" id="3d-chart-container" class="chart-container"></div>

      <div class="gesture-status" v-if="gestureStatus">
        <span class="status-icon">{{ statusIcon }}</span>
        {{ gestureStatus }}
      </div>

      <div
        v-if="cursor.visible"
        class="hand-cursor"
        :class="{
          'pinching': cursor.isPinching,
          'hovering': cursor.hoverTargetIndex !== -1
        }"
        :style="{ transform: `translate3d(${cursor.x}px, ${cursor.y}px, 0)` }"
      >
        <div class="cursor-ring"></div>
        <div v-if="cursor.isClicking" class="click-ripple"></div>
      </div>

      <video
        ref="gestureVideo"
        class="gesture-video"
        autoplay
        playsinline
        muted
      ></video>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick, watch, reactive } from 'vue'
import * as echarts from 'echarts'
import 'echarts-gl'

const props = defineProps({
  data: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  gestureEnabled: { type: Boolean, default: false }
})

const emit = defineEmits(['bar-click'])

// --- DOM & Chart 引用 ---
const chartContainer = ref(null)
const hasData = ref(false)
let chart3D = null
let resizeHandler = null
const experiences = ref([])
const educations = ref([])

// --- 手势与视频状态 ---
const gestureVideo = ref(null)
const gestureStatus = ref('')
const statusIcon = ref('✋')
let handsInstance = null
let gestureStream = null
let animationFrameId = null

// --- 物理平滑层 (核心性能优化) ---
// 目标值：手势控制这里
const targetState = { alpha: 30, beta: 40, distance: 250 }
// 当前值：渲染循环每一帧逼近这里
const currentState = { alpha: 30, beta: 40, distance: 250 }
// 平滑系数：越小越顺滑 (0.15 是黄金值)
const SMOOTHING = 0.15

// 光标 UI 状态 (保留响应式以驱动 CSS 类名)
const cursor = reactive({
  visible: false,
  x: 0,
  y: 0,
  isPinching: false,
  isClicking: false,
  hoverTargetIndex: -1 // 当前瞄准的柱子索引
})

// 防抖与逻辑变量
let lastHighlightedIndex = -1
let lastTip = { x: 0, y: 0 }
let isRotationActive = false
let wasPinching = false // 记录上一帧是否在捏合，用于检测捏合开始
let lastPinchTime = 0 // 上次捏合触发的时间，用于防抖

// ---------------- 数据监听与初始化 ----------------

watch(() => props.data, (newData) => {
  if (newData && newData.experiences) {
    hasData.value = true
    experiences.value = newData.experiences
    educations.value = newData.educations
    nextTick(() => setTimeout(() => render3DChart(newData), 100))
  }
}, { deep: true })

watch(() => props.gestureEnabled, (enabled) => {
  enabled ? initGestureControl() : stopGestureControl()
})

const render3DChart = (data) => {
  const container = chartContainer.value || document.getElementById('3d-chart-container')
  if (!container) return
  if (chart3D) chart3D.dispose()
  chart3D = echarts.init(container)
  
  const data3d = data.data_3d || []
  const scatterData = data3d.map((item, idx) => ({
    value: item,
    itemIndex: idx
  }))

  chart3D.setOption({
    backgroundColor: '#fafafa',
    grid3D: {
      boxWidth: 200, boxDepth: 100, boxHeight: 150,
      viewControl: {
        autoRotate: false,
        distance: currentState.distance,
        alpha: currentState.alpha,
        beta: currentState.beta,
        minDistance: 50,
        maxDistance: 600,
        // 关键：关闭 ECharts 自带动画，完全由外部循环接管
        animation: false
      }
    },
    xAxis3D: { type: 'category', data: experiences.value, name: '工作经验' },
    yAxis3D: { type: 'category', data: educations.value, name: '学历' },
    zAxis3D: { type: 'value', name: '薪资(K)' },
    series: [{
      type: 'bar3D',
      data: scatterData,
      shading: 'realistic',
      // 高亮样式配置
      emphasis: {
        label: { show: true, textStyle: { fontSize: 14, color: '#fff', backgroundColor: 'rgba(0,0,0,0.7)', padding: 4, borderRadius: 4 } },
        itemStyle: { color: '#ff4d4f', opacity: 1 } // 红色高亮
      },
      itemStyle: { color: '#409EFF', opacity: 0.9 }
    }]
  })

  // 启动高频渲染循环
  startRenderLoop()

  // 监听鼠标 hover 事件，用于获取当前 hover 的柱子索引
  chart3D.on('mouseover', (params) => {
    if (params.dataIndex !== undefined && params.seriesIndex === 0) {
      currentHoveredIndex = params.dataIndex
      cursor.hoverTargetIndex = params.dataIndex
      
      // 立即更新高亮状态
      if (params.dataIndex !== lastHighlightedIndex) {
        if (lastHighlightedIndex !== -1) {
          chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
        }
        chart3D.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: params.dataIndex })
        chart3D.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: params.dataIndex })
        lastHighlightedIndex = params.dataIndex
      }
    }
  })

  chart3D.on('mouseout', () => {
    // 鼠标移出时不清除，保持最后一次 hover 的索引
  })

  // 鼠标点击兜底
  chart3D.on('click', (params) => {
    if (params.data && params.dataIndex !== undefined) {
       triggerClick(params.dataIndex, params.data.value)
      }
  })

  resizeHandler = () => chart3D && chart3D.resize()
  window.addEventListener('resize', resizeHandler)
}

// ---------------- 渲染循环 (解决卡顿的核心) ----------------
const startRenderLoop = () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)

  const loop = () => {
    if (!chart3D) return

    // 1. 物理插值 (Lerp)：让当前视角平滑飞向目标视角
    currentState.alpha += (targetState.alpha - currentState.alpha) * SMOOTHING
    currentState.beta += (targetState.beta - currentState.beta) * SMOOTHING
    currentState.distance += (targetState.distance - currentState.distance) * SMOOTHING

    // 2. 只有当数值有明显变化时才调用 setOption，减少 GPU 负担
    if (
      Math.abs(targetState.alpha - currentState.alpha) > 0.01 ||
      Math.abs(targetState.beta - currentState.beta) > 0.01 ||
      Math.abs(targetState.distance - currentState.distance) > 0.1
    ) {
      chart3D.setOption({
        grid3D: {
          viewControl: {
            alpha: currentState.alpha,
            beta: currentState.beta,
            distance: currentState.distance
          }
        }
      })
    }
    animationFrameId = requestAnimationFrame(loop)
  }
  loop()
}

// ---------------- 手势识别逻辑 ----------------

const loadScript = (src) => new Promise((resolve) => {
  if (document.querySelector(`script[src="${src}"]`)) return resolve()
  const script = document.createElement('script'); script.src = src; script.onload = resolve; document.head.appendChild(script);
})

const initGestureControl = async () => {
  if (handsInstance) return
  await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js')

  const videoEl = gestureVideo.value
  gestureStream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480, facingMode: 'user' }
  })
  videoEl.srcObject = gestureStream
  videoEl.play()

  handsInstance = new window.Hands({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}` })
  handsInstance.setOptions({
    maxNumHands: 1,
    modelComplexity: 0, // 0 = Lite模型，速度最快，延迟最低
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  })

  handsInstance.onResults(handleGestures)

  const processFrame = async () => {
    if (handsInstance && videoEl && !videoEl.paused) await handsInstance.send({ image: videoEl })
    if (props.gestureEnabled) requestAnimationFrame(processFrame)
  }
  processFrame()
}

const stopGestureControl = () => {
  if (handsInstance) handsInstance.close()
  if (gestureStream) gestureStream.getTracks().forEach(t => t.stop())
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  handsInstance = null
}

// 辅助距离计算
const getDist = (lm, i, j) => Math.hypot(lm[i].x - lm[j].x, lm[i].y - lm[j].y)

const handleGestures = (results) => {
  // 如果手移开了
  if (!results.multiHandLandmarks?.length) {
    cursor.visible = false
    isRotationActive = false
    clearHighlight() // 取消高亮
    return
  }

  const lm = results.multiHandLandmarks[0]
  const palmSize = getDist(lm, 0, 9) // 归一化基准

  // --- 1. 更新光标位置 (带平滑) ---
  const rect = chartContainer.value.getBoundingClientRect()
  const rawX = (1 - lm[8].x) * rect.width // 镜像翻转
  const rawY = lm[8].y * rect.height
  cursor.x += (rawX - cursor.x) * 0.5
  cursor.y += (rawY - cursor.y) * 0.5
  cursor.visible = true

  // --- 2. 关键：每一帧都全局检测悬浮目标 (不管是否捏合) ---
  detectHoverTarget()

  // --- 3. 手势判定 ---
  const pinchDist = getDist(lm, 4, 8)
  const dIndex = getDist(lm, 8, 0)
  const dMiddle = getDist(lm, 12, 0)
  const avgSpread = (dIndex + dMiddle + getDist(lm,16,0) + getDist(lm,20,0)) / 4

  const isPinching = pinchDist < palmSize * 0.15
  // 指向：食指伸直，中指弯曲
  const isPointing = !isPinching && (dIndex > palmSize * 1.0) && (dMiddle < dIndex * 0.8)
  const isAllOpen = avgSpread > palmSize * 1.3
  const isFist = avgSpread < palmSize * 0.85

  // --- 4. 逻辑分发 (捏合优先级最高) ---
  if (isPinching) {
    statusIcon.value = '👌'
    gestureStatus.value = '已选中 (捏合)'
    cursor.isPinching = true
    isRotationActive = false

    // 关键修复：只在捏合状态从 false 变为 true 时触发一次，并添加防抖（至少间隔 500ms）
    const now = Date.now()
    if (!wasPinching && (now - lastPinchTime > 500)) {
      // 确保在捏合时也检测一次目标（因为捏合时手可能稍微移动）
      detectHoverTarget()
      executePinchSelection()
      lastPinchTime = now
    }
    wasPinching = true

  } else {
    cursor.isPinching = false
    wasPinching = false

    if (isPointing) {
      statusIcon.value = '☝️'
      gestureStatus.value = '旋转模式'

      if (!isRotationActive) {
        lastTip = { x: lm[8].x, y: lm[8].y }
        isRotationActive = true
      } else {
        const dx = lm[8].x - lastTip.x
        const dy = lm[8].y - lastTip.y
        // 旋转灵敏度
        const ROTATE_SPEED = 200
        targetState.beta  += dx * ROTATE_SPEED
        targetState.alpha += dy * ROTATE_SPEED
        targetState.alpha = Math.max(0, Math.min(90, targetState.alpha)) // 限制俯仰角
        lastTip = { x: lm[8].x, y: lm[8].y }
      }
    } else if (isAllOpen) {
      statusIcon.value = '🖐'
      gestureStatus.value = '放大 (靠近)'
      isRotationActive = false
      targetState.distance = Math.max(50, targetState.distance - 4)
    } else if (isFist) {
      statusIcon.value = '✊'
      gestureStatus.value = '缩小 (远离)'
      isRotationActive = false
      targetState.distance = Math.min(600, targetState.distance + 4)
    } else {
      statusIcon.value = '⏳'
      gestureStatus.value = '待机'
      isRotationActive = false
    }
  }
}

// 存储当前 hover 的索引（通过事件监听获取）
let currentHoveredIndex = -1

// --- 悬浮检测 (使用模拟鼠标事件) ---
const detectHoverTarget = () => {
  if (!chart3D || !chartContainer.value) return

  const x = cursor.x
  const y = cursor.y

  // 方法1：使用 ECharts 的 zrender 实例直接触发 hover 检测
  const zr = chart3D.getZr()
  if (zr) {
    // 使用 zrender 的 findHover 方法
    const hoverResult = zr.handler.findHover(x, y)
    
    if (hoverResult && hoverResult.target) {
      // 尝试从图形元素中提取数据索引
      let foundIndex = -1
      
      // 方法1：直接从 target 获取
      if (hoverResult.target.dataIndex !== undefined) {
        foundIndex = hoverResult.target.dataIndex
      }
      // 方法2：从 __ecComponentInfo 获取
      else if (hoverResult.target.__ecComponentInfo) {
        foundIndex = hoverResult.target.__ecComponentInfo.dataIndex
      }
      // 方法3：从父元素获取
      else if (hoverResult.target.parent && hoverResult.target.parent.dataIndex !== undefined) {
        foundIndex = hoverResult.target.parent.dataIndex
      }
      
      if (foundIndex !== -1 && foundIndex !== lastHighlightedIndex) {
        cursor.hoverTargetIndex = foundIndex
        currentHoveredIndex = foundIndex
        
        // 更新高亮状态
        if (lastHighlightedIndex !== -1) {
          chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
          chart3D.dispatchAction({ type: 'hideTip' })
        }

        chart3D.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: foundIndex })
        chart3D.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: foundIndex })

        lastHighlightedIndex = foundIndex
        return // 成功找到，不需要执行备用方法
      }
    }
  }
  
  // 方法2：如果 zrender 方法不工作，使用模拟鼠标事件
  const canvas = chartContainer.value.querySelector('canvas')
  if (canvas) {
    const rect = chartContainer.value.getBoundingClientRect()
    
    // 创建鼠标移动事件
    const mouseMoveEvent = new MouseEvent('mousemove', {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: rect.left + x,
      clientY: rect.top + y,
      button: 0
    })
    
    canvas.dispatchEvent(mouseMoveEvent)
    
    // 如果事件成功触发了 hover，使用 currentHoveredIndex
    if (currentHoveredIndex !== -1 && currentHoveredIndex !== lastHighlightedIndex) {
      cursor.hoverTargetIndex = currentHoveredIndex
      
      if (lastHighlightedIndex !== -1) {
        chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
        chart3D.dispatchAction({ type: 'hideTip' })
      }

      chart3D.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: currentHoveredIndex })
      chart3D.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: currentHoveredIndex })

      lastHighlightedIndex = currentHoveredIndex
      return
        }
      }

  // 方法2：如果方法1不工作，使用数据坐标匹配（备用方案）
  // 这个方法通过将屏幕坐标转换为数据坐标，然后匹配最近的数据点
  const series = chart3D.getOption().series[0]
  if (series && series.data) {
    const data = series.data
    let nearestIndex = -1
    let minDist = Infinity

    try {
      // 尝试使用 convertFromPixel 将屏幕坐标转换为数据坐标
      // 对于 3D 图表，我们需要指定正确的坐标系
      const dataCoord = chart3D.convertFromPixel({ seriesIndex: 0, coordSys: 'grid3D' }, [x, y])
      
      if (dataCoord && Array.isArray(dataCoord) && dataCoord.length >= 2) {
        const targetExpIdx = Math.round(dataCoord[0])
        const targetEduIdx = Math.round(dataCoord[1])

        // 在数据中找到最接近的点
        for (let i = 0; i < data.length; i++) {
          const val = data[i].value
          if (!val || !Array.isArray(val) || val.length < 3) continue

          const itemExpIdx = Math.round(val[0])
          const itemEduIdx = Math.round(val[1])
          
          // 计算数据空间的距离（只比较 x 和 y 维度，忽略 z）
          const dx = targetExpIdx - itemExpIdx
          const dy = targetEduIdx - itemEduIdx
          const dist = Math.sqrt(dx * dx + dy * dy)
          
          // 如果距离很近（在同一个格子内），就认为是这个点
          if (dist < 0.3 && dist < minDist) {
            minDist = dist
            nearestIndex = i
          }
        }
      }
    } catch (e) {
      // 如果 convertFromPixel 失败，尝试使用更简单的方法
      // 直接遍历所有数据点，使用屏幕坐标估算距离
      const MAGNET_RADIUS = cursor.isPinching ? 120 : 80
      
      for (let i = 0; i < data.length; i++) {
        const val = data[i].value
        if (!val || !Array.isArray(val) || val.length < 3) continue

        try {
          // 尝试使用 convertToPixel（虽然之前失败了，但可能在某些情况下可以工作）
          const pos = chart3D.convertToPixel({ seriesIndex: 0, coordSys: 'grid3D' }, val)
          if (pos && Array.isArray(pos) && pos.length >= 2) {
            const dx = pos[0] - x
            const dy = pos[1] - y
            const dist = Math.sqrt(dx * dx + dy * dy)
            if (dist < MAGNET_RADIUS && dist < minDist) {
              minDist = dist
              nearestIndex = i
            }
          }
        } catch (e2) {
          // 忽略错误，继续下一个点
      }
    }
    }

    // 如果找到了目标，更新状态
    if (nearestIndex !== -1) {
      cursor.hoverTargetIndex = nearestIndex
      currentHoveredIndex = nearestIndex

      // Diff 优化：仅在目标改变时调用 dispatchAction
      if (nearestIndex !== lastHighlightedIndex) {
        if (lastHighlightedIndex !== -1) {
          chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
          chart3D.dispatchAction({ type: 'hideTip' })
        }

        chart3D.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: nearestIndex })
        chart3D.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: nearestIndex })

        lastHighlightedIndex = nearestIndex
      }
    } else {
      // 如果没有找到目标，清除高亮
      if (lastHighlightedIndex !== -1) {
        chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
        chart3D.dispatchAction({ type: 'hideTip' })
        lastHighlightedIndex = -1
        cursor.hoverTargetIndex = -1
      }
    }
  }
}

const clearHighlight = () => {
  if (lastHighlightedIndex !== -1 && chart3D) {
    chart3D.dispatchAction({ type: 'downplay', seriesIndex: 0, dataIndex: lastHighlightedIndex })
    chart3D.dispatchAction({ type: 'hideTip' })
    lastHighlightedIndex = -1
    cursor.hoverTargetIndex = -1
  }
}

// 执行点击 (捏合触发)
const executePinchSelection = () => {
  if (!chart3D) {
    console.warn('Chart3D not initialized')
    return
  }

  // 容错：优先使用当前瞄准的，如果没有，使用上一次高亮的(防抖)
  let targetIndex = cursor.hoverTargetIndex !== -1 ? cursor.hoverTargetIndex : lastHighlightedIndex

  // 如果还是没有目标，尝试重新检测一次
  if (targetIndex === -1) {
    detectHoverTarget()
    targetIndex = cursor.hoverTargetIndex !== -1 ? cursor.hoverTargetIndex : lastHighlightedIndex
  }

  if (targetIndex !== -1) {
    const series = chart3D.getOption().series[0]
    if (!series || !series.data) {
      console.warn('Series data not found')
      return
    }

    const item = series.data[targetIndex]

    if (item && item.value && Array.isArray(item.value) && item.value.length >= 3) {
      // 触发视觉波纹
      cursor.isClicking = true
      setTimeout(() => cursor.isClicking = false, 300)

      // 强制高亮反馈
      chart3D.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: targetIndex })
      chart3D.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: targetIndex })

      // 触发点击事件
      triggerClick(targetIndex, item.value)
      
      console.log('Pinch selection triggered:', {
        index: targetIndex,
        value: item.value,
        experience: experiences.value[item.value[0]],
        education: educations.value[item.value[1]],
        salary: item.value[2]
      })
    } else {
      console.warn('Invalid item data at index', targetIndex, item)
    }
  } else {
    console.warn('No target found for pinch selection')
    gestureStatus.value = '未找到目标 (捏合)'
  }
}

const triggerClick = (index, value) => {
  emit('bar-click', {
    experience: experiences.value[value[0]],
    education: educations.value[value[1]],
    salary: value[2]
  })
}

onUnmounted(() => {
  stopGestureControl()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  if (chart3D) chart3D.dispose()
})
</script>

<style scoped>
.chart-3d { position: relative; width: 100%; height: 100%; }
.chart-wrapper { position: relative; width: 100%; overflow: hidden; }

/* 容器样式 */
.chart-container {
  width: 100%; height: 650px;
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.loading, .result.error { text-align: center; padding: 60px 20px; }
.spinner {
  border: 4px solid #eee; border-top: 4px solid #5470c6;
  border-radius: 50%; width: 50px; height: 50px;
  animation: spin 0.8s linear infinite; margin: 0 auto 20px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* === 手势交互 UI === */
.gesture-status {
  position: absolute; bottom: 20px; left: 20px;
  background: rgba(0,0,0,0.7); color: #fff;
  padding: 8px 16px; border-radius: 30px;
  display: flex; align-items: center; gap: 10px;
  font-size: 14px; pointer-events: none; user-select: none;
  backdrop-filter: blur(4px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
.status-icon { font-size: 18px; }

/* 虚拟光标容器 */
.hand-cursor {
  position: absolute; top: 0; left: 0;
  width: 0; height: 0; /* 自身不占位，靠 transform 定位 */
  pointer-events: none; z-index: 9999;
}

/* 光标圆环 */
.cursor-ring {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 24px; height: 24px;
  border: 2px solid rgba(64, 158, 255, 0.8);
  border-radius: 50%;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.4);
  background: rgba(64, 158, 255, 0.1);
}

/* 状态1：悬浮瞄准 (变大变橙) */
.hand-cursor.hovering .cursor-ring {
  width: 50px; height: 50px;
  border-color: #E6A23C;
  background: rgba(230, 162, 60, 0.15);
  border-width: 3px;
  box-shadow: 0 0 15px rgba(230, 162, 60, 0.6);
}

/* 状态2：捏合选中 (变红实心) */
.hand-cursor.pinching .cursor-ring {
  width: 16px; height: 16px;
  background: #ff4d4f;
  border-color: #ff4d4f;
  border-width: 0;
  box-shadow: 0 0 20px rgba(255, 77, 79, 0.9);
}

/* 点击波纹特效 */
.click-ripple {
  position: absolute; top: 50%; left: 50%;
  width: 100%; height: 100%;
  border-radius: 50%;
  border: 2px solid #ff4d4f;
  transform: translate(-50%, -50%);
  animation: ripple 0.6s ease-out forwards;
}

@keyframes ripple {
  0% { width: 10px; height: 10px; opacity: 1; border-width: 4px; }
  100% { width: 150px; height: 150px; opacity: 0; border-width: 0px; }
}

.gesture-video { position: absolute; opacity: 0; width: 1px; height: 1px; }
</style>