<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    
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
import { useTheme } from '@/utils/useTheme';

const API_BASE = `http://101.35.132.175:5000`;
const archivedPlans = ref([]);
const { isDarkMode } = useTheme();

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
/* 1. 颜色变量 */
$color-bg: #F5F5F0; $color-card: #FFFFFF; $color-primary: #4A6FA5;
$color-accent: #FF8A65; $color-text-main: #2C3E50; $color-text-sub: #95A5A6;

/* 深色模式变量 */
$dark-bg: #121212;
$dark-card: #1E1E1E;
$dark-text-main: #E0E0E0;
$dark-text-sub: #A0A0A0;

page { background-color: $color-bg; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }

.container { min-height: 100vh; padding: 40rpx 30rpx; position: relative; transition: all 0.3s; padding-top: var(--status-bar-height); }
.container.dark { background-color: $dark-bg !important; }

/* 2. Header */
.header-section { margin-bottom: 60rpx; padding-top: 20rpx; }
.page-title { font-size: 56rpx; font-weight: 300; color: $color-text-main; letter-spacing: -1px; line-height: 1; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .page-title { color: $dark-text-main; }

.page-subtitle { font-size: 24rpx; font-weight: 500; color: $color-text-sub; letter-spacing: 1px; text-transform: uppercase; transition: color 0.3s; }
.container.dark .page-subtitle { color: $dark-text-sub; }

/* 3. Empty State */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 120rpx; opacity: 0.6; }
.empty-icon { font-size: 60rpx; margin-bottom: 24rpx; filter: grayscale(1); }
.empty-title { font-size: 32rpx; font-weight: 600; color: $color-text-main; margin-bottom: 12rpx; transition: color 0.3s; }
.container.dark .empty-title { color: $dark-text-main; }

.empty-tip { font-size: 24rpx; color: $color-text-sub; text-align: center; max-width: 60%; line-height: 1.5; transition: color 0.3s; }
.container.dark .empty-tip { color: $dark-text-sub; }

/* 4. Timeline List */
.history-list { height: calc(100vh - 240rpx); }
.timeline-container { position: relative; padding-left: 20rpx; }

/* 时间轴线 */
.timeline-line { position: absolute; left: 33rpx; top: 30rpx; bottom: 0; width: 2rpx; background: rgba(0,0,0,0.06); z-index: 0; transition: background-color 0.3s; }
.container.dark .timeline-line { background: rgba(255,255,255,0.06); }

/* 单个历史项 */
.history-item { display: flex; margin-bottom: 50rpx; position: relative; z-index: 1; }
.history-item:last-child { margin-bottom: 0; }

/* 节点 */
.timeline-node { width: 30rpx; margin-right: 30rpx; display: flex; justify-content: center; padding-top: 10rpx; }
.node-dot { width: 16rpx; height: 16rpx; background: $color-text-sub; border-radius: 50%; border: 4rpx solid $color-bg; transition: border-color 0.3s; }
.container.dark .node-dot { border-color: $dark-bg; }

/* 内容卡片 */
.content-card { 
  flex: 1; 
  background: $color-card; 
  border-radius: 16rpx; 
  padding: 30rpx; 
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03); 
  transition: transform 0.2s, background-color 0.3s; 
}
.container.dark .content-card { background-color: $dark-card; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.3); }

.content-card:active { transform: scale(0.98); }

/* 卡片内部 */
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.archive-date { font-size: 24rpx; font-weight: 700; color: $color-text-sub; letter-spacing: 0.5px; transition: color 0.3s; }
.container.dark .archive-date { color: $dark-text-sub; }

.status-badge { font-size: 18rpx; font-weight: 800; color: #FFF; background: $color-text-sub; padding: 4rpx 12rpx; border-radius: 6rpx; letter-spacing: 1px; }

.plan-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; margin-bottom: 30rpx; display: block; transition: color 0.3s; }
.container.dark .plan-title { color: $dark-text-main; }

.card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0,0,0,0.04); padding-top: 20rpx; transition: border-color 0.3s; }
.container.dark .card-footer { border-top: 1px solid rgba(255,255,255,0.04); }

.meta-info { display: flex; flex-direction: column; }
.meta-label { font-size: 18rpx; font-weight: 600; color: $color-text-sub; margin-bottom: 4rpx; transition: color 0.3s; }
.container.dark .meta-label { color: $dark-text-sub; }

.meta-value { font-size: 24rpx; font-weight: 700; color: $color-text-main; transition: color 0.3s; }
.container.dark .meta-value { color: $dark-text-main; }

.review-btn { display: flex; align-items: center; font-size: 24rpx; font-weight: 600; color: $color-primary; }
.arrow { margin-left: 8rpx; transition: transform 0.2s; }
.content-card:active .arrow { transform: translateX(6rpx); }

/* 5. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-in { animation: slideIn 0.6s ease-out backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(20rpx); } to { opacity: 1; transform: translateX(0); } }
</style>