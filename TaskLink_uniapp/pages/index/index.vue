<template>
  <view class="container light-theme">
    <view class="header fade-in">
      <view class="greeting-box">
        <text class="title">计划中心 ✨</text>
        <text class="subtitle">今天也是充满元气的一天！</text>
      </view>
      <view class="avatar-placeholder">🌿</view>
    </view>

    <view class="stats-row fade-in">
      <view class="stat-card">
        <view class="stat-icon-wrapper mint-bg">
          <text class="stat-icon">🌱</text>
        </view>
        <view class="stat-info">
          <text class="stat-num">{{ activePlans.length }}</text>
          <text class="stat-label">进行中计划</text>
        </view>
      </view>
      
      <view class="stat-card">
        <view class="stat-icon-wrapper blue-bg">
          <text class="stat-icon">☁️</text>
        </view>
        <view class="stat-info">
          <text class="stat-num">{{ totalProgress }}%</text>
          <text class="stat-label">总体完成度</text>
        </view>
      </view>
    </view>

    <view class="section-title fade-in">我的日程安排</view>

    <scroll-view scroll-y class="plan-list-scroll">
      <view v-if="activePlans.length === 0" class="empty-state">
        <text class="empty-emoji">💤</text>
        <text class="empty-title">日程空空如也</text>
        <text class="empty-tip">快去种下一棵新的学习计划树吧~</text>
      </view>

      <view 
        v-for="(plan, index) in activePlans" 
        :key="plan.id" 
        class="plan-card slide-up"
        :style="{ animationDelay: index * 0.1 + 's' }"
        @click="goToDetail(plan.id)"
        @longpress="onLongPressPlan(plan)"
      >
        <view class="card-top">
          <text class="plan-title">{{ plan.title }}</text>
          <view class="plan-tag">{{ plan.total_days }} 天</view>
        </view>
        
        <text class="plan-goal">{{ plan.goal }}</text>
        
        <view class="progress-section">
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: plan.progress + '%' }"></view>
          </view>
          <text class="progress-val">{{ plan.progress }}%</text>
        </view>
      </view>
      
      <view style="height: 60px;"></view>
    </scroll-view>

  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';

const API_BASE = `http://101.35.132.175:5000`;
const activePlans = ref([]);

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (!user) {
    uni.reLaunch({ url: '/pages/login/login' });
    return;
  }
  fetchPlans();
});

onPullDownRefresh(() => {
  fetchPlans();
  setTimeout(() => uni.stopPullDownRefresh(), 800);
});

const fetchPlans = () => {
  const user = uni.getStorageSync('userInfo');
  uni.request({
    url: `${API_BASE}/api/plans?user_id=${user.id}&status=active`,
    success: (res) => {
      if (res.data.code === 200) {
        activePlans.value = res.data.data;
      }
    }
  });
};

const totalProgress = computed(() => {
  if (activePlans.value.length === 0) return 0;
  const sum = activePlans.value.reduce((acc, cur) => acc + (cur.progress || 0), 0);
  return Math.floor(sum / activePlans.value.length);
});

const goToDetail = (id) => {
  uni.navigateTo({ url: `/pages/plan/detail?id=${id}` });
};

// 交互文案也变得温柔了
const onLongPressPlan = (plan) => {
  uni.vibrateShort();
  uni.showModal({
    title: '温馨提示',
    content: `要删除【${plan.title}】这个计划吗？\n删除了就找不回来了哦~`,
    confirmText: '删掉啦',
    confirmColor: '#FF8A8A', // 柔和的西瓜红
    cancelText: '再想想',
    cancelColor: '#8CA19A',
    success: (res) => {
      if (res.confirm) {
        deletePlan(plan.id);
      }
    }
  });
};

const deletePlan = (id) => {
  uni.showLoading({ title: '清理中...' });
  
  uni.request({
    url: `${API_BASE}/api/plan/${id}`,
    method: 'DELETE',
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        uni.showToast({ title: '计划已清理', icon: 'success' });
        fetchPlans();
      } else {
        uni.showToast({ title: '出现了一点小问题', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: '网络好像断开啦', icon: 'none' });
    }
  });
};
</script>

