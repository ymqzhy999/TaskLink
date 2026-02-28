<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="header">
      <view class="header-left" @click="goBack">
        <text class="back-icon">←</text>
        <text class="header-title">手绘宠物</text>
      </view>
      <view class="header-right">
        <view class="action-btn" @click="importImage">
          <text class="icon">📁</text>
          <text>导入</text>
        </view>
        <view class="action-btn danger" @click="clearCanvas">
          <text class="icon">🗑️</text>
          <text>清空</text>
        </view>
      </view>
    </view>

    <view class="main-content">
      <view class="canvas-section">
        <view class="canvas-header">
          <text class="section-badge">🖍️ 创作区</text>
        </view>
        
        <view class="canvas-wrapper">
          <canvas
            canvas-id="drawCanvas"
            id="drawCanvas"
            class="draw-canvas"
            :style="{ background: 'transparent' }"
            @touchstart="onDrawStart"
            @touchmove="onDrawMove"
            @touchend="onDrawEnd"
            disable-scroll
          ></canvas>
        </view>

        <view class="toolbar" v-if="!importedImage">
          <view class="tool-row">
            <view class="tool-group tools-grid">
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'brush' }"
                @click="currentTool = 'brush'"
              >
                <text class="tool-icon">✎</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'eraser' }"
                @click="currentTool = 'eraser'"
              >
                <text class="tool-icon">▱</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'line' }"
                @click="currentTool = 'line'"
              >
                <text class="tool-icon">╱</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'rect' }"
                @click="currentTool = 'rect'"
              >
                <text class="tool-icon">□</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'circle' }"
                @click="currentTool = 'circle'"
              >
                <text class="tool-icon">○</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'fill' }"
                @click="currentTool = 'fill'"
              >
                <text class="tool-icon">♨</text>
              </view>
            </view>
            
            <view class="tool-btn remove-img" v-if="importedImage" @click="removeImportedImage">
              <text>✖</text>
            </view>
          </view>

          <view class="color-section">
            <text class="section-title">色彩</text>
            <view class="color-picker">
              <view 
                v-for="color in colors" 
                :key="color"
                class="color-dot"
                :class="{ active: currentColor === color }"
                :style="{ backgroundColor: color }"
                @click="currentColor = color"
              ></view>
            </view>
          </view>

          <view class="size-section">
            <text class="section-title">画笔粗细</text>
            <view class="size-row">
              <view class="size-preview-dot" :style="{ width: brushSize + 'px', height: brushSize + 'px', backgroundColor: currentColor === '#FFFFFF' ? '#E0E0E0' : currentColor }"></view>
              <slider 
                class="size-slider"
                :value="brushSize" 
                min="2" 
                max="30" 
                block-size="18"
                activeColor="#FF6B6B"
                backgroundColor="#F0F0F0"
                block-color="#FFFFFF"
                @change="onSizeChange"
                @changing="onSizeChanging"
              />
              <text class="size-value">{{ brushSize }}px</text>
            </view>
          </view>
        </view>

        <view class="imported-tip" v-else>
          <view class="tip-content">
            <text>🖼️ 成功导入图片</text>
            <text class="link-btn" @click="removeImportedImage">撤销图片</text>
          </view>
        </view>
      </view>

      <view class="preview-section">
        <view class="canvas-header">
          <text class="section-badge">👀 最终预览</text>
        </view>
        
        <view class="preview-content">
          <view class="preview-wrapper">
            <image 
              v-if="importedImage" 
              :src="importedImage" 
              class="preview-image"
              mode="aspectFit"
            />
            <image 
              v-else-if="generatedImage" 
              :src="generatedImage" 
              class="preview-image"
              mode="aspectFit"
            />
            <view v-else class="preview-empty">
              <text class="empty-icon">✨</text>
              <text>等待生成魔法</text>
            </view>
          </view>

          <view class="preview-actions">
            <button 
              class="generate-btn" 
              :class="{ 'is-loading': isGenerating }"
              @click="generatePet" 
              :disabled="isGenerating || (!hasDrawing && !importedImage)"
            >
              <text>{{ isGenerating ? '魔法处理中...' : '生成预览图' }}</text>
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>

  <view class="save-bar" :class="{ 'dark': isDarkMode }">
    <button class="save-btn" @click="savePet" :disabled="!importedImage && !generatedImage">
      <text>💾 保存到我的宠物</text>
    </button>
  </view>
