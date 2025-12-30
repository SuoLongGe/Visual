<template>
  <div class="custom-select-wrapper" :class="{ 'is-open': isOpen, 'has-value': modelValue }" @click.stop>
    <div class="custom-select-input" @click.stop="handleInputClick">
      <input
        v-model="inputValue"
        type="text"
        :placeholder="placeholder"
        class="select-input"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @click.stop
        @keydown.enter.prevent="selectFirstMatch"
        @keydown.escape="closeDropdown"
        @keydown.down.prevent="navigateDown"
        @keydown.up.prevent="navigateUp"
      />
      <span class="select-arrow" :class="{ 'is-open': isOpen }">▼</span>
    </div>
    
    <transition name="dropdown">
      <div v-if="isOpen && filteredOptions.length > 0" class="custom-select-dropdown">
        <div
          v-for="(option, index) in displayedOptions"
          :key="option"
          :class="['dropdown-option', { 'is-hovered': index === hoveredIndex, 'is-selected': option === modelValue }]"
          @mouseenter="hoveredIndex = index"
          @mousedown.prevent
          @click.stop="selectOption(option)"
        >
          {{ option }}
        </div>
        <div v-if="filteredOptions.length >= maxVisible" class="dropdown-footer">
          显示前 {{ maxVisible }} 个结果，共 169308 个
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择或输入'
  },
  maxVisible: {
    type: Number,
    default: 100
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const inputValue = ref(props.modelValue || '')
const hoveredIndex = ref(-1)

// 过滤选项
const filteredOptions = computed(() => {
  if (!inputValue.value.trim()) {
    return props.options
  }
  const searchTerm = inputValue.value.toLowerCase().trim()
  return props.options.filter(option => 
    option.toLowerCase().includes(searchTerm)
  )
})

// 显示的选项（限制数量）
const displayedOptions = computed(() => {
  return filteredOptions.value.slice(0, props.maxVisible)
})

// 监听外部点击 - 使用 mousedown 而不是 click，因为 mousedown 在 blur 之前触发
const handleClickOutside = (event) => {
  const wrapper = event.target.closest('.custom-select-wrapper')
  if (!wrapper && isOpen.value) {
    closeDropdown()
  }
}

onMounted(() => {
  // 使用 mousedown 而不是 click，避免与 blur 事件冲突
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  inputValue.value = newValue || ''
})

// 处理输入
const handleInput = (event) => {
  inputValue.value = event.target.value
  emit('update:modelValue', inputValue.value)
  if (!isOpen.value) {
    isOpen.value = true
  }
  hoveredIndex.value = -1
}

// 处理输入框点击
const handleInputClick = (event) => {
  event.stopPropagation()
  // 如果点击的是输入框本身，聚焦它
  if (event.target.tagName === 'INPUT') {
    event.target.focus()
  }
  // 切换下拉框状态
  if (!isOpen.value) {
    isOpen.value = true
    hoveredIndex.value = -1
  } else {
    closeDropdown()
  }
}

// 处理焦点
const handleFocus = () => {
  if (!isOpen.value) {
    isOpen.value = true
    hoveredIndex.value = -1
  }
}

// 处理失焦
const handleBlur = (event) => {
  // 延迟关闭，以便点击选项时能触发
  // 使用较长的延迟，确保 mousedown 事件先处理
  setTimeout(() => {
    // 检查焦点是否移到了下拉框内
    const activeElement = document.activeElement
    const wrapper = event.currentTarget.closest('.custom-select-wrapper')
    const dropdown = wrapper?.querySelector('.custom-select-dropdown')
    
    // 如果焦点在下拉框内，不关闭
    if (dropdown && dropdown.contains(activeElement)) {
      return
    }
    
    // 如果点击的是下拉框内的元素，不关闭
    if (event.relatedTarget && wrapper && wrapper.contains(event.relatedTarget)) {
      return
    }
    
    closeDropdown()
  }, 150)
}

// 关闭下拉框
const closeDropdown = () => {
  isOpen.value = false
  hoveredIndex.value = -1
}

// 选择选项
const selectOption = (option) => {
  inputValue.value = option
  emit('update:modelValue', option)
  // 延迟关闭，确保点击事件完成
  setTimeout(() => {
    closeDropdown()
  }, 50)
}

// 选择第一个匹配项
const selectFirstMatch = () => {
  if (displayedOptions.value.length > 0) {
    selectOption(displayedOptions.value[0])
  }
}

// 键盘导航
const navigateDown = () => {
  if (!isOpen.value) {
    isOpen.value = true
    return
  }
  if (hoveredIndex.value < displayedOptions.value.length - 1) {
    hoveredIndex.value++
  }
}

const navigateUp = () => {
  if (hoveredIndex.value > 0) {
    hoveredIndex.value--
  }
}
</script>

<style scoped>
.custom-select-wrapper {
  position: relative;
  width: 100%;
}

.custom-select-input {
  position: relative;
  display: flex;
  align-items: center;
}

.select-input {
  width: 100%;
  padding: 10px 36px 10px 12px;
  border: 1px solid #eef3f6;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  color: #2c3e50;
  transition: all 0.3s ease;
  outline: none;
}

.select-input:focus {
  border-color: #5470c6;
  box-shadow: 0 0 0 3px rgba(84, 112, 198, 0.1);
}

.select-input::placeholder {
  color: #999;
}

.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
  font-size: 12px;
  pointer-events: none;
  transition: transform 0.3s ease;
}

.select-arrow.is-open {
  transform: translateY(-50%) rotate(180deg);
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #eef3f6;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 4px;
}

.dropdown-option {
  padding: 10px 12px;
  font-size: 14px;
  color: #2c3e50;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f5f5f5;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.dropdown-option:hover,
.dropdown-option.is-hovered {
  background: rgba(84, 112, 198, 0.08);
  color: #5470c6;
}

.dropdown-option.is-selected {
  background: rgba(84, 112, 198, 0.12);
  color: #5470c6;
  font-weight: 500;
}

.dropdown-footer {
  padding: 8px 12px;
  font-size: 12px;
  color: #999;
  text-align: center;
  background: #fafafa;
  border-top: 1px solid #eef3f6;
  border-radius: 0 0 8px 8px;
}

/* 滚动条样式 */
.custom-select-dropdown::-webkit-scrollbar {
  width: 6px;
}

.custom-select-dropdown::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 4px;
}

.custom-select-dropdown::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.custom-select-dropdown::-webkit-scrollbar-thumb:hover {
  background: #999;
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

</style>

