/**
 * D3颜色比例工具
 */
import * as d3 from 'd3'

/**
 * 创建颜色比例尺
 * @param {Array} domain - 数据范围
 * @param {string} scheme - 颜色方案名称
 * @returns {Function} 颜色比例尺函数
 */
export function createColorScale(domain, scheme = 'viridis') {
  const schemes = {
    viridis: d3.scaleSequential(d3.interpolateViridis),
    plasma: d3.scaleSequential(d3.interpolatePlasma),
    inferno: d3.scaleSequential(d3.interpolateInferno),
    magma: d3.scaleSequential(d3.interpolateMagma),
    rainbow: d3.scaleSequential(d3.interpolateRainbow),
    category10: d3.scaleOrdinal(d3.schemeCategory10),
    category20: d3.scaleOrdinal(d3.schemeCategory20),
    accent: d3.scaleOrdinal(d3.schemeAccent),
    dark2: d3.scaleOrdinal(d3.schemeDark2),
    pastel1: d3.scaleOrdinal(d3.schemePastel1),
    pastel2: d3.scaleOrdinal(d3.schemePastel2),
    set1: d3.scaleOrdinal(d3.schemeSet1),
    set2: d3.scaleOrdinal(d3.schemeSet2),
    set3: d3.scaleOrdinal(d3.schemeSet3)
  }

  const scale = schemes[scheme] || schemes.viridis
  
  if (domain) {
    if (scheme.includes('Sequential')) {
      scale.domain(domain)
    } else {
      scale.domain(domain)
    }
  }

  return scale
}

/**
 * 创建渐变色比例尺（用于数值映射）
 * @param {Array} domain - 数据范围 [min, max]
 * @param {Array} range - 颜色范围
 * @returns {Function} 颜色比例尺函数
 */
export function createGradientScale(domain, range = ['#667eea', '#764ba2']) {
  return d3.scaleLinear()
    .domain(domain)
    .range(range)
    .interpolate(d3.interpolateRgb)
}

/**
 * 获取默认颜色方案
 * @param {number} count - 需要的颜色数量
 * @returns {Array} 颜色数组
 */
export function getDefaultColors(count) {
  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0',
    '#a8edea', '#fed6e3', '#ffecd2', '#fcb69f'
  ]
  
  if (count <= colors.length) {
    return colors.slice(0, count)
  }
  
  // 如果需要的颜色数量超过预设，使用插值生成
  const scale = d3.scaleOrdinal(d3.schemeCategory20)
  return Array.from({ length: count }, (_, i) => scale(i))
}