</template>
<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue'
import { useTheme } from '@/utils/useTheme'
import { post } from '@/utils/request.js'

const { isDarkMode } = useTheme()
const instance = getCurrentInstance()

// 工具与样式
const currentTool = ref('brush')
const currentColor = ref('#2C3E50')
const brushSize = ref(8)
const colors = [
  '#2C3E50', '#E74C3C', '#3498DB', '#27AE60', 
  '#F39C12', '#9B59B6', '#1ABC9C', '#34495E',
  '#E91E63', '#00BCD4', '#8BC34A', '#FF5722',
  '#795548', '#607D8B', '#FFC107', '#673AB7'
]

// 画布相关
const drawCtx = ref(null)
const isDrawing = ref(false)
const lastPoint = ref({ x: 0, y: 0 })
const hasDrawing = ref(false)

const importedImage = ref('')
const generatedImage = ref(null)
const isGenerating = ref(false)

const initCanvas = () => {
  drawCtx.value = uni.createCanvasContext('drawCanvas', instance?.proxy)
  hasDrawing.value = false
  
  // 初始化时，填充一个白色背景，防止导出时变成黑色背景
  drawCtx.value.setFillStyle('#FFFFFF')
  drawCtx.value.fillRect(0, 0, 300, 300)
  drawCtx.value.draw()
}

// ✅ 修复 1 & 4：简化坐标获取，直接使用原生的 e.touches[0].x 和 y
// UniApp 原生的 canvas touch 事件天然支持相对画布的 x/y，不需要复杂转换！
const getTouchPoint = (e) => {
  const point = e.touches[0]
  if (typeof point.x === 'number' && typeof point.y === 'number') {
    return { x: point.x, y: point.y }
  }
  // 极端降级情况（极少发生）
  return { x: point.clientX, y: point.clientY }
}

const onDrawStart = (e) => {
  if (e.cancelable && !e.defaultPrevented) e.preventDefault()
  if (importedImage.value || !drawCtx.value) return
  
  isDrawing.value = true
  lastPoint.value = getTouchPoint(e)
  
  // ✅ 修复 2：彻底抛弃有兼容性问题的 setGlobalCompositeOperation
  // 橡皮擦的本质：用白色的粗笔去覆盖即可！
  drawCtx.value.beginPath()
  drawCtx.value.setLineCap('round')
  drawCtx.value.setLineJoin('round')
  
  if (currentTool.value === 'eraser') {
    drawCtx.value.setStrokeStyle('#FFFFFF') // 使用白色作为橡皮擦
    drawCtx.value.setLineWidth(brushSize.value * 2) // 橡皮擦稍微大一点
  } else {
    drawCtx.value.setStrokeStyle(currentColor.value)
    drawCtx.value.setLineWidth(brushSize.value)
  }
}

const onDrawMove = (e) => {
  if (e.cancelable && !e.defaultPrevented) e.preventDefault()
  if (!isDrawing.value || importedImage.value || !drawCtx.value) return
  
  const currentPoint = getTouchPoint(e)
  
  drawCtx.value.moveTo(lastPoint.value.x, lastPoint.value.y)
  drawCtx.value.lineTo(currentPoint.x, currentPoint.y)
  drawCtx.value.stroke()
  drawCtx.value.draw(true) // true 表示保留之前的绘制内容
  
  hasDrawing.value = true
  lastPoint.value = currentPoint
}

const onDrawEnd = () => {
  isDrawing.value = false
}

