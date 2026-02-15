<template>
  <view class="container">
    <view class="header-section">
      <view class="header-content">
        <text class="page-title">Create New Plan</text>
        <text class="page-subtitle">制定你的专属成长路径</text>
      </view>
      <view class="status-badge">
        <view class="status-dot"></view>
        <text>Ready</text>
      </view>
    </view>

    <view class="form-container fade-in">
      
      <view class="input-card">
        <view class="label-row">
          <text class="label-text">核心目标</text>
          <text class="label-count">{{ planForm.goal.length }}/50</text>
        </view>
        <view class="input-wrapper">
          <input 
            class="custom-input" 
            v-model="planForm.goal" 
            placeholder="例如：7天掌握 Python 基础" 
            placeholder-class="ph-style"
            :maxlength="50"
          />
        </view>
      </view>

      <view class="input-card">
        <view class="label-row">
          <text class="label-text">最终预期 (可选)</text>
        </view>
        <view class="input-wrapper area-wrapper">
          <textarea 
            class="custom-textarea" 
            v-model="planForm.expectation" 
            placeholder="描述你希望达成的具体效果，越详细越好..." 
            placeholder-class="ph-style"
            :maxlength="200"
            auto-height
          />
        </view>
      </view>

      <view class="input-card">
        <view class="label-row">
          <text class="label-text">执行周期 (天)</text>
        </view>
        <view class="input-wrapper">
          <input 
            class="custom-input" 
            type="number" 
            v-model="planForm.days" 
            placeholder="推荐 3-21 天" 
            placeholder-class="ph-style"
          />
        </view>
      </view>

    </view>

    <view class="footer-section">
      <button 
        class="generate-btn" 
        :class="{ 'btn-disabled': isGenerating }" 
        @click="generatePlan"
        :disabled="isGenerating"
      >
        <text v-if="!isGenerating">生成智能计划</text>
        <view v-else class="btn-loading-content">
          <view class="mini-spinner"></view>
          <text>正在生成...</text>
        </view>
      </button>
    </view>

    <view class="loading-modal" v-if="isGenerating">
      <view class="modal-card">
        <view class="spinner-ring"></view>
        <text class="loading-title">正在规划路径</text>
        <text class="loading-desc">{{ loadingStepText }}</text>
        
        <view class="progress-bar-bg">
          <view class="progress-bar-fill" :style="{ width: progressWidth + '%' }"></view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';

const API_BASE = `http://101.35.132.175:5000`;
const planForm = ref({ goal: '', expectation: '', days: '' });
const isGenerating = ref(false);

const loadingStepText = ref('初始化请求...');
const progressWidth = ref(0);
let progressTimer = null;
let stepTimer = null;

const loadingSteps = [
  "正在拆解目标语义...",
  "检索知识图谱关联...",
  "构建学习路径依赖树...",
  "估算时间成本与风险...",
  "生成 Markdown 渲染层...",
  "正在封装战术手册..."
];

const startLoadingAnim = () => {
  progressWidth.value = 0;
  let stepIndex = 0;
  loadingStepText.value = loadingSteps[0];
  
  // 模拟进度条
  progressTimer = setInterval(() => {
    if (progressWidth.value < 95) {
      progressWidth.value += (Math.random() * 3);
    }
  }, 150);

  // 模拟步骤文字切换
  stepTimer = setInterval(() => {
    stepIndex++;
    if (stepIndex < loadingSteps.length) {
      loadingStepText.value = loadingSteps[stepIndex];
    }
  }, 1200);
};

const stopLoadingAnim = () => {
  clearInterval(progressTimer);
  clearInterval(stepTimer);
  progressWidth.value = 100;
};

const generatePlan = () => {
  if (!planForm.value.goal.trim()) return uni.showToast({ title: '请输入核心目标', icon: 'none' });
  
  const d = parseInt(planForm.value.days);
  if (!d || d <= 0) return uni.showToast({ title: '请输入有效天数', icon: 'none' });

  const userInfo = uni.getStorageSync('userInfo');
  if (!userInfo) return uni.showToast({ title: '用户未登录', icon: 'none' });

  isGenerating.value = true;
  startLoadingAnim();

  uni.request({
    url: `${API_BASE}/api/plan/generate`,
    method: 'POST',
    data: { 
      user_id: userInfo.id, 
      goal: planForm.value.goal, 
      days: d,
      expectation: planForm.value.expectation
    },
    timeout: 120000, 
    success: (res) => {
      stopLoadingAnim();
      if (res.data.code === 200) {
        // 延迟跳转，展示100%进度
        setTimeout(() => {
          isGenerating.value = false;
          uni.navigateTo({ url: `/pages/plan/detail?id=${res.data.data.plan_id}` });
        }, 800);
      } else {
        isGenerating.value = false;
        uni.showToast({ title: '生成失败: ' + res.data.msg, icon: 'none' });
      }
    },
    fail: (err) => {
      stopLoadingAnim();
      isGenerating.value = false;
      uni.showToast({ title: '网络请求超时', icon: 'none' });
    }
  });
};

