<template>
  <view 
    class="pet-canvas-wrapper" 
    :class="{ 'is-dragging': isDragging }"
    :style="wrapperStyle"
    @click="handleTap"
  >
    <view 
      class="pet-touch-area"
      @touchstart.stop.prevent="onTouchStart"
      @touchmove.stop.prevent="onTouchMove"
      @touchend.stop.prevent="onTouchEnd"
      @longpress.stop.prevent="handleLongPress"
    >
      <image 
        v-if="displayImage" 
        :src="displayImage" 
        class="pet-image"
        mode="aspectFit"
      />
      <canvas
        v-show="!displayImage"
        canvas-id="petCanvas"
        id="petCanvas"
        class="pet-canvas"
        :style="{ width: canvasSize + 'rpx', height: canvasSize + 'rpx' }"
      ></canvas>
    </view>

    <view class="level-badge" v-if="petData">
      <text class="level-text">Lv.{{ petData.level }}</text>
    </view>

    <view class="exp-bar" v-if="petData">
      <view class="exp-fill" :style="{ width: expPercent + '%' }"></view>
    </view>

    <view class="feed-btn" @click.stop="handleFeed" v-if="showFeedBtn && !isDragging">
      <text class="feed-icon">🍖</text>
      <text class="feed-count" v-if="petData && petData.feed_points > 0">{{ petData.feed_points }}</text>
    </view>

    <view class="food-anim" v-if="showFoodAnim" :class="foodAnimClass">
      <text class="food-emoji">{{ currentFoodEmoji }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'

const props = defineProps({
  petData: {
    type: Object,
    default: null
  },
  styleConfig: {
    type: Object,
    default: null
  },
  position: {
    type: Object,
    default: () => ({ x: 20, y: 120 })
  },
  customImage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['feed', 'tap', 'positionChange', 'toggleHide'])

const canvasSize = ref(160)
const ctx = ref(null)
const showFeedBtn = ref(true)
const showFoodAnim = ref(false)
const currentFoodEmoji = ref('🍓')
const foodAnimClass = ref('')

// 拖拽相关
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const currentX = ref(props.position.x)
const currentY = ref(props.position.y)

// 经验百分比
const expPercent = computed(() => {
  if (!props.petData) return 0
  const level = props.petData.level || 1
  const exp = props.petData.exp || 0
  const needExp = 20 + (level - 1) * 10
  return Math.min(100, (exp / needExp) * 100)
})

const isSvgString = (str) => {
  return typeof str === 'string' && str.trim().startsWith('<svg');
}

// 修复：处理自定义图像，安全转码 SVG / Base64
const displayImage = computed(() => {
  const custom = props.customImage;
  if (!custom || custom.length === 0) {
    return '';
  }
  
  // 如果已经是完整的 data URI，直接返回
  if (custom.startsWith('data:')) {
    return custom;
  }
  
  // 如果后端返回的是原生的 <svg> 标签代码，必须进行 URI 编码才能作为 src 使用
  if (isSvgString(custom)) {
    // 处理可能存在的换行和特殊字符
    const cleanSvg = custom.replace(/\n/g, '').replace(/\r/g, '');
    return `data:image/svg+xml;utf8,${encodeURIComponent(cleanSvg)}`;
  }

  if (/^[A-Za-z0-9+/=]{20,}$/.test(custom)) {
    // 尝试判断图片类型（默认 PNG）
    return `data:image/png;base64,${custom}`;
  }
  
  // 否则当作普通的 URL 返回
  return custom;
})

// 包装器样式
const wrapperStyle = computed(() => ({
  left: currentX.value + 'rpx',
  top: currentY.value + 'rpx'
}))

const foodEmojis = ['🍓', '🍪', '🍎', '🥕', '🍑', '🍇', '🧀', '🍔', '🍗', '🥩']

// 初始化画布
const initCanvas = () => {
  ctx.value = uni.createCanvasContext('petCanvas')
  drawPet()
}

// 统一封装一些简单的绘制方法，适配 uni 的 CanvasContext API
const clear = () => {
  if (!ctx.value) return
  ctx.value.clearRect(0, 0, 300, 300)
}

const setFill = (color) => {
  ctx.value.setFillStyle(color)
}

const setStroke = (color, width = 1) => {
  ctx.value.setStrokeStyle(color)
  ctx.value.setLineWidth(width)
}

// 画圆
const fillCircle = (x, y, r, color) => {
  setFill(color)
  ctx.value.beginPath()
  ctx.value.arc(x, y, r, 0, Math.PI * 2)
  ctx.value.fill()
}

// 画椭圆（简单缩放模拟）
const fillEllipse = (x, y, rx, ry, color) => {
  ctx.value.save()
  ctx.value.translate(x, y)
  ctx.value.scale(1, ry / rx)
  fillCircle(0, 0, rx, color)
  ctx.value.restore()
}

// 主绘制
const drawPet = () => {
  if (!ctx.value) return

  clear()

  const style = props.styleConfig || {}
  const level = props.petData?.level || 1

  const colors = {
    body: style.body_color || '#FFB6C1',
    eye: style.eye_color || '#2C3E50',
    accent: style.accent_color || '#FF69B4'
  }

  const size = 50 + level * 2
  const centerX = 80
  const centerY = 80

  const species = style.species_key || 'cat'

  if (species === 'slime') {
    drawSlime(centerX, centerY, colors, level, size)
  } else if (species === 'bot') {
    drawBot(centerX, centerY, colors, level, size)
  } else {
    drawCat(centerX, centerY, colors, level, size)
  }

  ctx.value.draw()
}

const drawCat = (x, y, colors, level, size) => {
  // 身体
  fillEllipse(x, y + 30, size * 0.8, size * 0.6, colors.body)
  // 头
  fillCircle(x, y - 10, size * 0.7, colors.body)

  // 耳朵
  setFill(colors.body)
  ctx.value.beginPath()
  ctx.value.moveTo(x - size * 0.6, y - 30)
  ctx.value.lineTo(x - size * 0.9, y - size)
  ctx.value.lineTo(x - size * 0.2, y - 35)
  ctx.value.closePath()
  ctx.value.fill()

  ctx.value.beginPath()
  ctx.value.moveTo(x + size * 0.6, y - 30)
  ctx.value.lineTo(x + size * 0.9, y - size)
  ctx.value.lineTo(x + size * 0.2, y - 35)
  ctx.value.closePath()
  ctx.value.fill()

  // 眼睛
  fillCircle(x - size * 0.3, y - 15, size * 0.12, colors.eye)
  fillCircle(x + size * 0.3, y - 15, size * 0.12, colors.eye)

  // 嘴巴
  setStroke(colors.eye, 2)
  ctx.value.beginPath()
  ctx.value.arc(x, y - 2, size * 0.12, 0, Math.PI)
  ctx.value.stroke()

  // 腮红
  if (level >= 5) {
    fillCircle(x - size * 0.5, y, size * 0.18, 'rgba(255,150,150,0.4)')
    fillCircle(x + size * 0.5, y, size * 0.18, 'rgba(255,150,150,0.4)')
  }
}

const drawSlime = (x, y, colors, level, size) => {
  setFill(colors.body)
  ctx.value.beginPath()
  ctx.value.arc(x, y, size, Math.PI, 0)
  ctx.value.lineTo(x + size, y + 30)
  ctx.value.lineTo(x - size, y + 30)
  ctx.value.closePath()
  ctx.value.fill()

  // 眼睛
  fillCircle(x - size * 0.3, y + 5, size * 0.12, colors.eye)
  fillCircle(x + size * 0.3, y + 5, size * 0.12, colors.eye)
}

const drawBot = (x, y, colors, level, size) => {
  setFill(colors.body)
  ctx.value.fillRect(x - size * 0.7, y - size * 0.3, size * 1.4, size * 1.2)
  ctx.value.fillRect(x - size * 0.6, y - size * 1.1, size * 1.2, size * 0.9)

  // 眼睛
  setFill('#FFD700')
  ctx.value.fillRect(x - size * 0.35, y - size * 0.9, size * 0.3, size * 0.2)
  ctx.value.fillRect(x + size * 0.05, y - size * 0.9, size * 0.3, size * 0.2)
}

// 点击
const handleTap = () => {
  emit('tap')
  showFeedBtn.value = !showFeedBtn.value
}

// 长按隐藏宠物
const handleLongPress = () => {
  emit('toggleHide')
}

// 拖拽处理 - 使用绝对定位
let touchStartTime = 0
let movedDistance = 0

const onTouchStart = (e) => {
  touchStartTime = Date.now()
  movedDistance = 0
  dragStartX.value = e.touches[0].clientX
  dragStartY.value = e.touches[0].clientY
}

const onTouchMove = (e) => {
  const dx = e.touches[0].clientX - dragStartX.value
  const dy = e.touches[0].clientY - dragStartY.value
  movedDistance = Math.abs(dx) + Math.abs(dy)
  
  // 移动超过 10rpx 认为是拖拽
  if (movedDistance > 10) {
    isDragging.value = true
    currentX.value = Math.max(0, Math.min(500, currentX.value + dx))
    currentY.value = Math.max(0, Math.min(800, currentY.value + dy))
    dragStartX.value = e.touches[0].clientX
    dragStartY.value = e.touches[0].clientY
  }
}

const onTouchEnd = () => {
  const touchDuration = Date.now() - touchStartTime
  
  // 如果移动距离很小且时间很短，认为是点击
  if (movedDistance < 10 && touchDuration < 300) {
    handleTap()
  }
  
  if (isDragging.value) {
    isDragging.value = false
    emit('positionChange', { x: currentX.value, y: currentY.value })
  }
}

// 喂食
const handleFeed = () => {
  currentFoodEmoji.value = foodEmojis[Math.floor(Math.random() * foodEmojis.length)]
  showFoodAnim.value = true
  foodAnimClass.value = 'food-drop'

  setTimeout(() => {
    showFoodAnim.value = false
  }, 800)

  emit('feed')
}

// 数据变化时重画（加保护：确保 ctx 已就绪）
watch(
  () => props.petData,
  () => {
    if (ctx.value) {
      drawPet()
    }
  },
  { deep: true }
)

watch(
  () => props.styleConfig,
  () => {
    if (ctx.value) {
      drawPet()
    }
  },
  { deep: true }
)

// 修复：在数据更新时，如果退回 Canvas 模式，确保重新绘制
watch(
  () => props.customImage,
  (newVal, oldVal) => {
    if (!newVal && oldVal) {
      // 从有图片变为无图片时，重绘 Canvas
      nextTick(() => {
        setTimeout(() => {
          if (ctx.value) {
            drawPet() // 重新绘制，不要重新 init，上下文一直都在
          }
        }, 100)
      })
    }
  }
)

onMounted(() => {
  // 使用 nextTick + 延迟确保 Canvas 元素已挂载并准备好
  nextTick(() => {
    // 多次尝试初始化，防止某些情况下 DOM 未就绪
    const tryInit = () => {
      if (!ctx.value) {
        initCanvas()
      }
      // 如果还是拿不到 ctx，再试一次
      if (!ctx.value) {
        setTimeout(tryInit, 200)
      }
    }
    tryInit()
  })
})
</script>

<style scoped>
.pet-canvas-wrapper {
  position: fixed;
  z-index: 999;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: transform 0.05s;
}

.pet-canvas-wrapper.is-dragging {
  transform: scale(1.15);
  z-index: 1000;
}

.pet-touch-area {
  width: 160rpx;
  height: 160rpx;
}

.pet-image {
  width: 160rpx;
  height: 160rpx;
  animation: petFloat 3s ease-in-out infinite;
}

@keyframes petFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10rpx); }
}

