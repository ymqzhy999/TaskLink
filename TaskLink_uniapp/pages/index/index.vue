<template>
  <view class="container">
    <view class="header fade-in">
      <view class="header-left">
        <text class="app-name">Task<text class="app-name-highlight">Link</text></text>
        <text class="page-title">计划中心</text>
      </view>
      <view class="header-right">
        <view class="date-badge">
          <text class="date-text">TODAY</text>
        </view>
      </view>
    </view>

    <view class="dashboard fade-in">
      <view class="stat-card primary-card">
        <text class="stat-label">ACTIVE</text>
        <view class="stat-content">
          <text class="stat-num">{{ activePlans.length }}</text>
          <text class="stat-unit">个计划</text>
        </view>
        <view class="stat-icon-bg"></view>
      </view>
      
      <view class="stat-card accent-card">
        <text class="stat-label">TOTAL PROGRESS</text>
        <view class="stat-content">
          <text class="stat-num">{{ totalProgress }}</text>
          <text class="stat-unit">%</text>
        </view>
        <view class="stat-ring" :style="{ '--p': totalProgress }"></view>
      </view>
    </view>

    <view class="section-header fade-in">
      <text class="section-title">我的日程</text>
      <text class="section-subtitle">MY SCHEDULE</text>
    </view>

    <scroll-view scroll-y class="plan-list-scroll">
      <view v-if="activePlans.length === 0" class="empty-state">
        <text class="empty-icon">⚪</text>
        <text class="empty-text">No active plans.</text>
        <text class="empty-sub">保持专注，从创建一个计划开始。</text>
      </view>

      <view 
        v-for="(plan, index) in activePlans" 
        :key="plan.id" 
        class="plan-card slide-up"
        :style="{ animationDelay: index * 0.05 + 's' }"
        @click="goToDetail(plan.id)"
        @longpress="onLongPressPlan(plan)"
      >
        <view class="card-main">
          <view class="card-header">
            <text class="plan-title">{{ plan.title }}</text>
            <view class="plan-days-tag">
              <text>{{ plan.total_days }} DAYS</text>
            </view>
          </view>
          
          <text class="plan-desc">{{ plan.goal }}</text>
          
          <view class="progress-container">
            <view class="progress-info">
              <text class="progress-label">Completeness</text>
              <text class="progress-val">{{ plan.progress }}%</text>
            </view>
            <view class="progress-track">
              <view class="progress-bar" :style="{ width: plan.progress + '%' }"></view>
            </view>
          </view>
        </view>
        
        <view class="card-status-bar"></view>
      </view>
      
      <view style="height: 100rpx;"></view>
    </scroll-view>

  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
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

// 交互文案微调：更符合极简风格
const onLongPressPlan = (plan) => {
  uni.vibrateShort();
  uni.showModal({
    title: '确认操作',
    content: `确认结束并删除计划“${plan.title}”吗？此操作不可恢复。`,
    confirmText: '删除',
    confirmColor: '#FF8A65', // 珊瑚橙
    cancelText: '取消',
    cancelColor: '#95A5A6',
    success: (res) => {
      if (res.confirm) {
        deletePlan(plan.id);
      }
    }
  });
};

const deletePlan = (id) => {
  uni.showLoading({ title: 'Processing...' });
  
  uni.request({
    url: `${API_BASE}/api/plan/${id}`,
    method: 'DELETE',
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        uni.showToast({ title: 'Deleted', icon: 'success' });
        fetchPlans();
      } else {
        uni.showToast({ title: 'Error', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: 'Network Error', icon: 'none' });
    }
  });
};
</script>

<style lang="scss" scoped>
/* =================================================================
   视觉样式重构 (莫兰迪极简高级感)
   ================================================================= */

/* 1. 色彩变量 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 辅助文字 */
$color-line: #E0E0E0;

page { 
  background-color: $color-bg; 
  color: $color-text-main; 
  font-family: 'Inter', -apple-system, Helvetica, sans-serif; 
}

.container {
  min-height: 100vh;
  padding: 40rpx 40rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* 2. 头部 Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-top: 40rpx;
  margin-bottom: 60rpx;
}

.app-name {
  font-size: 24rpx;
  font-weight: 900;
  color: $color-text-main;
  letter-spacing: 1px;
  display: block;
  margin-bottom: 8rpx;
}
.app-name-highlight { color: $color-accent; }

