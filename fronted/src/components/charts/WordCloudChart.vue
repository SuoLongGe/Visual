<template>
  <div class="wordcloud-container">
    <canvas ref="canvasRef" :width="width" :height="height"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  multiData: {
    type: Object,
    default: () => ({})
  },
  width: {
    type: Number,
    default: 1920
  },
  height: {
    type: Number,
    default: 1080
  }
})

const canvasRef = ref(null)

// 不同维度的颜色配置
const dimensionColors = {
  jobs: ['#d97757', '#ff8c69', '#ff6b4a', '#ff4d2e'],
  education: ['#4a90e2', '#5ba3f5', '#6cb6ff', '#7dc9ff'],
  experience: ['#50c878', '#5fd988', '#6eea98', '#7dfba8'],
  salary: ['#ffa500', '#ffb347', '#ffc166', '#ffcf85'],
  city: ['#9b59b6', '#8e44ad', '#7d3c98', '#6c3483'],
  company_type: ['#e74c3c', '#c0392b', '#a93226', '#922b21']
}

// 全屏自由布局算法（混合所有维度）
const layoutWordsFullscreen = (allWords, canvasWidth, canvasHeight) => {
  const placed = []
  const padding = 3
  
  // 创建临时 canvas 用于测量文字
  const measureCanvas = document.createElement('canvas')
  const measureCtx = measureCanvas.getContext('2d')
  const fontFamily = 'Arial, sans-serif'
  
  // 创建网格用于快速碰撞检测
  const gridSize = 50
  const grid = new Map()
  
  const getGridKey = (gx, gy) => `${gx},${gy}`
  const getGridCoords = (px, py) => ({
    gx: Math.floor(px / gridSize),
    gy: Math.floor(py / gridSize)
  })
  
  // 打乱顺序，让不同维度的词混合
  const shuffledWords = [...allWords].sort(() => Math.random() - 0.5)
  
  shuffledWords.forEach((word) => {
    const fontSize = Math.max(10, Math.min(word.value || 30, 60))
    measureCtx.font = `bold ${fontSize}px ${fontFamily}`
    const textWidth = measureCtx.measureText(word.name).width
    const textHeight = fontSize
    
    let isPlaced = false
    let attempts = 0
    const maxAttempts = 1000
    
    // 策略1: 随机位置（全屏范围）
    while (!isPlaced && attempts < maxAttempts * 0.7) {
      const wordX = padding + Math.random() * (canvasWidth - textWidth - padding * 2)
      const wordY = padding + textHeight + Math.random() * (canvasHeight - textHeight - padding * 2)
      
      // 快速网格碰撞检测
      const gridCoords = getGridCoords(wordX, wordY)
      let collision = false
      
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          const key = getGridKey(gridCoords.gx + dx, gridCoords.gy + dy)
          const gridWords = grid.get(key) || []
          for (const placedWord of gridWords) {
            const dx2 = wordX - placedWord.x
            const dy2 = wordY - placedWord.y
            const distance = Math.sqrt(dx2 * dx2 + dy2 * dy2)
            const minDistance = Math.max(textWidth, placedWord.width) / 2 + padding
            if (distance < minDistance) {
              collision = true
              break
            }
          }
          if (collision) break
        }
        if (collision) break
      }
      
      if (!collision) {
        const wordObj = {
          ...word,
          x: wordX,
          y: wordY,
          width: textWidth,
          height: textHeight,
          fontSize
        }
        placed.push(wordObj)
        
        // 添加到网格
        const gridCoords = getGridCoords(wordX, wordY)
        for (let dx = -1; dx <= 1; dx++) {
          for (let dy = -1; dy <= 1; dy++) {
            const key = getGridKey(gridCoords.gx + dx, gridCoords.gy + dy)
            if (!grid.has(key)) grid.set(key, [])
            grid.get(key).push(wordObj)
          }
        }
        
        isPlaced = true
      }
      
      attempts++
    }
    
    // 策略2: 螺旋布局（如果随机失败）
    if (!isPlaced) {
      const centerX = canvasWidth / 2
      const centerY = canvasHeight / 2
      let angle = Math.random() * Math.PI * 2
      let radius = 0
      
      while (!isPlaced && attempts < maxAttempts) {
        radius += 1.0
        angle += 0.15
        
        const wordX = centerX + Math.cos(angle) * radius - textWidth / 2
        const wordY = centerY + Math.sin(angle) * radius + textHeight / 2
        
        // 边界检查
        if (wordX < padding || wordX + textWidth > canvasWidth - padding ||
            wordY - textHeight < padding || wordY > canvasHeight - padding) {
          attempts++
          continue
        }
        
        // 碰撞检测
        let collision = false
        for (const placedWord of placed) {
          const dx = wordX - placedWord.x
          const dy = wordY - placedWord.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          const minDistance = Math.max(textWidth, placedWord.width) / 2 + padding
          if (distance < minDistance) {
            collision = true
            break
          }
        }
        
        if (!collision) {
          const wordObj = {
            ...word,
            x: wordX,
            y: wordY,
            width: textWidth,
            height: textHeight,
            fontSize
          }
          placed.push(wordObj)
          isPlaced = true
        }
        
        attempts++
      }
    }
  })
  
  return placed
}

