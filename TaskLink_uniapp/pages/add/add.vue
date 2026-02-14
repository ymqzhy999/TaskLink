<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="header-section">
      <view class="header-content">
        <text class="main-title">计划制定控制台</text>
      </view>
      <view class="status-badge">
        <view class="status-dot"></view>
        <text>SYSTEM READY</text>
      </view>
    </view>

    <view class="form-container">
      
      <view class="input-group">
        <view class="label-row">
          <text class="label-text">核心目标</text>
          <text class="label-tip">{{ planForm.goal.length }}/50</text>
        </view>
        <view class="input-wrapper focus-border">
          <input 
            class="cyber-input" 
            v-model="planForm.goal" 
            placeholder="例如：七天掌握 Python 基础" 
            placeholder-class="ph-style"
            :maxlength="50"
          />
          <view class="corner-mark"></view>
        </view>
      </view>

      <view class="input-group">
        <view class="label-row">
          <text class="label-text">最终预期</text>
        </view>
        <view class="input-wrapper area-wrapper">
          <textarea 
            class="cyber-textarea" 
            v-model="planForm.expectation" 
            placeholder="描述你希望达成的具体效果..." 
            placeholder-class="ph-style"
            :maxlength="200"
            auto-height
          />
        </view>
      </view>

      <view class="input-group">
        <view class="label-row">
          <text class="label-text">执行周期 (天)</text>
        </view>
        <view class="input-wrapper focus-border">
          <input 
            class="cyber-input" 
            type="number" 
            v-model="planForm.days" 
            placeholder="请输入天数 (例如: 7)" 
            placeholder-class="ph-style"
          />
          <view class="corner-mark"></view>
        </view>
      </view>

    </view>

    <view class="footer-section">
      <button 
        class="execute-btn" 
        :class="{ processing: isGenerating }" 
        @click="generatePlan"
        :disabled="isGenerating"
      >
        <text class="btn-text">{{ isGenerating ? 'CALCULATING...' : '生成计划' }}</text>
        <view class="btn-glare"></view>
      </button>
    </view>

    <view class="loading-modal" v-if="isGenerating">
      <view class="modal-content">
        <view class="spinner-ring"></view>
        <view class="spinner-core"></view>
        
        <text class="loading-title">ANALYZING</text>
        <text class="loading-desc">{{ loadingStepText }}</text>
        
        <view class="progress-bar">
          <view class="progress-inner" :style="{ width: progressWidth + '%' }"></view>
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
  
  progressTimer = setInterval(() => {
    if (progressWidth.value < 95) {
      progressWidth.value += (Math.random() * 5);
    }
  }, 200);

  stepTimer = setInterval(() => {
    stepIndex++;
    if (stepIndex < loadingSteps.length) {
      loadingStepText.value = loadingSteps[stepIndex];
    }
  }, 1500);
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
        setTimeout(() => {
          isGenerating.value = false;
          uni.navigateTo({ url: `/pages/plan/detail?id=${res.data.data.plan_id}` });
        }, 500);
      } else {
        isGenerating.value = false;
        uni.showToast({ title: '生成失败: ' + res.data.msg, icon: 'none' });
      }
    },
    fail: (err) => {
      stopLoadingAnim();
      isGenerating.value = false;
      uni.showToast({ title: '网络中断', icon: 'none' });
    }
  });
};

onUnmounted(() => {
  stopLoadingAnim();
});
</script>

<style>

page { background-color: #0a0a0a; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
.container { min-height: 100vh; padding: 40rpx; box-sizing: border-box; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, #0f0f13 0%, #000000 100%); z-index: -1; }
.header-section { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 60rpx; padding-top: 20rpx; }
.main-title { font-size: 40rpx; font-weight: 900; letter-spacing: 2rpx; display: block; color: #fff; }
.sub-title { font-size: 24rpx; color: #666; margin-top: 8rpx; display: block; letter-spacing: 4rpx; }
.status-badge { display: flex; align-items: center; border: 1px solid #333; padding: 6rpx 16rpx; border-radius: 100rpx; background: rgba(255,255,255,0.05); }
.status-dot { width: 12rpx; height: 12rpx; background: #00ff9d; border-radius: 50%; margin-right: 12rpx; box-shadow: 0 0 10rpx #00ff9d; }
.status-badge text { font-size: 20rpx; color: #888; font-weight: bold; }
.form-container { flex: 1; display: flex; flex-direction: column; gap: 50rpx; }
.input-group { display: flex; flex-direction: column; gap: 20rpx; }
.label-row { display: flex; justify-content: space-between; align-items: baseline; }
.label-text { font-size: 24rpx; color: #00f3ff; font-weight: bold; opacity: 0.8; letter-spacing: 1rpx; }
.label-tip { font-size: 22rpx; color: #444; }
.input-wrapper { position: relative; background: #131316; border: 1px solid #333; border-radius: 8rpx; transition: all 0.3s ease; }
.area-wrapper { min-height: 180rpx; }
.input-wrapper:focus-within { border-color: #00f3ff; box-shadow: 0 0 15rpx rgba(0, 243, 255, 0.1); background: #16161a; }
.cyber-input { height: 100rpx; padding: 0 30rpx; font-size: 32rpx; color: #fff; font-weight: 500; }
.cyber-textarea { width: 100%; padding: 30rpx; font-size: 28rpx; color: #eee; line-height: 1.6; min-height: 180rpx; box-sizing: border-box; }
.ph-style { color: #444; font-weight: normal; }
.corner-mark { position: absolute; top: -1px; right: -1px; width: 15rpx; height: 15rpx; border-top: 2px solid #00f3ff; border-right: 2px solid #00f3ff; border-radius: 0 8rpx 0 0; }
.footer-section { padding: 40rpx 0; }
.execute-btn { 
  background: linear-gradient(135deg, #00f3ff 0%, #0066ff 100%);
  color: #000; 
  height: 100rpx; border-radius: 4rpx; 
  display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; border: none;
  box-shadow: 0 0 20rpx rgba(0, 243, 255, 0.3);
}
.execute-btn.processing { background: #333; color: #888; box-shadow: none; }
.btn-text { font-size: 32rpx; font-weight: 900; letter-spacing: 2rpx; z-index: 2; }
.btn-glare { position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: rgba(255,255,255,0.2); transform: skewX(-20deg); animation: glare 3s infinite; }
@keyframes glare { 0% { left: -100%; } 20% { left: 200%; } 100% { left: 200%; } }
.execute-btn:active { transform: scale(0.98); opacity: 0.9; }
.loading-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal-content { width: 500rpx; display: flex; flex-direction: column; align-items: center; }
.spinner-ring { width: 120rpx; height: 120rpx; border: 4rpx solid rgba(0, 243, 255, 0.1); border-top-color: #00f3ff; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 40rpx; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.loading-title { font-size: 24rpx; color: #00f3ff; letter-spacing: 4rpx; font-weight: bold; margin-bottom: 10rpx; }
.loading-desc { font-size: 24rpx; color: #666; margin-bottom: 30rpx; height: 30rpx; }
.progress-bar { width: 100%; height: 4rpx; background: #222; border-radius: 2rpx; overflow: hidden; }
.progress-inner { height: 100%; background: #00f3ff; box-shadow: 0 0 10rpx #00f3ff; transition: width 0.2s linear; }
</style>