// ✅ 修复 3：使用 fillRect 覆盖实现彻底清空
const clearCanvas = () => {
  if (!drawCtx.value) return
  
  // 填充白色背景覆盖一切
  drawCtx.value.setFillStyle('#FFFFFF')
  drawCtx.value.fillRect(0, 0, 300, 300)
  drawCtx.value.draw(false) // false 表示清除之前的绘画记录

  importedImage.value = ''
  generatedImage.value = null
  hasDrawing.value = false
  uni.showToast({ title: '已清空', icon: 'none' })
}

const importImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      if (res.tempFilePaths && res.tempFilePaths.length > 0) {
        importedImage.value = res.tempFilePaths[0]
        generatedImage.value = res.tempFilePaths[0]
        hasDrawing.value = false
        uni.showToast({ title: '图片导入成功', icon: 'success' })
      }
    }
  })
}

const removeImportedImage = () => {
  importedImage.value = ''
  generatedImage.value = null
  clearCanvas()
}

// 画笔大小改变
const onSizeChange = (e) => { brushSize.value = e.detail.value }
const onSizeChanging = (e) => { brushSize.value = e.detail.value }

const generatePet = () => {
  if (isGenerating.value) return
  if (!hasDrawing.value && !importedImage.value) {
    uni.showToast({ title: '请先绘制或导入图片', icon: 'none' })
    return
  }
  
  isGenerating.value = true
  
  if (importedImage.value) {
    generatedImage.value = importedImage.value
    isGenerating.value = false
    uni.showToast({ title: '预览生成成功！', icon: 'success' })
    return
  }
  
  // 从画布导出
  uni.canvasToTempFilePath({
    canvasId: 'drawCanvas',
    width: 300,
    height: 300,
    destWidth: 300,
    destHeight: 300,
    success: (res) => {
      generatedImage.value = res.tempFilePath
      uni.showToast({ title: '预览生成成功！', icon: 'success' })
    },
    fail: (err) => {
      console.error('导出失败:', err)
      uni.showToast({ title: '预览生成失败', icon: 'none' })
    },
    complete: () => { isGenerating.value = false }
  }, instance?.proxy)
}

const processImage = (path) => {
  return new Promise((resolve, reject) => {
    if (!path) return resolve('')
    if (path.startsWith('data:') || path.includes('base64,')) return resolve(path)

    // #ifdef APP-PLUS
    plus.io.resolveLocalFileSystemURL(path, (entry) => {
      entry.file((file) => {
        const fileReader = new plus.io.FileReader()
        fileReader.onload = (data) => resolve(data.target.result)
        fileReader.onerror = () => resolve('')
        fileReader.readAsDataURL(file)
      })
    }, () => resolve(''))
    return
    // #endif

    // #ifndef APP-PLUS
    if (typeof uni.getFileSystemManager === 'function') {
      try {
        const fs = uni.getFileSystemManager()
        const result = fs.readFileSync(path, 'base64')
        return resolve('data:image/png;base64,' + result)
      } catch (e) { console.error(e) }
    }
    
    uni.request({
      url: path,
      method: 'GET',
      responseType: 'arraybuffer',
      success: (res) => resolve('data:image/png;base64,' + uni.arrayBufferToBase64(res.data)),
      fail: () => resolve('')
    })
    // #endif
  })
}

const savePet = async () => {
  const userInfo = uni.getStorageSync('userInfo')
  if (!userInfo) return uni.showToast({ title: '请先登录', icon: 'none' })
  
  const imageToSave = importedImage.value || generatedImage.value
  uni.showLoading({ title: '数据同步中...' })
  
  try {
    const imageBase64 = await processImage(imageToSave)
    
    // 使用封装好的 post 请求
    const result = await post('/api/pet/custom', { 
      user_id: userInfo.id, 
      image_data: imageBase64 
    })
    
    uni.hideLoading()
    if (!imageBase64) {
      uni.showToast({ title: '已恢复默认宠物', icon: 'success' })
    } else {
      uni.showToast({ title: '保存成功！', icon: 'success' })
    }
    uni.setStorageSync('customPetImage', imageBase64)
    setTimeout(() => goBack(), 1500)
  } catch (e) {
    uni.hideLoading()
    // 错误已经被 request.js 处理过了，这里直接提示
    const msg = e?.message || '保存失败'
    if (msg !== '会话过期') {
      uni.showToast({ title: msg, icon: 'none' })
    }
  }
}

