<template>
  <view class="container">
    <view class="header-section fade-in">
      <view class="header-content">
        <text class="page-title">Archives</text>
        <text class="page-subtitle">已完成的计划历史记录</text>
      </view>
    </view>

    <scroll-view scroll-y class="history-list">
      <view v-if="archivedPlans.length === 0" class="empty-state">
        <view class="empty-icon">⚪</view>
        <text class="empty-title">暂无存档记录</text>
        <text class="empty-tip">当计划的所有节点完成后，将会自动归档至此处，记录你的每一次成长。</text>
      </view>

      <view class="timeline-container">
        <view class="timeline-line" v-if="archivedPlans.length > 0"></view>
        
        <view 
          class="history-item slide-in" 
          v-for="(plan, index) in archivedPlans" 
          :key="plan.id" 
          @click="goToDetail(plan.id)"
          :style="{ animationDelay: index * 0.05 + 's' }"
        >
          <view class="timeline-node">
            <view class="node-dot"></view>
          </view>
          
          <view class="content-card">
            <view class="card-header">
              <text class="archive-date">{{ formatDate(plan.created_at) }}</text>
              <view class="status-badge">ARCHIVED</view>
            </view>
            
            <text class="plan-title">{{ plan.title }}</text>
            
            <view class="card-footer">
              <view class="meta-info">
                <text class="meta-label">DURATION:</text>
                <text class="meta-value">{{ plan.total_days }} DAYS</text>
              </view>
              <view class="review-btn">
                <text>回顾详情</text>
                <text class="arrow">→</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <view style="height: 60rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;
const archivedPlans = ref([]);

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) {
    fetchArchived(user.id);
  } else {
    uni.showToast({ title: '请先登录', icon: 'none' });
  }
});

onPullDownRefresh(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) fetchArchived(user.id);
  setTimeout(() => uni.stopPullDownRefresh(), 800);
});

const fetchArchived = (userId) => {
  uni.request({
    url: `${API_BASE}/api/plans?user_id=${userId}&status=archived`,
    success: (res) => {
      if (res.data.code === 200) {
        archivedPlans.value = res.data.data;
      }
    },
    fail: () => {
      uni.showToast({ title: '网络连接异常', icon: 'none' });
    }
  });
};

const goToDetail = (id) => {
  uni.navigateTo({ url: `/pages/plan/detail?id=${id}` });
};

const formatDate = (str) => {
  if (!str) return '';
  return str.split(' ')[0]; // 只显示 YYYY-MM-DD
}
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
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
  display: flex;
  flex-direction: column;
}

/* 2. 头部 */
.header-section {
  padding-top: var(--status-bar-height);
  margin-top: 60rpx;
  margin-bottom: 60rpx;
}

.page-title {
  font-size: 56rpx;
  font-weight: 300;
  color: $color-text-main;
  letter-spacing: -1px;
  display: block;
}

.page-subtitle {
  font-size: 24rpx;
  color: $color-text-sub;
  margin-top: 8rpx;
  letter-spacing: 1px;
}

/* 3. 历史列表 & 时间轴 */
.history-list {
  flex: 1;
  height: 0;
}

.timeline-container {
  position: relative;
  padding-left: 20rpx;
}

.timeline-line {
  position: absolute;
  left: 31rpx; /* 对齐圆点中心 */
  top: 10rpx;
  bottom: 0;
  width: 2rpx;
  background-color: $color-line;
  z-index: 0;
}

.history-item {
  position: relative;
  padding-left: 60rpx;
  margin-bottom: 50rpx;
  z-index: 1;
}

.timeline-node {
  position: absolute;
  left: 14rpx;
  top: 40rpx;
  width: 36rpx;
  height: 36rpx;
  background-color: $color-bg; /* 遮挡线条 */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.node-dot {
  width: 14rpx;
  height: 14rpx;
  border: 4rpx solid $color-primary;
  border-radius: 50%;
  background-color: #FFF;
}

/* 内容卡片 */
.content-card {
  background: $color-card;
  border-radius: 20rpx;
  padding: 30rpx 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
  transition: all 0.3s ease;
}

.content-card:active {
  transform: scale(0.98);
  box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.archive-date {
  font-size: 24rpx;
  color: $color-text-sub;
  font-weight: 600;
  font-family: monospace;
}

.status-badge {
  font-size: 18rpx;
  color: $color-primary;
  background: rgba(74, 111, 165, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.plan-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $color-text-main;
  margin-bottom: 30rpx;
  display: block;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 24rpx;
  border-top: 1px solid #F5F5F5;
}

.meta-info {
  display: flex;
  align-items: center;
}

.meta-label {
  font-size: 18rpx;
  color: $color-text-sub;
  font-weight: 600;
  margin-right: 8rpx;
}

.meta-value {
  font-size: 22rpx;
  color: $color-text-main;
  font-weight: 700;
}

.review-btn {
  display: flex;
  align-items: center;
}

.review-btn text {
  font-size: 22rpx;
  color: $color-primary;
  font-weight: 600;
}

.review-btn .arrow {
  margin-left: 6rpx;
  font-size: 28rpx;
}

/* 4. 空状态 */
.empty-state {
  margin-top: 200rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 60rpx;
  text-align: center;
}

.empty-icon {
  font-size: 100rpx;
  color: $color-line;
  margin-bottom: 40rpx;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $color-text-main;
  margin-bottom: 16rpx;
}

.empty-tip {
  font-size: 24rpx;
  color: $color-text-sub;
  line-height: 1.6;
}

/* 5. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-in { animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { 
  from { opacity: 0; transform: translateY(30rpx); } 
  to { opacity: 1; transform: translateY(0); } 
}
</style>