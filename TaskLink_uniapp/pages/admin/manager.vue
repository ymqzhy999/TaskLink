<template>
  <view class="container">
    <view class="header-section">
      <view class="header-content">
        <text class="page-title">User Management</text>
        <text class="page-subtitle">系统用户权限控制台</text>
      </view>
      <view class="admin-badge">
        <text>ADMIN</text>
      </view>
    </view>

    <view class="stats-row fade-in">
      <view class="stat-card">
        <text class="stat-num">{{ users.length }}</text>
        <text class="stat-label">Total Users</text>
      </view>
      <view class="stat-card">
        <text class="stat-num highlight">{{ adminCount }}</text>
        <text class="stat-label">Admins</text>
      </view>
    </view>

    <scroll-view scroll-y class="user-list">
      <view 
        v-for="(user, index) in users" 
        :key="user.id" 
        class="user-card slide-up" 
        :class="{ 'banned': user.status === 0 }"
        :style="{ animationDelay: index * 0.05 + 's' }"
      >
        <image :src="formatAvatar(user.avatar)" class="avatar" mode="aspectFill"></image>
        
        <view class="info-column">
          <view class="user-header">
            <text class="username">{{ user.username }}</text>
            <view v-if="user.role === 1" class="role-tag admin-tag">ADMIN</view>
            <view v-if="user.status === 0" class="role-tag ban-tag">BANNED</view>
          </view>
          <text class="user-meta">UID: #{{ String(user.id).padStart(4, '0') }}</text>
        </view>

        <view class="action-btn" :class="user.status === 1 ? 'btn-disable' : 'btn-enable'" @click="toggleStatus(user)">
          <text>{{ user.status === 1 ? '禁用' : '启用' }}</text>
        </view>
      </view>
      
      <view style="height: 40rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const SERVICE_HOST = '101.35.132.175';
const API_BASE = `http://${SERVICE_HOST}:5000`;

const users = ref([]);
const myInfo = ref({});

// 计算管理员数量
const adminCount = computed(() => users.value.filter(u => u.role === 1).length);

onShow(() => {
  myInfo.value = uni.getStorageSync('userInfo') || {};
  fetchUsers();
});

const formatAvatar = (path) => {
  if (!path) return '/static/logo.png';
  return path.startsWith('http') ? path : `${API_BASE}${path}`;
};

const fetchUsers = () => {
  uni.showLoading({ title: 'Loading...' });
  uni.request({
    url: `${API_BASE}/api/admin/users`,
    method: 'GET',
    data: { operator_id: myInfo.value.id },
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        users.value = res.data.data;
      } else {
        uni.showToast({ title: '权限不足或数据错误', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    }
  });
};

const toggleStatus = (user) => {
  if (user.id === myInfo.value.id) {
    uni.showToast({ title: '无法禁用自己', icon: 'none' });
    return;
  }

  const newStatus = user.status === 1 ? 0 : 1;
  const actionText = newStatus === 0 ? '禁用' : '启用';

  uni.showModal({
    title: '确认操作',
    content: `确定要 [${actionText}] 用户 "${user.username}" 吗？`,
    confirmColor: newStatus === 0 ? '#EF5350' : '#4A6FA5',
    success: (res) => {
      if (res.confirm) {
        uni.request({
          url: `${API_BASE}/api/admin/user/status`,
          method: 'POST',
          data: {
            operator_id: myInfo.value.id,
            user_id: user.id,
            status: newStatus
          },
          success: (resp) => {
            if (resp.data.code === 200) {
              user.status = newStatus;
              uni.showToast({ title: '操作成功' });
            } else {
              uni.showToast({ title: resp.data.msg, icon: 'none' });
            }
          }
        });
      }
    }
  });
};
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 2. 头部 */
.header-section {
  padding: 100rpx 40rpx 40rpx;
  background: $color-bg;
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

.admin-badge {
  background: $color-text-main;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
}

.admin-badge text {
  color: #FFF;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 1px;
}

/* 3. 统计行 */
.stats-row {
  display: flex;
  padding: 0 40rpx;
  gap: 30rpx;
  margin-bottom: 40rpx;
}

.stat-card {
  flex: 1;
  background: $color-card;
  padding: 30rpx;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 48rpx;
  font-weight: 700;
  color: $color-text-main;
  line-height: 1;
  margin-bottom: 8rpx;
}

.stat-num.highlight { color: $color-primary; }

.stat-label {
  font-size: 22rpx;
  color: $color-text-sub;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 4. 用户列表 */
.user-list {
  flex: 1;
  height: 0;
  padding: 0 40rpx;
  box-sizing: border-box;
}

.user-card {
  background: $color-card;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.02);
  transition: all 0.3s ease;
}

.user-card.banned {
  opacity: 0.6;
  background: #F5F5F5;
}

.avatar {
  width: 90rpx;
  height: 90rpx;
  border-radius: 50%;
  background: #E0E0E0;
  margin-right: 24rpx;
}

.info-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-header {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.username {
  font-size: 30rpx;
  font-weight: 600;
  color: $color-text-main;
  margin-right: 16rpx;
}

.role-tag {
  font-size: 18rpx;
  font-weight: 700;
  padding: 4rpx 10rpx;
  border-radius: 6rpx;
}

.admin-tag {
  background: rgba(74, 111, 165, 0.1);
  color: $color-primary;
}

.ban-tag {
  background: rgba(239, 83, 80, 0.1);
  color: #EF5350;
}

.user-meta {
  font-size: 22rpx;
  color: $color-text-sub;
  font-family: monospace;
}

/* 按钮 */
.action-btn {
  padding: 12rpx 24rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.btn-disable {
  background: rgba(239, 83, 80, 0.1);
  color: #EF5350;
}

.btn-enable {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

/* 动画 */
.fade-in { animation: fadeIn 0.6s ease-out; }
.slide-up { animation: slideUp 0.5s ease-out backwards; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>