const goBack = () => uni.navigateBack()

onMounted(() => initCanvas())
</script>

<style scoped lang="scss">
// 现代化清新配色
$primary: #FF6B6B;        
$primary-light: #FF8E8E;
$secondary: #4ECDC4;      
$dark: #2B2D42;           
$bg-light: #F8F9FA;          
$card-bg: #FFFFFF;
$danger: #FF5252;
$gray: #8D99AE;
$border-color: #EDF2F4;

.container {
  min-height: 100vh;
  background: $bg-light;
  padding-bottom: 160rpx; // 为底部按钮留出空间
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
}

.container.dark {
  background: #0F0F1A;
  color: #E2E2E2;
}

// 顶部导航
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 88rpx 32rpx 24rpx; // 适配状态栏
  background: $card-bg;
  border-bottom: 1rpx solid $border-color;
  position: sticky;
  top: 0;
  z-index: 100;
}

.container.dark .header {
  background: #181824;
  border-bottom-color: #2A2A35;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-icon {
  font-size: 36rpx;
  color: $dark;
  margin-right: 12rpx;
  font-weight: bold;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: $dark;
}

.container.dark .back-icon,
.container.dark .header-title {
  color: #FFFFFF;
}

.header-right {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 24rpx;
  background: $bg-light;
  border-radius: 30rpx;
  font-size: 24rpx;
  font-weight: 500;
  color: $dark;
  transition: all 0.2s;
}

.action-btn:active {
  transform: scale(0.95);
}

.action-btn.danger {
  background: rgba($danger, 0.08);
  color: $danger;
}

.container.dark .action-btn {
  background: #252535;
  color: #E2E2E2;
}

// 主内容区
.main-content {
  display: flex;
  flex-direction: column;
  padding: 32rpx 24rpx;
  gap: 32rpx;
}

// 通用卡片样式
.canvas-section, .preview-section {
  background: $card-bg;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 8rpx 30rpx rgba(141, 153, 174, 0.08);
  border: 1rpx solid rgba(255,255,255,0.8);
}

.container.dark .canvas-section, 
.container.dark .preview-section {
  background: #181824;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.3);
  border-color: #2A2A35;
}

.canvas-header {
  margin-bottom: 24rpx;
}

.section-badge {
  display: inline-block;
  font-size: 24rpx;
  font-weight: 600;
  color: $dark;
  background: $bg-light;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}

.container.dark .section-badge {
  color: #FFF;
  background: #252535;
}

// 核心修复：画布区域必须写死为 300px，否则 JS 的 300x300 坐标系全乱
.canvas-wrapper {
  width: 300px;
  height: 300px;
  margin: 0 auto;
  background: #FFFFFF; // 必须是白色，防止深色模式下变黑影响导出
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: inset 0 0 0 2rpx $border-color;
  position: relative;
}

.container.dark .canvas-wrapper {
  box-shadow: inset 0 0 0 2rpx #333;
}

.draw-canvas {
  width: 300px;
  height: 300px;
  position: absolute;
  top: 0;
  left: 0;
  touch-action: none; // 核心修复：阻止页面跟随手指滑动
}

// 工具栏
.toolbar {
  margin-top: 32rpx;
  padding-top: 24rpx;
  border-top: 2rpx dashed $border-color;
}

.container.dark .toolbar {
  border-top-color: #2A2A35;
}

.tool-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16rpx;
  width: 100%;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 76rpx;
  background: $bg-light;
  border-radius: 20rpx;
  color: $gray;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2rpx solid transparent;
}

.tool-icon {
  font-size: 32rpx;
}

