<template>
  <div class="force-directed-chart">
    <div v-if="selectedIndustries.length !== 2" class="placeholder">
      <p>请保持选中 2 个行业以生成力引导图</p>
      <p class="hint">节点距离中心越近，表示该维度差异贡献越大</p>
    </div>
    <div v-else ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  selectedIndustries: {
    type: Array,
    default: () => []
  }
})

const chartContainer = ref(null)
let chartInstance = null

const dimensionConfig = [
  { key: 'avg_median_salary', name: '平均薪资', unit: 'K', min: 0, max: 200 },
  { key: 'avg_experience_rank', name: '平均经验', unit: '级', min: 0, max: 10 },
  { key: 'avg_education_rank', name: '平均学历', unit: '级', min: 0, max: 10 },
  { key: 'avg_city_tier_score', name: '平均城市等级', unit: '级', min: 1, max: 4 },
  { key: 'job_count', name: '招聘总数', unit: '个', min: 0, max: 50000, useRatio: true }
]

const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']

const buildDiffPayload = (industryA, industryB) => {
  const result = {
    industryA: industryA.company_type,
    industryB: industryB.company_type,
    dimensions: [],
    totalScore: 0
  }

  dimensionConfig.forEach((config, idx) => {
    const valueA = industryA[config.key] ?? 0
    const valueB = industryB[config.key] ?? 0
    let score = 0
    let ratio = null
    let winner = 'A'
    const rawDiff = Math.abs(valueA - valueB)

    if (config.useRatio) {
      const larger = Math.max(valueA, valueB)
      const smaller = Math.max(1, Math.min(valueA, valueB))
      ratio = larger / (smaller || 1)
      score = ratio >= 10 ? 2 : ((ratio - 1) / 9) * 2
      winner = larger === valueA ? 'A' : 'B'
    } else {
      const span = Math.max(config.max - config.min, 1)
      score = Math.min(2, (rawDiff / span) * 2)
      winner = valueA >= valueB ? 'A' : 'B'
    }

    result.totalScore += score
    result.dimensions.push({
      name: config.name,
      unit: config.unit,
      valueA,
      valueB,
      score,
      ratio,
      winner,
      color: colors[idx % colors.length]
    })
  })

  return result
}