onUnmounted(() => {
  stopLoadingAnim();
});
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */
$color-line: #E0E0E0;

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
}

.container {
  min-height: 100vh;
  padding: 0 40rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* 2. 头部 */
.header-section {
  padding-top: var(--status-bar-height);
  margin-top: 40rpx;
  margin-bottom: 60rpx;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $color-text-main;
  display: block;
  margin-bottom: 8rpx;
}

.page-subtitle {
  font-size: 24rpx;
  color: $color-text-sub;
  letter-spacing: 1px;
}

.status-badge {
  display: flex;
  align-items: center;
  background: rgba(74, 111, 165, 0.1);
  padding: 8rpx 20rpx;
  border-radius: 30rpx;
}

.status-dot {
  width: 12rpx;
  height: 12rpx;
  background: $color-primary;
  border-radius: 50%;
  margin-right: 10rpx;
}

.status-badge text {
  font-size: 20rpx;
  color: $color-primary;
  font-weight: 600;
}

/* 3. 表单区域 */
.form-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 40rpx;
}

.input-card {
  background: $color-card;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  transition: box-shadow 0.3s ease;
}

.input-card:focus-within {
  box-shadow: 0 8rpx 30rpx rgba(74, 111, 165, 0.1);
}

.label-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.label-text {
  font-size: 26rpx;
  font-weight: 600;
  color: $color-text-main;
}

.label-count {
  font-size: 22rpx;
  color: $color-text-sub;
}

.input-wrapper {
  background: #FAFAFA;
  border-radius: 12rpx;
  padding: 20rpx;
  border: 1px solid transparent;
  transition: border-color 0.3s;
}

.input-wrapper:focus-within {
  border-color: rgba(74, 111, 165, 0.3);
  background: #FFF;
}

.custom-input {
  height: 60rpx;
  font-size: 30rpx;
  color: $color-text-main;
}

.custom-textarea {
  width: 100%;
  font-size: 28rpx;
  color: $color-text-main;
  line-height: 1.6;
  min-height: 160rpx;
}

.ph-style {
  color: #CFD8DC;
  font-weight: 300;
}

/* 4. 底部按钮 */
.footer-section {
  padding: 60rpx 0;
  margin-bottom: 40rpx;
}

.generate-btn {
  background: $color-primary;
  color: #FFF;
  height: 100rpx;
  border-radius: 50rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 2rpx;
  border: none;
  box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.3);
  transition: all 0.3s ease;
}

.generate-btn:active {
  transform: scale(0.98);
  box-shadow: 0 6rpx 20rpx rgba(74, 111, 165, 0.2);
}

.btn-disabled {
  background: #B0BEC5;
  box-shadow: none;
  opacity: 0.8;
}

.btn-loading-content {
  display: flex;
  align-items: center;
}

.mini-spinner {
  width: 30rpx;
  height: 30rpx;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #FFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 16rpx;
}

/* 5. 加载模态框 */
.loading-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(245, 245, 240, 0.8);
  backdrop-filter: blur(5px);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  width: 560rpx;
  background: $color-card;
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.08);
}

.spinner-ring {
  width: 100rpx;
  height: 100rpx;
  border: 6rpx solid #F0F0F0;
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
  margin-bottom: 40rpx;
}

.loading-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $color-text-main;
  margin-bottom: 16rpx;
}

.loading-desc {
  font-size: 24rpx;
  color: $color-text-sub;
  margin-bottom: 50rpx;
  height: 34rpx; /* 固定高度防止跳动 */
}

.progress-bar-bg {
  width: 100%;
  height: 8rpx;
  background: #F0F0F0;
  border-radius: 4rpx;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: $color-primary;
  border-radius: 4rpx;
  transition: width 0.3s ease;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.fade-in { animation: fadeIn 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>