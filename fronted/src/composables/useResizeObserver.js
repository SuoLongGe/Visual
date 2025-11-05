/**
 * 自适应大小监听组合式函数
 */
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 监听元素大小变化
 * @param {HTMLElement|Ref} target - 目标元素
 * @returns {Object} 包含width和height的响应式对象
 */
export function useResizeObserver(target) {
  const width = ref(0)
  const height = ref(0)
  let resizeObserver = null

  const updateSize = () => {
    const element = target.value || target
    if (element) {
      width.value = element.clientWidth
      height.value = element.clientHeight
    }
  }

  onMounted(() => {
    const element = target.value || target
    if (!element) return

    // 初始设置
    updateSize()

    // 使用ResizeObserver监听大小变化
    if (window.ResizeObserver) {
      resizeObserver = new ResizeObserver(() => {
        updateSize()
      })
      resizeObserver.observe(element)
    } else {
      // 降级方案：使用window resize事件
      window.addEventListener('resize', updateSize)
    }
  })

  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
    } else {
      window.removeEventListener('resize', updateSize)
    }
  })

  return {
    width,
    height
  }
}