const drawWordCloud = () => {
  if (!canvasRef.value || !props.multiData || Object.keys(props.multiData).length === 0) {
    return
  }
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, props.width, props.height)
  
  // 设置全局透明度
  ctx.globalAlpha = 0.4
  
  // 合并所有维度的词，添加维度标识
  const allWords = []
  
  Object.keys(props.multiData).forEach((dimension) => {
    const words = props.multiData[dimension] || []
    if (words.length === 0) {
      console.warn(`维度 ${dimension} 没有数据`)
      return
    }
    
    console.log(`维度 ${dimension} 有 ${words.length} 个词`)
    
    // 准备数据
    let limitedWords
    if (dimension === 'jobs') {
      limitedWords = words.slice(0, 37).map((item) => ({
        name: item.name,
        value: item.value || 30,
        dimension: dimension
      }))
    } else if (dimension === 'salary') {
      limitedWords = words.slice(0, 20).map((item) => ({
        name: item.name,
        value: item.value || 30,
        dimension: dimension
      }))
    } else if (dimension === 'city') {
      limitedWords = words.slice(0, 80).map((item) => ({
        name: item.name,
        value: item.value || 30,
        dimension: dimension
      }))
    } else if (dimension === 'company_type') {
      limitedWords = words.slice(0, 60).map((item) => ({
        name: item.name,
        value: item.value || 30,
        dimension: dimension
      }))
    } else {
      limitedWords = words.slice(0, 80).map((item) => ({
        name: item.name,
        value: item.value || 30,
        dimension: dimension
      }))
    }
    
    allWords.push(...limitedWords)
  })
  
  // 按大小排序
  allWords.sort((a, b) => b.value - a.value)
  
  console.log(`总共准备显示 ${allWords.length} 个词`)
  
  // 全屏布局所有词
  const placedWords = layoutWordsFullscreen(allWords, props.width, props.height)
  
  console.log(`成功放置 ${placedWords.length} 个词`)
  
  // 绘制文字（根据维度使用不同颜色）
  placedWords.forEach((word) => {
    const colors = dimensionColors[word.dimension] || dimensionColors.jobs
    
    // 根据字体大小选择颜色
    const maxSize = Math.max(...placedWords.map(w => w.fontSize))
    const minSize = Math.min(...placedWords.map(w => w.fontSize))
    const sizeRatio = (word.fontSize - minSize) / (maxSize - minSize || 1)
    const colorIndex = Math.min(
      Math.floor(sizeRatio * (colors.length - 1)),
      colors.length - 1
    )
    const color = colors[colorIndex] || colors[0]
    
    ctx.save()
    
    // 设置字体和样式
    ctx.font = `bold ${word.fontSize}px Arial, sans-serif`
    
    // 添加阴影效果
    ctx.shadowColor = 'rgba(0, 0, 0, 0.4)'
    ctx.shadowBlur = 6
    ctx.shadowOffsetX = 2
    ctx.shadowOffsetY = 2
    
    // 使用纯色
    ctx.fillStyle = color
    
    // 绘制文字
    ctx.fillText(word.name, word.x, word.y)
    
    ctx.restore()
  })
  
  // 恢复透明度
  ctx.globalAlpha = 1.0
}

watch(() => props.multiData, () => {
  nextTick(() => {
    drawWordCloud()
  })
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    drawWordCloud()
  })
})
</script>

<style scoped>
.wordcloud-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