.page-title {
  font-size: 56rpx;
  font-weight: 300; /* 细字体显得高级 */
  color: $color-text-main;
  letter-spacing: -1px;
  line-height: 1;
}

.date-badge {
  background: rgba(74, 111, 165, 0.1);
  padding: 8rpx 20rpx;
  border-radius: 100rpx;
}
.date-text {
  font-size: 20rpx;
  color: $color-primary;
  font-weight: 700;
  letter-spacing: 1px;
}

/* 3. 数据仪表盘 Dashboard */
.dashboard {
  display: flex;
  justify-content: space-between;
  margin-bottom: 60rpx;
}

.stat-card {
  width: 48%;
  background: $color-card;
  border-radius: 16rpx;
  padding: 30rpx;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20rpx 40rpx rgba(74, 111, 165, 0.06);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 200rpx;
  transition: transform 0.3s ease;
}

.stat-card:active { transform: scale(0.98); }

.stat-label {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  z-index: 2;
}

.stat-content {
  z-index: 2;
  margin-top: 20rpx;
}

.stat-num {
  font-size: 64rpx;
  font-weight: 700;
  line-height: 1;
  color: $color-text-main;
}

.stat-unit {
  font-size: 22rpx;
  color: $color-text-sub;
  margin-left: 8rpx;
}

/* 差异化设计 */
.primary-card .stat-num { color: $color-primary; }
.accent-card .stat-num { color: $color-accent; }

/* 装饰元素 */
.stat-icon-bg {
  position: absolute;
  right: -20rpx;
  bottom: -20rpx;
  width: 100rpx;
  height: 100rpx;
  background: $color-primary;
  opacity: 0.1;
  border-radius: 50%;
}

.stat-ring {
  position: absolute;
  right: -30rpx;
  bottom: -30rpx;
  width: 120rpx;
  height: 120rpx;
  border: 8rpx solid $color-accent;
  opacity: 0.15;
  border-radius: 50%;
}

/* 4. 列表标题 */
.section-header {
  display: flex;
  align-items: baseline;
  margin-bottom: 30rpx;
  padding-left: 8rpx;
}
.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $color-text-main;
  margin-right: 16rpx;
}
.section-subtitle {
  font-size: 20rpx;
  color: $color-text-sub;
  letter-spacing: 2px;
  font-weight: 500;
}

/* 5. 计划列表 */
.plan-list-scroll {
  flex: 1;
  height: 0; /* Flex布局下滚动必须 */
}

.plan-card {
  background: $color-card;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(44, 62, 80, 0.04);
  position: relative;
  overflow: hidden;
  display: flex;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.plan-card:active {
  transform: scale(0.98);
  box-shadow: 0 5rpx 15rpx rgba(44, 62, 80, 0.02);
}

.card-status-bar {
  width: 8rpx;
  background-color: $color-primary;
  opacity: 0.8;
}

.card-main {
  flex: 1;
  padding: 30rpx 40rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20rpx;
}

.plan-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $color-text-main;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-days-tag {
  background: #F0F4F8;
  padding: 6rpx 12rpx;
  border-radius: 4rpx;
}
.plan-days-tag text {
  font-size: 18rpx;
  color: $color-text-sub;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.plan-desc {
  font-size: 24rpx;
  color: $color-text-sub;
  line-height: 1.6;
  margin-bottom: 40rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 76rpx; /* 保持卡片高度一致 */
}

/* 极简进度条 */
.progress-container {
  display: flex;
  flex-direction: column;
}
.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10rpx;
}
.progress-label {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 500;
}
.progress-val {
  font-size: 24rpx;
  color: $color-primary;
  font-weight: 700;
}

.progress-track {
  width: 100%;
  height: 4rpx; /* 极细 */
  background: #EFF1F3;
  border-radius: 4rpx;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background-color: $color-primary;
  border-radius: 4rpx;
  transition: width 0.6s ease;
}

/* 6. 空状态 */
.empty-state {
  margin-top: 100rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.6;
}
.empty-icon { font-size: 60rpx; margin-bottom: 20rpx; filter: grayscale(1); }
.empty-text { font-size: 28rpx; color: $color-text-main; font-weight: 600; letter-spacing: 1px; margin-bottom: 8rpx; }
.empty-sub { font-size: 22rpx; color: $color-text-sub; }

/* 7. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(40rpx); } to { opacity: 1; transform: translateY(0); } }
</style>