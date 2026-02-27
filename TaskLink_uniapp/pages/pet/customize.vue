<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="header">
      <view class="header-left" @click="goBack">
        <text class="back-icon">←</text>
        <text class="header-title">自定义宠物</text>
      </view>
      <view class="header-right">
        <text class="import-btn" @click="importImage">📁 导入图片</text>
        <text class="clear-btn" @click="clearCanvas">🗑️ 清空</text>
      </view>
    </view>

    <view class="main-content">
      <!-- 画布和预览并排 -->
      <view class="workspace">
        <!-- 手绘画布 -->
        <view class="draw-section">
          <text class="section-label">👆 手绘或导入图片</text>
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
          
          <!-- 紧凑工具栏 -->
          <view class="toolbar" v-if="!importedImage">
            <view class="tool-group">
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'brush' }"
                @click="currentTool = 'brush'"
              >
                <text class="tool-icon">✎</text>
                <text>画笔</text>
              </view>
              <view 
                class="tool-btn" 
                :class="{ active: currentTool === 'eraser' }"
                @click="currentTool = 'eraser'"
              >
                <text class="tool-icon">✕</text>
                <text>橡皮</text>
              </view>
            </view>
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
            <view class="size-control">
              <text class="size-label">粗细</text>
              <slider 
                :value="brushSize" 
                min="2" 
                max="20" 
                block-size="14"
                activeColor="#4A6FA5"
                @change="onSizeChange"
              />
            </view>
          </view>
          
          <view class="toolbar compact" v-else>
            <view class="tool-btn active" @click="removeImportedImage">
              <text>❌ 移除图片</text>
            </view>
          </view>
        </view>

        <!-- 预览区域 -->
        <view class="preview-section">
          <text class="section-label">👀 预览效果</text>
          <view class="preview-canvas-wrapper">
          <!-- 导入的图片预览 -->
          <image 
            v-if="importedImage" 
            :src="importedImage" 
            class="preview-image"
            mode="aspectFit"
          />
          <!-- 绘制内容预览 -->
          <image 
            v-else-if="generatedImage" 
            :src="generatedImage" 
            class="preview-image"
            mode="aspectFit"
          />
          <!-- 空状态 -->
          <view v-else class="preview-empty">
            <text>暂无预览</text>
          </view>
        </view>
        <view class="preview-actions">
          <button class="preview-btn" @click="generatePet" :disabled="isGenerating || !hasDrawing">
            <text>{{ isGenerating ? '处理中...' : '✨ 确认预览' }}</text>
          </button>
        </view>
      </view>
    </view>

    <!-- 保存按钮 -->
    <view class="save-section">
      <button class="save-btn" @click="savePet" :disabled="!canSave">
        <text>💾 保存到数据库</text>
      </button>
    </view>

    <!-- 提示 -->
    <view class="tips" v-if="!canSave">
    </view>
  </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/useTheme'

const { isDarkMode } = useTheme()

const API_BASE = `http://101.35.132.175:5000`

// 画笔工具
const currentTool = ref('brush')
const currentColor = ref('#000000')
const brushSize = ref(8)
const colors = ['#000000', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FF8C00']

// 画布相关
const drawCtx = ref(null)
const isDrawing = ref(false)
const lastPoint = ref({ x: 0, y: 0 })
const hasDrawing = ref(false)

// 导入图片
const importedImage = ref('')

// 生成相关
const generatedImage = ref(null)
const isGenerating = ref(false)

// 计算是否可以保存
const canSave = computed(() => {
  return importedImage.value || generatedImage.value
})

// 初始化画布（透明背景）
const initCanvas = () => {
  drawCtx.value = uni.createCanvasContext('drawCanvas')

  // 不画白色背景，保持透明
  // drawCtx.value.setFillStyle('transparent')
  // drawCtx.value.fillRect(0, 0, 600, 600)
  // 不需要 draw()，保持透明

  hasDrawing.value = false
}

// 绘制开始
const onDrawStart = (e) => {
  isDrawing.value = true
  const point = e.touches[0]
  lastPoint.value = { x: point.x, y: point.y }

  if (currentTool.value === 'eraser') {
    // 橡皮擦：使用透明擦除
    // H5 端使用 destination-out 模式实现真正透明
    // #ifdef H5
    // H5 端暂不支持 canvas 2d 的 destination-out，这里用白色代替
    drawCtx.value.setStrokeStyle('#FFFFFF')
    // #endif
    // #ifndef H5
    // App/小程序端使用 globalCompositeOperation 实现透明擦除
    // 注意：uni.createCanvasContext 默认不支持，需要用 node 模式
    // 这里暂时也用白色代替，实际透明需要更高版本支持
    drawCtx.value.setStrokeStyle('#FFFFFF')
    // #endif
    drawCtx.value.setLineWidth(brushSize.value * 2)
  } else {
    drawCtx.value.setStrokeStyle(currentColor.value)
    drawCtx.value.setLineWidth(brushSize.value)
  }
  drawCtx.value.setLineCap('round')
  drawCtx.value.setLineJoin('round')
}

// 绘制移动
const onDrawMove = (e) => {
  if (!isDrawing.value) return
  
  const point = e.touches[0]
  
  drawCtx.value.beginPath()
  drawCtx.value.moveTo(lastPoint.value.x, lastPoint.value.y)
  drawCtx.value.lineTo(point.x, point.y)
  drawCtx.value.stroke()
  drawCtx.value.draw(true)
  
  hasDrawing.value = true
  lastPoint.value = { x: point.x, y: point.y }
}

// 绘制结束
const onDrawEnd = () => {
  isDrawing.value = false
}

// 清空画布
const clearCanvas = () => {
  drawCtx.value.setFillStyle('#FFFFFF')
  drawCtx.value.fillRect(0, 0, 600, 600)
  drawCtx.value.draw()
  generatedImage.value = null
  hasDrawing.value = false
}

// 导入图片
const importImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      if (res.tempFilePaths && res.tempFilePaths.length > 0) {
        importedImage.value = res.tempFilePaths[0]
        generatedImage.value = null
        uni.showToast({ title: '图片导入成功', icon: 'success' })
      }
    },
    fail: () => {
      uni.showToast({ title: '取消选择', icon: 'none' })
    }
  })
}