const buildOption = (diffData, width, height) => {
  const nodes = []
  const links = []
  
  // 中心节点：总差异度分数（使用与周围节点完全不同的颜色，如深紫色）
  const centerNode = {
    id: 'center',
    name: `差异总分\n${diffData.totalScore.toFixed(2)}`,
    value: diffData.totalScore,
    category: 0,
    symbolSize: 80,
    itemStyle: {
      color: '#9b59b6', // 深紫色，与周围节点的蓝、绿、黄、红、青色都不同
      borderColor: '#fff',
      borderWidth: 3
    },
    label: {
      show: true,
      fontSize: 14,
      fontWeight: 'bold',
      color: '#fff',
      formatter: `差异总分\n{value|${diffData.totalScore.toFixed(2)}}`,
      rich: {
        value: {
          fontSize: 18,
          fontWeight: 'bold',
          color: '#fff'
        }
      }
    },
    x: width / 2,
    y: height / 2,
    fixed: true // 固定中心节点位置
  }
  nodes.push(centerNode)

  // 计算总权重，用于确定节点距离
  const totalWeight = diffData.dimensions.reduce((sum, d) => sum + (d.score || 0.1), 0)
  
  // 辅助函数：将颜色变浅（同色系）
  const lightenColor = (color, amount = 0.4) => {
    // 简单的颜色变浅逻辑，将RGB值增加
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const newR = Math.min(255, Math.floor(r + (255 - r) * amount))
    const newG = Math.min(255, Math.floor(g + (255 - g) * amount))
    const newB = Math.min(255, Math.floor(b + (255 - b) * amount))
    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`
  }

  // 五个维度节点
  diffData.dimensions.forEach((dim, idx) => {
    const weight = Math.max(dim.score || 0.1, 0.1)
    const weightRatio = weight / totalWeight
    
    // 贡献占比越大，离中心越近
    // 使用反比例：贡献越大，距离越小
    // 减小分布范围，让节点更集中在中心区域，优化初始展示区域大小
    // 使用更小的比例系数，让节点更紧凑地分布在中心区域
    const baseSize = Math.min(width, height)
    const maxRadius = baseSize * 0.2  // 进一步减小最大半径
    const minRadius = baseSize * 0.08 // 进一步减小最小半径
    // 权重越大，距离越小（反比例关系）
    const distance = minRadius + (maxRadius - minRadius) * (1 - weightRatio)
    
    // 均匀分布在圆周上
    const angle = (idx * Math.PI * 2) / diffData.dimensions.length
    const dimX = width / 2 + Math.cos(angle) * distance
    const dimY = height / 2 + Math.sin(angle) * distance
    
    // 节点大小根据分数调整
    const nodeSize = 30 + (weight / 2) * 20
    
    const dimensionNode = {
      id: `dim_${idx}`,
      name: `${dim.name}\n${dim.score.toFixed(2)}`,
      value: dim.score,
      category: 1,
      symbolSize: nodeSize,
      itemStyle: {
        color: dim.color,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 12,
        fontWeight: 'bold',
        color: '#333',
        formatter: `{name|${dim.name}}\n{value|${dim.score.toFixed(2)}}`,
        rich: {
          name: {
            fontSize: 12,
            fontWeight: 'bold',
            color: '#333'
          },
          value: {
            fontSize: 11,
            color: '#666'
          }
        }
      },
      x: dimX,
      y: dimY
    }
    nodes.push(dimensionNode)
    
    // 创建从维度节点到中心节点的连线
    links.push({
      source: `dim_${idx}`,
      target: 'center',
      value: dim.score,
      lineStyle: {
        color: dim.color,
        width: 2 + (dim.score / 2) * 3, // 线宽根据分数调整
        opacity: 0.6,
        curveness: 0.1 // 轻微弯曲，更美观
      },
      label: {
        show: false
      }
    })

    // 为每个维度节点添加两个子节点（行业A和行业B的值）
    // 子节点位置：在维度节点的外圈，沿维度节点到中心的反方向分布
    const subNodeRadius = Math.min(width, height) * 0.01 // 子节点距离维度节点的距离（缩短一半）
    const subNodeSize = 18 // 固定大小
    
    // 计算子节点的角度：沿维度节点到中心的反方向，稍微偏移以避免重叠
    const reverseAngle = angle + Math.PI // 反方向
    const offsetAngle = Math.PI / 3 // 60度偏移
    
    // 行业A的子节点（左侧偏移）
    const subNodeAId = `dim_${idx}_A`
    const subNodeAAngle = reverseAngle - offsetAngle
    const subNodeAX = dimX + Math.cos(subNodeAAngle) * subNodeRadius
    const subNodeAY = dimY + Math.sin(subNodeAAngle) * subNodeRadius
    const lightColorA = lightenColor(dim.color, 0.5)
    
    const subNodeA = {
      id: subNodeAId,
      name: `A\n${dim.valueA.toFixed(1)}`,
      value: dim.valueA,
      category: 2,
      symbolSize: subNodeSize,
      itemStyle: {
        color: lightColorA,
        borderColor: dim.color,
        borderWidth: 1.5
      },
      label: {
        show: true,
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        formatter: `A\n{value|${dim.valueA.toFixed(1)}}`,
        rich: {
          value: {
            fontSize: 9,
            color: '#666'
          }
        }
      },
      x: subNodeAX,
      y: subNodeAY
    }
    nodes.push(subNodeA)
    
    // 行业B的子节点（右侧偏移）
    const subNodeBId = `dim_${idx}_B`
    const subNodeBAngle = reverseAngle + offsetAngle
    const subNodeBX = dimX + Math.cos(subNodeBAngle) * subNodeRadius
    const subNodeBY = dimY + Math.sin(subNodeBAngle) * subNodeRadius
    const lightColorB = lightenColor(dim.color, 0.3)
    
    const subNodeB = {
      id: subNodeBId,
      name: `B\n${dim.valueB.toFixed(1)}`,
      value: dim.valueB,
      category: 2,
      symbolSize: subNodeSize,
      itemStyle: {
        color: lightColorB,
        borderColor: dim.color,
        borderWidth: 1.5
      },
      label: {
        show: true,
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        formatter: `B\n{value|${dim.valueB.toFixed(1)}}`,
        rich: {
          value: {
            fontSize: 9,
            color: '#666'
          }
        }
      },
      x: subNodeBX,
      y: subNodeBY
    }
    nodes.push(subNodeB)
    
    // 创建从子节点到维度节点的连线
    links.push({
      source: subNodeAId,
      target: `dim_${idx}`,
      value: dim.valueA,
      lineStyle: {
        color: lightColorA,
        width: 1.5,
        opacity: 0.4,
        curveness: 0
      },
      label: {
        show: false
      }
    })
    
    links.push({
      source: subNodeBId,
      target: `dim_${idx}`,
      value: dim.valueB,
      lineStyle: {
        color: lightColorB,
        width: 1.5,
        opacity: 0.4,
        curveness: 0
      },
      label: {
        show: false
      }
    })
  })

  // 计算各维度占比，用于 tooltip 显示（使用上面已计算的 totalWeight）
  const dimensionRatios = diffData.dimensions.map(dim => ({
    ...dim,
    ratio: totalWeight > 0 ? ((dim.score || 0.1) / totalWeight * 100).toFixed(2) : '0.00'
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          if (params.data.id === 'center') {
            // 中心节点悬浮时显示各维度差异度占比
            let tooltipContent = `<div style="font-weight: bold; margin-bottom: 8px;">差异总分: ${params.data.value.toFixed(2)}</div>`
            tooltipContent += '<div style="margin-top: 8px; border-top: 1px solid #ddd; padding-top: 8px;">各维度差异度占比：</div>'
            dimensionRatios.forEach((dim, idx) => {
              tooltipContent += `<div style="margin-top: 4px;">
                <span style="display: inline-block; width: 8px; height: 8px; background-color: ${dim.color}; border-radius: 50%; margin-right: 6px;"></span>
                ${dim.name}: ${dim.ratio}%
              </div>`
            })
            return tooltipContent
          } else if (params.data.id && params.data.id.startsWith('dim_')) {
            // 维度节点
            const dimMatch = params.data.id.match(/^dim_(\d+)$/)
            if (dimMatch) {
              const dimIdx = parseInt(dimMatch[1])
              const dim = diffData.dimensions[dimIdx]
              if (dim) {
                const ratio = totalWeight > 0 ? ((dim.score || 0.1) / totalWeight * 100).toFixed(2) : '0.00'
                return `${dim.name}<br/>差异分数: ${dim.score.toFixed(2)}<br/>占比: ${ratio}%<br/>行业A: ${dim.valueA.toFixed(2)}${dim.unit}<br/>行业B: ${dim.valueB.toFixed(2)}${dim.unit}`
              }
            }
            // 子节点（行业A或B）
            const subMatch = params.data.id.match(/^dim_(\d+)_([AB])$/)
            if (subMatch) {
              const dimIdx = parseInt(subMatch[1])
              const industry = subMatch[2]
              const dim = diffData.dimensions[dimIdx]
              if (dim) {
                const value = industry === 'A' ? dim.valueA : dim.valueB
                const industryName = industry === 'A' ? diffData.industryA : diffData.industryB
                return `${dim.name} - 行业${industry}<br/>${industryName}<br/>值: ${value.toFixed(2)}${dim.unit}`
              }
            }
          }
        }
        return ''
      }
    },
    legend: {
      show: false
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        animation: true,
        data: nodes,
        links: links,
        categories: [
          {
            name: '中心节点',
            itemStyle: {
              color: '#9b59b6' // 深紫色，与周围节点颜色不同
            }
          },
          {
            name: '维度节点',
            itemStyle: {
              color: '#5470c6'
            }
          },
          {
            name: '子节点',
            itemStyle: {
              color: '#95a5a6'
            }
          }
        ],
        roam: true,
        label: {
          show: true,
          position: 'inside',
          formatter: '{b}'
        },
        labelLayout: {
          hideOverlap: true
        },
        lineStyle: {
          color: 'source',
          curveness: 0
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          }
        },
        force: {
          // 力引导布局配置，营造漂浮效果
          initLayout: 'none', // 使用我们预设的位置
          repulsion: [100, 200], // 节点之间的斥力范围，减小以让节点更紧凑，确保能一次性展示
          gravity: 0.05, // 增加重力，让节点更靠近中心，确保完整显示
          edgeLength: [60, 100], // 边的理想长度范围，减小以确保紧凑布局
          layoutAnimation: true, // 启用布局动画
          friction: 0.4, // 摩擦系数，稍微增加以稳定布局
          // 限制节点在画布内
          preventOverlap: true,
          // 添加一些随机性，让节点有轻微的抖动效果
          cooling: 0.92 // 冷却系数，稍微降低以加快收敛
        }
      }
    ]
  }
}

const updateChart = () => {
  if (!chartInstance || props.selectedIndustries.length !== 2) return
  const diffData = buildDiffPayload(props.selectedIndustries[0], props.selectedIndustries[1])

  try {
    const width = chartInstance.getWidth()
    const height = chartInstance.getHeight()
    chartInstance.setOption(buildOption(diffData, width, height), true)
    chartInstance.resize()
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('ForceDirectedChart: setOption failed', e)
  }
}

const initChart = async () => {
  await nextTick()
  if (!chartContainer.value) return

  const dom = chartContainer.value

  // 如果容器还没有尺寸，等待几帧
  let retries = 0
  while ((!dom.offsetWidth || !dom.offsetHeight) && retries < 5) {
    await nextTick()
    retries++
  }

  if (!dom.offsetWidth || !dom.offsetHeight) {
    console.warn('ForceDirectedChart: chartContainer has no size, will retry')
    // 延迟重试
    setTimeout(async () => {
      if (chartContainer.value && props.selectedIndustries.length === 2) {
        await initChart()
      }
    }, 200)
    return
  }

  // 如果实例已存在，先销毁
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  chartInstance = echarts.init(dom)

  if (import.meta && import.meta.env && import.meta.env.DEV) {
    // eslint-disable-next-line no-underscore-dangle
    window.__forceDirectedChart = chartInstance
  }

  window.addEventListener('resize', handleResize)
  updateChart()
}

const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
    updateChart()
  }
}

watch(
  () => props.selectedIndustries,
  async (val) => {
    await nextTick()
    if (val.length === 2) {
      // 确保容器存在且可见
      if (!chartContainer.value) {
        await nextTick()
      }
      if (!chartInstance) {
        await initChart()
      } else {
        // 如果图表实例存在但容器可能被隐藏过，需要重新显示并更新
        if (chartContainer.value && (!chartContainer.value.offsetWidth || !chartContainer.value.offsetHeight)) {
          await nextTick()
          // 等待一帧确保 DOM 更新
          setTimeout(() => {
            if (chartInstance) {
              chartInstance.resize()
              updateChart()
            }
          }, 100)
        } else {
          updateChart()
        }
      }
    } else if (chartInstance) {
      // 不清空图表实例，只清空内容，这样再次选择时可以快速恢复
      disposeChart()
      return
    }
  },
  { deep: true }
)

onMounted(async () => {
  if (props.selectedIndustries.length === 2) {
    await initChart()
  }
})

onUnmounted(() => {
  disposeChart()
})
</script>

<style scoped>
.force-directed-chart {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 260px;
}

.placeholder {
  text-align: center;
  color: #777;
  padding: 40px 20px;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: #aaa;
}
</style>