<style>
/* 调色板参考：
  背景色：#F7F9F8 (极浅的奶绿白)
  文字主色：#3A4B45 (深墨绿，代替纯黑，更柔和)
  文字次色：#8CA19A (灰绿色)
  薄荷绿主色：#78D8C1
  浅蓝辅色：#A3D5F5
*/

page { 
  background-color: #F7F9F8; 
  color: #3A4B45; 
  /* 尽量使用系统默认的无衬线黑体，或者圆体 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
}

.container { padding: 40rpx 30rpx; min-height: 100vh; box-sizing: border-box; }

/* 头部样式 */
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 50rpx; margin-top: 20rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #3A4B45; display: block; margin-bottom: 10rpx; }
.subtitle { font-size: 24rpx; color: #8CA19A; }
.avatar-placeholder { width: 90rpx; height: 90rpx; background: #FFF; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 40rpx; box-shadow: 0 8rpx 20rpx rgba(120, 216, 193, 0.2); }

/* 统计卡片区 */
.stats-row { display: flex; gap: 30rpx; margin-bottom: 50rpx; }
.stat-card { flex: 1; background: #FFF; border-radius: 30rpx; padding: 30rpx; display: flex; align-items: center; gap: 20rpx; box-shadow: 0 10rpx 30rpx rgba(140, 161, 154, 0.08); }
.stat-icon-wrapper { width: 70rpx; height: 70rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; }
.mint-bg { background: rgba(120, 216, 193, 0.15); }
.blue-bg { background: rgba(163, 213, 245, 0.15); }
.stat-icon { font-size: 32rpx; }
.stat-info { display: flex; flex-direction: column; }
.stat-num { font-size: 36rpx; font-weight: 800; color: #3A4B45; }
.stat-label { font-size: 20rpx; color: #8CA19A; margin-top: 4rpx; }

.section-title { font-size: 32rpx; font-weight: bold; color: #3A4B45; margin-bottom: 30rpx; position: relative; padding-left: 20rpx; }
.section-title::before { content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 8rpx; height: 28rpx; background: #78D8C1; border-radius: 10rpx; }

/* 计划卡片 */
.plan-card { 
  background: #FFF; 
  border-radius: 30rpx; 
  padding: 30rpx; 
  margin-bottom: 30rpx; 
  box-shadow: 0 10rpx 40rpx rgba(140, 161, 154, 0.06); 
  transition: all 0.2s ease;
}
.plan-card:active { transform: scale(0.98); box-shadow: 0 5rpx 15rpx rgba(140, 161, 154, 0.04); }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.plan-title { font-size: 32rpx; font-weight: bold; color: #3A4B45; }
.plan-tag { font-size: 20rpx; color: #78D8C1; background: rgba(120, 216, 193, 0.1); padding: 6rpx 16rpx; border-radius: 20rpx; font-weight: bold; }

.plan-goal { font-size: 26rpx; color: #8CA19A; line-height: 1.5; margin-bottom: 30rpx; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* 进度条 */
.progress-section { display: flex; align-items: center; gap: 20rpx; }
.progress-bar { flex: 1; height: 16rpx; background: #F0F4F2; border-radius: 20rpx; overflow: hidden; }
.progress-fill { 
  height: 100%; 
  background: linear-gradient(90deg, #A3D5F5, #78D8C1); /* 浅蓝渐变到薄荷绿 */
  border-radius: 20rpx;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); /* Q弹的动画效果 */
}
.progress-val { font-size: 24rpx; color: #78D8C1; font-weight: bold; width: 60rpx; text-align: right; }

/* 空状态 */
.empty-state { text-align: center; margin-top: 100rpx; display: flex; flex-direction: column; align-items: center; }
.empty-emoji { font-size: 80rpx; margin-bottom: 20rpx; opacity: 0.8; }
.empty-title { font-size: 32rpx; font-weight: bold; color: #3A4B45; margin-bottom: 10rpx; }
.empty-tip { font-size: 24rpx; color: #8CA19A; }

/* 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(30rpx); } to { opacity: 1; transform: translateY(0); } }
</style>