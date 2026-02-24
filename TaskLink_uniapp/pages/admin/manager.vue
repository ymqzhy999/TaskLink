<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
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
import { useTheme } from '@/utils/useTheme';

const SERVICE_HOST = '101.35.132.175';
const API_BASE = `http://${SERVICE_HOST}:5000`;

const users = ref([]);
const myInfo = ref({});
const { isDarkMode } = useTheme();

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
.header-section { margin-bottom: 50rpx; display: flex; justify-content: space-between; align-items: flex-start; padding-top: 20rpx; }
.page-title { font-size: 56rpx; font-weight: 300; color: $color-text-main; letter-spacing: -1px; line-height: 1; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .page-title { color: $dark-text-main; }

.page-subtitle { font-size: 24rpx; font-weight: 500; color: $color-text-sub; letter-spacing: 1px; transition: color 0.3s; }
.container.dark .page-subtitle { color: $dark-text-sub; }

.admin-badge { background: $color-primary; color: #FFF; padding: 6rpx 16rpx; border-radius: 8rpx; font-size: 20rpx; font-weight: 700; letter-spacing: 1px; height: fit-content; }

/* 3. Stats */
.stats-row { display: flex; gap: 24rpx; margin-bottom: 40rpx; }
.stat-card { 
  flex: 1; 
  background: $color-card; 
  border-radius: 16rpx; 
  padding: 30rpx; 
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03); 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  transition: background-color 0.3s, box-shadow 0.3s;
}
.container.dark .stat-card { background: $dark-card; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.3); }

.stat-num { font-size: 48rpx; font-weight: 800; color: $color-text-main; line-height: 1; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .stat-num { color: $dark-text-main; }
.highlight { color: $color-primary; }

.stat-label { font-size: 22rpx; color: $color-text-sub; font-weight: 500; transition: color 0.3s; }
.container.dark .stat-label { color: $dark-text-sub; }

/* 4. List */
.user-list { height: calc(100vh - 400rpx); }

.user-card { 
  background: $color-card; 
  border-radius: 20rpx; 
  padding: 30rpx; 
  margin-bottom: 30rpx; 
  display: flex; 
  align-items: center; 
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.02); 
  transition: all 0.3s; 
}
.container.dark .user-card { background: $dark-card; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.3); }

.user-card.banned { opacity: 0.6; filter: grayscale(0.8); }

.avatar { width: 90rpx; height: 90rpx; border-radius: 50%; background: #E0E0E0; margin-right: 24rpx; }

.info-column { flex: 1; display: flex; flex-direction: column; }
.user-header { display: flex; align-items: center; margin-bottom: 8rpx; }
.username { font-size: 30rpx; font-weight: 700; color: $color-text-main; margin-right: 12rpx; transition: color 0.3s; }
.container.dark .username { color: $dark-text-main; }

.role-tag { font-size: 18rpx; font-weight: 800; padding: 4rpx 10rpx; border-radius: 6rpx; letter-spacing: 0.5px; }
.admin-tag { background: rgba(74, 111, 165, 0.1); color: $color-primary; }
.ban-tag { background: #FFEBEE; color: #FF5252; margin-left: 8rpx; }

.user-meta { font-size: 22rpx; color: $color-text-sub; font-family: monospace; transition: color 0.3s; }
.container.dark .user-meta { color: $dark-text-sub; }

/* Action Btn */
.action-btn { 
  padding: 12rpx 30rpx; 
  border-radius: 30rpx; 
  font-size: 24rpx; 
  font-weight: 600; 
  transition: all 0.2s; 
}
.btn-disable { background: #FFEBEE; color: #FF5252; }
.btn-enable { background: #E8F5E9; color: #4CAF50; }

/* 5. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s ease-out backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>