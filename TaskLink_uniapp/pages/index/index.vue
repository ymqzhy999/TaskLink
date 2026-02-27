<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
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

    <!-- 悬浮宠物组件 -->
    <PetCanvas 
      :pet-data="petData" 
      :style-config="styleConfig" 
      :position="petPosition"
      :custom-image="customPetImage"
      @feed="handleFeedPet"
      @positionChange="onPetPositionChange"
    />

  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';
import { useTheme } from '@/utils/useTheme';
import PetCanvas from '@/components/PetCanvas.vue';


const API_BASE = `http://101.35.132.175:5000`;
const activePlans = ref([]);
const { isDarkMode } = useTheme();

// 宠物相关数据
const petData = ref(null);
const styleConfig = ref(null);
const petPosition = ref({ x: 20, y: 120 });
const customPetImage = ref('');

// 获取宠物状态
const fetchPetState = () => {
  const user = uni.getStorageSync('userInfo');
  if (!user) return;
  
  uni.request({
    url: `${API_BASE}/api/pet/state?user_id=${user.id}`,
    success: (res) => {
      if (res.data.code === 200 && res.data.data) {
        petData.value = res.data.data.pet;
        styleConfig.value = res.data.data.style;
        
        // 设置位置
        if (res.data.data.pet) {
          petPosition.value = {
            x: res.data.data.pet.pos_x || 20,
            y: res.data.data.pet.pos_y || 120
          };
          
          // 优先使用后端保存的自定义图片
          if (res.data.data.pet.custom_image) {
            customPetImage.value = res.data.data.pet.custom_image;
          } else {
            // 降级：使用本地缓存
            const localImage = uni.getStorageSync('customPetImage');
            if (localImage) {
              customPetImage.value = localImage;
            }
          }
        }
      }
    }
  });
};

// 宠物位置变化处理
const onPetPositionChange = (pos) => {
  petPosition.value = pos;
  
  const user = uni.getStorageSync('userInfo');
  if (!user || !petData.value) return;
  
  // 保存位置到后端
  uni.request({
    url: `${API_BASE}/api/pet/position`,
    method: 'POST',
    header: { 'Content-Type': 'application/json' },
    data: { user_id: user.id, pos_x: pos.x, pos_y: pos.y },
    fail: () => {}
  });
};

// 喂食宠物
const handleFeedPet = () => {
  const user = uni.getStorageSync('userInfo');
  if (!user) return;
  
  if (!petData.value || !petData.value.feed_points || petData.value.feed_points <= 0) {
    uni.showToast({ title: '没有食物啦，快去背单词~', icon: 'none', duration: 2000 });
    return;
  }
  
  uni.request({
    url: `${API_BASE}/api/pet/feed`,
    method: 'POST',
    header: { 'Content-Type': 'application/json' },
    data: { user_id: user.id, count: 1 },
    success: (res) => {
      if (res.data.code === 200) {
        fetchPetState(); // 刷新宠物状态
        uni.showToast({ title: '喂食成功 +1 经验', icon: 'success', duration: 1500 });
      } else {
        uni.showToast({ title: res.data.msg || '喂食失败', icon: 'none', duration: 1500 });
      }
    },
    fail: () => {
      uni.showToast({ title: '网络错误', icon: 'none', duration: 1500 });
    }
  });
};

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (!user) {
    uni.reLaunch({ url: '/pages/login/login' });
    return;
  }
  fetchPlans();
  fetchPetState(); // 获取宠物状态
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
   视觉样式重构 (莫兰迪极简高级感) - Dark Mode Supported
   ================================================================= */

/* 1. 色彩变量 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 辅助文字 */
$color-line: #E0E0E0;

/* 深色模式变量 */
$dark-bg: #121212;
$dark-card: #1E1E1E;
$dark-text-main: #E0E0E0;
$dark-text-sub: #A0A0A0;

page { 
  background-color: $color-bg; 
  color: $color-text-main; 
  font-family: 'Inter', -apple-system, Helvetica, sans-serif; 
  transition: background-color 0.3s;
}

.container {
  min-height: 100vh;
  padding: 40rpx 40rpx;
  padding-top: calc(var(--status-bar-height) + 40rpx);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}
.container.dark { background-color: $dark-bg !important; }

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
  transition: color 0.3s;
}
.container.dark .app-name { color: $dark-text-main; }
.app-name-highlight { color: $color-accent; }