.pet-canvas {
  background: transparent;
  width: 160rpx;
  height: 160rpx;
  animation: petFloat 3s ease-in-out infinite;
}

.feed-btn {
  position: absolute;
  top: 10rpx;
  right: -40rpx;
  min-width: 60rpx;
  height: 60rpx;
  background: linear-gradient(135deg, #FF6B6B, #FF8E53);
  border-radius: 30rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(255, 107, 107, 0.4);
  animation: pulse 2s infinite;
  padding: 0 16rpx;
}

.feed-icon {
  font-size: 32rpx;
}

.feed-count {
  font-size: 20rpx;
  color: #fff;
  font-weight: bold;
  margin-left: 4rpx;
}

.level-badge {
  position: absolute;
  top: -45rpx;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #ffd700, #ffa500);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.2);
}

.level-text {
  font-size: 20rpx;
  font-weight: bold;
  color: #fff;
}

.exp-bar {
  position: absolute;
  bottom: -25rpx;
  left: 0;
  right: 0;
  height: 6rpx;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3rpx;
  overflow: hidden;
}

.exp-fill {
  height: 100%;
  background: linear-gradient(90deg, #4A6FA5, #FF8A65);
  border-radius: 3rpx;
  transition: width 0.3s ease;
}

.food-anim {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  font-size: 40rpx;
}

.food-drop {
  animation: foodDrop 0.8s ease-out forwards;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes foodDrop {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(100rpx) scale(0.5);
  }
}
</style>