// 移除导入的图片
const removeImportedImage = () => {
  importedImage.value = ''
  clearCanvas()
}

// 笔触大小改变
const onSizeChange = (e) => {
  brushSize.value = e.detail.value
}

// 生成宠物预览
const generatePet = () => {
  if (isGenerating.value) return
  
  if (!hasDrawing.value && !importedImage.value) {
    uni.showToast({ title: '请先绘制或导入图片', icon: 'none' })
    return
  }
  
  isGenerating.value = true
  
  // 如果有导入的图片，直接使用
  if (importedImage.value) {
    generatedImage.value = importedImage.value
    isGenerating.value = false
    uni.showToast({ title: '预览生成成功！', icon: 'success' })
    return
  }
  
  // 否则从画布导出
  uni.canvasToTempFilePath({
    canvasId: 'drawCanvas',
    success: (res) => {
      generatedImage.value = res.tempFilePath
      uni.showToast({ title: '预览生成成功！', icon: 'success' })
    },
    fail: (err) => {
      console.error('导出失败:', err)
      uni.showToast({ title: '预览生成失败', icon: 'none' })
    },
    complete: () => {
      isGenerating.value = false
    }
  })
}

// 保存宠物到数据库
const savePet = async () => {
  const userInfo = uni.getStorageSync('userInfo')
  if (!userInfo) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  
  const imageToSave = importedImage.value || generatedImage.value
  if (!imageToSave) {
    uni.showToast({ title: '请先生成预览', icon: 'none' })
    return
  }
  
  uni.showLoading({ title: '保存中...' })
  
  // 处理图片路径，转为 base64
  const processImage = async (path) => {
    // 判断是本地临时路径还是 base64 数据
    if (path.startsWith('data:')) {
      return path // 已经是 base64
    }
    
    // #ifdef H5
    // H5 端：直接使用 base64 图片
    return path
    // #endif
    
    // #ifndef H5
    // App/小程序端：使用 uni.getFileSystemManager 读取
    try {
      const fs = uni.getFileSystemManager()
      const base64 = fs.readFileSync(path, 'base64')
      return 'data:image/png;base64,' + base64
    } catch (e) {
      console.error('读取图片失败:', e)
      return path
    }
    // #endif
  }
  
  try {
    // 异步处理图片
    const imageBase64 = await processImage(imageToSave)
    
    // 调用后端 API 保存宠物图像
    uni.request({
      url: `${API_BASE}/api/pet/custom`,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: {
        user_id: userInfo.id,
        image_data: imageBase64
      },
      success: (res) => {
        uni.hideLoading()
        if (res.data.code === 200) {
          uni.showToast({ title: '保存成功！', icon: 'success' })
          
          // 同时保存到本地缓存一份
          uni.setStorageSync('customPetImage', imageToSave)
          
          setTimeout(() => {
            goBack()
          }, 1500)
        } else {
          // 后端保存失败，保存到本地
          uni.setStorageSync('customPetImage', imageToSave)
          uni.showToast({ title: '已本地保存', icon: 'success' })
          setTimeout(() => {
            goBack()
          }, 1500)
        }
      },
      fail: () => {
        // 网络错误，保存到本地
        uni.hideLoading()
        uni.setStorageSync('customPetImage', imageToSave)
        uni.showToast({ title: '已本地保存', icon: 'success' })
        setTimeout(() => {
          goBack()
        }, 1500)
      }
    })
  } catch (e) {
    console.error('保存失败:', e)
    uni.hideLoading()
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

// 返回
const goBack = () => {
  uni.navigateBack()
}

onMounted(() => {
  initCanvas()
})
</script>

<style scoped lang="scss">
.container {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 120rpx;
}

.container.dark {
  background: #1a1a2e;
  color: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 40rpx;
  background: #fff;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.container.dark .header {
  background: #16213e;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}

.header-title {
  font-size: 34rpx;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.import-btn, .clear-btn {
  font-size: 26rpx;
  color: #666;
}

.container.dark .import-btn,
.container.dark .clear-btn {
  color: #aaa;
}

.container.dark .clear-btn {
  color: #aaa;
}

.main-content {
  padding: 24rpx;
}

.workspace {
  display: flex;
  gap: 24rpx;
  align-items: flex-start;
}

.draw-section {
  flex: 1;
  min-width: 0;
}

.preview-section {
  width: 240rpx;
  flex-shrink: 0;
}

.section-label {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 16rpx;
  display: block;
  font-weight: 500;
}

.container.dark .section-label {
  color: #aaa;
}

.draw-canvas {
  width: 100%;
  height: 400rpx;
  background: #fff;
  border-radius: 20rpx;
  margin: 0 auto;
  display: block;
  box-shadow: 
    0 6rpx 20rpx rgba(0, 0, 0, 0.1),
    inset 0 0 0 1rpx rgba(74, 111, 165, 0.08);
  border: 2rpx solid rgba(74, 111, 165, 0.12);
}

.container.dark .draw-canvas {
  background: #1a1a2e;
  box-shadow: 
    0 8rpx 30rpx rgba(0, 0, 0, 0.4),
    inset 0 0 0 1rpx rgba(74, 111, 165, 0.2);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 20rpx;
  flex-wrap: wrap;
  justify-content: space-between;
}

.toolbar.compact {
  justify-content: center;
}

.tool-group {
  display: flex;
  gap: 12rpx;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 14rpx 22rpx;
  background: #fff;
  border-radius: 30rpx;
  font-size: 26rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  border: 2rpx solid transparent;
}

.container.dark .tool-btn {
  background: #1a1a2e;
  color: #e0e0e0;
}

.tool-btn.active {
  background: linear-gradient(135deg, #4A6FA5 0%, #3D5A80 100%);
  color: #fff;
  box-shadow: 0 4rpx 15rpx rgba(74, 111, 165, 0.4);
  border-color: rgba(255, 255, 255, 0.2);
}

.tool-icon {
  font-size: 28rpx;
  font-weight: bold;
}

.color-picker {
  display: flex;
  gap: 12rpx;
}

.color-dot {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  border: 3rpx solid transparent;
  transition: all 0.2s;
}

.color-dot.active {
  border-color: #4A6FA5;
  transform: scale(1.2);
}

.size-slider {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.size-label {
  font-size: 24rpx;
  color: #666;
}

.size-slider slider {
  width: 150rpx;
}

.preview-section {
  text-align: center;
}

.preview-canvas-wrapper {
  width: 300rpx;
  height: 300rpx;
  margin: 0 auto;
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 
    0 8rpx 30rpx rgba(0, 0, 0, 0.12),
    inset 0 0 0 1rpx rgba(74, 111, 165, 0.1);
  border: 3rpx solid rgba(74, 111, 165, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.container.dark .preview-canvas-wrapper {
  background: #1a1a2e;
}

.preview-canvas {
  width: 300rpx;
  height: 300rpx;
}

.preview-image {
  width: 280rpx;
  height: 280rpx;
  object-fit: contain;
}

.preview-empty {
  width: 300rpx;
  height: 300rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-size: 26rpx;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 20rpx;
}

.container.dark .preview-empty {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.preview-actions {
  margin-top: 30rpx;
}

.preview-btn {
  background: linear-gradient(135deg, #4A6FA5 0%, #6B8DD6 100%);
  color: #fff;
  padding: 22rpx 60rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  box-shadow: 0 6rpx 20rpx rgba(74, 111, 165, 0.35);
  border: none;
}

.preview-btn[disabled] {
  background: #ccc;
}

.save-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 30rpx;
  background: #fff;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.container.dark .save-section {
  background: #16213e;
}

.save-btn {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: #fff;
  padding: 26rpx;
  border-radius: 44rpx;
  font-size: 32rpx;
  font-weight: bold;
  text-align: center;
  box-shadow: 0 8rpx 25rpx rgba(255, 107, 107, 0.4);
  border: none;
}

.save-btn[disabled] {
  background: linear-gradient(135deg, #c8c8c8 0%, #a8a8a8 100%);
  box-shadow: none;
}

.tips {
  position: fixed;
  bottom: 140rpx;
  left: 30rpx;
  right: 30rpx;
  text-align: center;
  font-size: 24rpx;
  color: #999;
}
</style>