.page-title {
  font-size: 56rpx;
  font-weight: 300;
  color: $color-text-main;
  letter-spacing: -1px;
  line-height: 1;
  transition: color 0.3s;
}
.container.dark .page-title { color: $dark-text-sub; }

.date-badge {
  background: rgba(74, 111, 165, 0.1);
  padding: 8rpx 20rpx;
  border-radius: 100rpx;
  transition: background-color 0.3s;
}
.container.dark .date-badge { background: #333; }
.date-text {
  font-size: 20rpx;
  color: $color-primary;
  font-weight: 700;
  letter-spacing: 1px;
  transition: color 0.3s;
}
.container.dark .date-text { color: $dark-text-main; }

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
  transition: transform 0.3s ease, background-color 0.3s;
}
.container.dark .stat-card { background-color: $dark-card; box-shadow: 0 20rpx 40rpx rgba(0,0,0,0.3); }

.stat-card:active { transform: scale(0.98); }

.stat-label {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  z-index: 2;
  transition: color 0.3s;
}
.container.dark .stat-label { color: $dark-text-sub; }

.stat-content {
  z-index: 2;
  margin-top: 20rpx;
}

.stat-num {
  font-size: 64rpx;
  font-weight: 700;
  line-height: 1;
  color: $color-text-main;
  transition: color 0.3s;
}
.container.dark .stat-num { color: $dark-text-main; }

.stat-unit {
  font-size: 22rpx;
  color: $color-text-sub;
  margin-left: 8rpx;
  transition: color 0.3s;
}
.container.dark .stat-unit { color: $dark-text-sub; }

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
  transition: color 0.3s;
}
.container.dark .section-title { color: $dark-text-main; }

.section-subtitle {
  font-size: 20rpx;
  color: $color-text-sub;
  letter-spacing: 2px;
  font-weight: 500;
  transition: color 0.3s;
}
.container.dark .section-subtitle { color: $dark-text-sub; }

/* 5. 计划列表 */
.plan-list-scroll {
  flex: 1;
  height: 0;
}

.plan-card {
  background: $color-card;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 10rpx 30rpx rgba(44, 62, 80, 0.04);
  position: relative;
  overflow: hidden;
  display: flex;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), background-color 0.3s;
}
.container.dark .plan-card { background-color: $dark-card; box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.3); }

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
  transition: color 0.3s;
}
.container.dark .plan-title { color: $dark-text-main; }

.plan-days-tag {
  background: #F0F4F8;
  padding: 6rpx 12rpx;
  border-radius: 4rpx;
  transition: background-color 0.3s;
}
.container.dark .plan-days-tag { background: #333; }
.plan-days-tag text {
  font-size: 18rpx;
  color: $color-text-sub;
  font-weight: 700;
  letter-spacing: 0.5px;
  transition: color 0.3s;
}
.container.dark .plan-days-tag text { color: $dark-text-sub; }

.plan-desc {
  font-size: 24rpx;
  color: $color-text-sub;
  line-height: 1.6;
  margin-bottom: 40rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 76rpx;
  transition: color 0.3s;
}
.container.dark .plan-desc { color: $dark-text-sub; }

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
  transition: color 0.3s;
}
.container.dark .progress-label { color: $dark-text-sub; }

.progress-val {
  font-size: 24rpx;
  color: $color-primary;
  font-weight: 700;
  transition: color 0.3s;
}
.container.dark .progress-val { color: $dark-text-main; }

.progress-track {
  width: 100%;
  height: 4rpx; 
  background: #EFF1F3;
  border-radius: 4rpx;
  overflow: hidden;
  transition: background-color 0.3s;
}
.container.dark .progress-track { background: #333; }

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
.empty-text { 
  font-size: 28rpx; 
  color: $color-text-main; 
  font-weight: 600; 
  letter-spacing: 1px; 
  margin-bottom: 8rpx;
  transition: color 0.3s;
}
.container.dark .empty-text { color: $dark-text-main; }

.empty-sub { 
  font-size: 22rpx; 
  color: $color-text-sub;
  transition: color 0.3s;
}
.container.dark .empty-sub { color: $dark-text-sub; }

/* 悬浮宠物区域 */
.floating-pet {
  position: fixed;
  right: 20rpx;
  bottom: 120rpx;
  z-index: 999;
  touch-action: none;
}

/* 7. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(40rpx); } to { opacity: 1; transform: translateY(0); } }
</style>