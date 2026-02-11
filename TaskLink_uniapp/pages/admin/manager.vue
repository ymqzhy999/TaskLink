<template>
  <view class="container">
    <view class="cyber-bg"></view>
    
    <view class="header">
      <text class="title">USER DATABASE</text>
      <text class="subtitle">ACCESS LEVEL: ADMINISTRATOR</text>
    </view>

    <scroll-view scroll-y class="user-list">
      <view v-for="(user, index) in users" :key="user.id" class="user-card" :class="{ 'banned': user.status === 0 }">
        <image :src="formatAvatar(user.avatar)" class="avatar" mode="aspectFill"></image>
        
        <view class="info">
          <view class="top-row">
            <text class="username">{{ user.username }}</text>
            <text v-if="user.role === 1" class="tag admin-tag">ADMIN</text>
            <text v-if="user.status === 0" class="tag ban-tag">BANNED</text>
          </view>
          <text class="uid">UID: {{ user.id }} | REG: {{ user.created_at }}</text>
        </view>

        <view class="action-btn" @click="toggleStatus(user)">
          <text :class="user.status === 1 ? 'btn-disable' : 'btn-enable'">
            {{ user.status === 1 ? 'DISABLE' : 'ENABLE' }}
          </text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const SERVICE_HOST = '101.35.132.175'; // 记得改成你的 IP
const API_BASE = `http://${SERVICE_HOST}:5000`;

const users = ref([]);
const myInfo = ref({});

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
    data: { operator_id: myInfo.value.id }, // 传管理员ID去验证
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        users.value = res.data.data;
      } else {
        uni.showToast({ title: res.data.msg, icon: 'none' });
      }
    }
  });
};

const toggleStatus = (user) => {
  if (user.id === myInfo.value.id) {
    uni.showToast({ title: '无法操作自己', icon: 'none' });
    return;
  }

  const newStatus = user.status === 1 ? 0 : 1;
  const actionText = newStatus === 0 ? '禁用' : '启用';

  uni.showModal({
    title: '权限确认',
    content: `确定要 [${actionText}] 用户 ${user.username} 吗？`,
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
              user.status = newStatus; // 本地更新状态，不用刷新全页
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

<style>
page { background-color: #050505; color: #fff; font-family: 'Courier New', monospace; }
.container { padding: 20px; height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 50%, #111 0%, #000 90%); z-index: -1; }

.header { margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; }
.title { font-size: 24px; font-weight: bold; color: #00f3ff; display: block; }
.subtitle { font-size: 12px; color: #666; letter-spacing: 2px; }

.user-list { flex: 1; height: 0; }
.user-card { 
  display: flex; align-items: center; background: #111; 
  margin-bottom: 15px; padding: 15px; border: 1px solid #333; border-radius: 4px; 
  transition: all 0.3s;
}
.user-card.banned { border-color: #555; opacity: 0.6; filter: grayscale(0.8); }

.avatar { width: 50px; height: 50px; border-radius: 4px; background: #222; margin-right: 15px; }
.info { flex: 1; }
.top-row { display: flex; align-items: center; margin-bottom: 5px; }
.username { font-size: 16px; font-weight: bold; color: #fff; margin-right: 10px; }
.tag { font-size: 10px; padding: 2px 6px; border-radius: 2px; margin-right: 5px; font-weight: bold; }
.admin-tag { background: #00f3ff; color: #000; }
.ban-tag { background: #ff003c; color: #fff; }
.uid { font-size: 10px; color: #666; }

.action-btn { padding: 5px 10px; border: 1px solid #333; cursor: pointer; }
.btn-disable { color: #ff003c; }
.btn-enable { color: #00ff9d; }
.action-btn:active { background: #222; }
</style>