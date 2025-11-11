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
    // 延迟初始化，确保元素已经渲染
    const initObserver = () => {
      const element = target.value || target
      if (!element || !(element instanceof Element)) {
        // 如果元素还未渲染，延迟重试（最多重试10次）
        let retryCount = 0
        const maxRetries = 10
        const retry = () => {
          retryCount++
          if (retryCount < maxRetries) {
            setTimeout(() => {
              const el = target.value || target
              if (el && el instanceof Element) {
                initObserver()
              } else {
                retry()
              }
            }, 100)
          }
        }
        retry()
        return
      }

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
    }
    
    // 延迟初始化，确保 DOM 已更新
    setTimeout(initObserver, 0)
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

