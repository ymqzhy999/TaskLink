<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
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
import { onShow } from '@dcloudio/uni-app';
import { useTheme } from '@/utils/useTheme';

const API_BASE = `http://101.35.132.175:5000`;
const planForm = ref({ goal: '', expectation: '', days: '' });
const isGenerating = ref(false);
const { isDarkMode } = useTheme();



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
/* 1. 颜色变量 */
$color-bg: #F5F5F0; $color-card: #FFFFFF; $color-primary: #4A6FA5;
$color-accent: #FF8A65; $color-text-main: #2C3E50; $color-text-sub: #95A5A6;

/* 深色模式变量 */
$dark-bg: #121212;
$dark-card: #1E1E1E;
$dark-text-main: #E0E0E0;
$dark-text-sub: #A0A0A0;
$dark-input-bg: #2C2C2C;

page { background-color: $color-bg; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }

.container { min-height: 100vh; padding: 40rpx 30rpx; position: relative; transition: all 0.3s; }
.container.dark { background-color: $dark-bg; }

/* 2. Header */
.header-section { margin-bottom: 50rpx; display: flex; justify-content: space-between; align-items: flex-start; padding-top: 20rpx; }
.page-title { font-size: 56rpx; font-weight: 300; color: $color-text-main; letter-spacing: -1px; line-height: 1; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .page-title { color: $dark-text-main; }

.page-subtitle { font-size: 24rpx; font-weight: 500; color: $color-text-sub; letter-spacing: 1px; transition: color 0.3s; }
.container.dark .page-subtitle { color: $dark-text-sub; }

.status-badge { display: flex; align-items: center; background: rgba(76, 175, 80, 0.1); padding: 4rpx 12rpx; border-radius: 100rpx; transition: background-color 0.3s; }
.container.dark .status-badge { background: rgba(76, 175, 80, 0.2); }

.status-dot { width: 12rpx; height: 12rpx; background: #4CAF50; border-radius: 50%; margin-right: 8rpx; }
.status-badge text { font-size: 20rpx; color: #4CAF50; font-weight: 600; }

/* 3. Form Container */
.form-container { margin-bottom: 40rpx; }
.input-card { margin-bottom: 40rpx; }

.label-row { display: flex; justify-content: space-between; margin-bottom: 16rpx; }
.label-text { font-size: 28rpx; font-weight: 600; color: $color-text-main; transition: color 0.3s; }
.container.dark .label-text { color: $dark-text-main; }

.label-count { font-size: 22rpx; color: $color-text-sub; transition: color 0.3s; }
.container.dark .label-count { color: $dark-text-sub; }

.input-wrapper { background: #FFFFFF; border-radius: 16rpx; padding: 0 30rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.03); transition: background-color 0.3s, box-shadow 0.3s; }
.container.dark .input-wrapper { background: $dark-card; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.3); }

.area-wrapper { padding: 30rpx; }

.custom-input { height: 100rpx; font-size: 30rpx; color: $color-text-main; font-weight: 500; transition: color 0.3s; }
.container.dark .custom-input { color: $dark-text-main; }

.custom-textarea { width: 100%; min-height: 160rpx; font-size: 30rpx; color: $color-text-main; line-height: 1.5; transition: color 0.3s; }
.container.dark .custom-textarea { color: $dark-text-main; }

.ph-style { color: #B0BEC5; font-weight: 400; }

/* 4. Footer Btn */
.footer-section { position: fixed; bottom: 40rpx; left: 30rpx; right: 30rpx; }
.generate-btn { 
  background: $color-text-main; 
  color: #FFF; 
  height: 100rpx; 
  border-radius: 24rpx; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 32rpx; 
  font-weight: 600; 
  box-shadow: 0 10rpx 30rpx rgba(44, 62, 80, 0.3); 
  transition: all 0.3s; 
}
.container.dark .generate-btn { background: $color-primary; box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.4); }

.generate-btn:active { transform: scale(0.98); }
.btn-disabled { opacity: 0.7; pointer-events: none; }
.btn-loading-content { display: flex; align-items: center; }
.mini-spinner { width: 30rpx; height: 30rpx; border: 4rpx solid rgba(255,255,255,0.3); border-top-color: #FFF; border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 16rpx; }

/* 5. Loading Modal */
.loading-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.9); backdrop-filter: blur(5px); z-index: 999; display: flex; align-items: center; justify-content: center; transition: background-color 0.3s; }
.container.dark .loading-modal { background: rgba(0,0,0,0.8); }

.modal-card { width: 80%; background: #FFF; border-radius: 24rpx; padding: 60rpx 40rpx; display: flex; flex-direction: column; align-items: center; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.1); transition: background-color 0.3s; }
.container.dark .modal-card { background: $dark-card; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.4); }

.spinner-ring { width: 80rpx; height: 80rpx; border: 6rpx solid #F0F0F0; border-top-color: $color-primary; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 40rpx; transition: border-color 0.3s; }
.container.dark .spinner-ring { border-color: #333; border-top-color: $color-primary; }

.loading-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; margin-bottom: 16rpx; transition: color 0.3s; }
.container.dark .loading-title { color: $dark-text-main; }

.loading-desc { font-size: 24rpx; color: $color-text-sub; margin-bottom: 40rpx; text-align: center; transition: color 0.3s; }
.container.dark .loading-desc { color: $dark-text-sub; }

.progress-bar-bg { width: 100%; height: 8rpx; background: #F0F0F0; border-radius: 4rpx; overflow: hidden; transition: background-color 0.3s; }
.container.dark .progress-bar-bg { background: #333; }

.progress-bar-fill { height: 100%; background: $color-primary; border-radius: 4rpx; transition: width 0.3s ease; }

/* 6. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes spin { to { transform: rotate(360deg); } }
</style>