.tool-btn.active {
  background: rgba($primary, 0.1);
  color: $primary;
  border-color: rgba($primary, 0.3);
  transform: translateY(-4rpx);
}

.container.dark .tool-btn {
  background: #252535;
  color: #8D99AE;
}

.container.dark .tool-btn.active {
  background: rgba($primary, 0.15);
  color: $primary-light;
  border-color: rgba($primary, 0.4);
}

// 小标题
.section-title {
  font-size: 24rpx;
  color: $gray;
  font-weight: 500;
  margin-bottom: 16rpx;
  display: block;
}

// 颜色选择
.color-section {
  margin-top: 24rpx;
}

.color-picker {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 16rpx 12rpx;
}

.color-dot {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  border: 4rpx solid transparent;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  box-sizing: border-box;
}

.color-dot.active {
  transform: scale(1.2);
  border-color: $dark;
  box-shadow: 0 6rpx 16rpx rgba(0, 0, 0, 0.15);
}

.container.dark .color-dot.active {
  border-color: #FFFFFF;
}

// 粗细调节
.size-section {
  margin-top: 32rpx;
  background: $bg-light;
  padding: 16rpx 24rpx;
  border-radius: 24rpx;
}

.container.dark .size-section {
  background: #252535;
}

.size-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.size-preview-dot {
  border-radius: 50%;
  background-color: $dark;
  transition: all 0.1s;
}

.size-slider {
  flex: 1;
  margin: 0;
}

.size-value {
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
  width: 60rpx;
  text-align: right;
}

// 导入提示区
.imported-tip {
  margin-top: 32rpx;
  background: rgba($secondary, 0.08);
  border-radius: 20rpx;
  padding: 24rpx;
}

.tip-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 26rpx;
  color: $dark;
  font-weight: 500;
}

.container.dark .tip-content {
  color: #FFF;
}

.link-btn {
  color: $danger;
  background: rgba($danger, 0.1);
  padding: 8rpx 20rpx;
  border-radius: 24rpx;
  font-size: 24rpx;
}

// 预览区内部
.preview-content {
  display: flex;
  align-items: center;
  gap: 32rpx;
}

.preview-wrapper {
  width: 200rpx;
  height: 200rpx;
  background: $bg-light;
  border-radius: 24rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2rpx dashed $border-color;
  flex-shrink: 0;
}

.container.dark .preview-wrapper {
  background: #252535;
  border-color: #333;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  color: $gray;
  font-size: 22rpx;
}

.empty-icon {
  font-size: 40rpx;
}

.preview-actions {
  flex: 1;
}

.generate-btn {
  width: 100%;
  padding: 0;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, $secondary 0%, #38B2A6 100%);
  color: #FFF;
  border-radius: 24rpx;
  font-size: 28rpx;
  font-weight: 600;
  border: none;
  box-shadow: 0 8rpx 24rpx rgba($secondary, 0.3);
}

.generate-btn::after {
  display: none; // 移除小程序原生边框
}

.generate-btn[disabled] {
  background: #E2E8F0;
  box-shadow: none;
  color: #94A3B8;
}

.container.dark .generate-btn[disabled] {
  background: #2A2A35;
  color: #666;
}

// 底部保存悬浮栏
.save-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 40rpx calc(24rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-top: 1rpx solid rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.save-bar.dark {
  background: rgba(24, 24, 36, 0.9);
  border-top-color: rgba(255, 255, 255, 0.05);
}

.save-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  background: $dark;
  color: #FFF;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  box-shadow: 0 12rpx 32rpx rgba($dark, 0.25);
  transition: all 0.3s;
}

.save-bar.dark .save-btn {
  background: $primary;
  box-shadow: 0 12rpx 32rpx rgba($primary, 0.25);
}

.save-btn::after {
  display: none;
}

.save-btn:active {
  transform: scale(0.98);
}

.save-btn[disabled] {
  background: #E2E8F0;
  box-shadow: none;
  color: #94A3B8;
}

.save-bar.dark .save-btn[disabled] {
  background: #2A2A35;
  color: #555;
}
</style>
