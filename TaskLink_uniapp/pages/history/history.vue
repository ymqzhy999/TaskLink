<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>
    
    <view class="header-box fade-in">
      <text class="title">DATA_ARCHIVES</text>
      <text class="subtitle">// 已完成的战术协议历史记录</text>
    </view>

    <scroll-view scroll-y class="history-list">
      <view v-if="archivedPlans.length === 0" class="empty-box">
        <text class="glitch-text">NO ARCHIVES</text>
        <text class="empty-sub">暂无已归档的战术</text>
        <text class="empty-tip">当所有节点标记为完成后，计划将自动归档至此</text>
      </view>

      <view class="timeline-item slide-in" v-for="(plan, index) in archivedPlans" :key="index" @click="goToDetail(plan.id)">
        <view class="left-section">
          <view class="neon-dot completed"></view>
          <view class="neon-line" v-if="index < archivedPlans.length - 1"></view>
        </view>
        
        <view class="right-content cyber-card">
          <view class="row-top">
            <text class="task-time">{{ formatDate(plan.created_at) }}</text>
            <text class="status-badge">ARCHIVED</text>
          </view>
          <text class="task-name">{{ plan.title }}</text>
          <view class="card-footer">
            <text class="type-code">CYCLES: {{ plan.total_days }} DAYS</text>
            <text class="detail-link">REVIEW >></text>
          </view>
        </view>
      </view>
      
      <view style="height: 30px;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';

const API_BASE = 'http://192.168.10.28:5000'; // ⚠️ 请确保 IP 正确
const archivedPlans = ref([]);

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) {
    fetchArchived(user.id);
  } else {
    uni.showToast({ title: '请先登录', icon: 'none' });
  }
});

// 🔥 新增：下拉刷新支持
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
      uni.showToast({ title: '无法连接数据中枢', icon: 'none' });
    }
  });
};

const goToDetail = (id) => {
  uni.navigateTo({ url: `/pages/plan/detail?id=${id}` });
};

// 简单的日期格式化
const formatDate = (str) => {
  if (!str) return '';
  return str.split(' ')[0]; // 只显示 YYYY-MM-DD
}
</script>

<style>
/* 保持原有赛博朋克风格 */
page { background-color: #050505; color: #ccc; font-family: 'Courier New', monospace; }
.container { padding: 20px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 10% 10%, #111 0%, #000 80%); z-index: -1; }

.header-box { margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 15px; border-left: 4px solid #00ff9d; padding-left: 15px; }
.title { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 2px; display: block; }
.subtitle { font-size: 12px; color: #00ff9d; display: block; margin-top: 5px; opacity: 0.8; }

.timeline-item { display: flex; padding-bottom: 0; min-height: 100px; }
.left-section { width: 30px; display: flex; flex-direction: column; align-items: center; margin-right: 15px; position: relative; }
.neon-dot { width: 14px; height: 14px; background: #000; border: 2px solid #00ff9d; border-radius: 50%; z-index: 2; box-shadow: 0 0 10px #00ff9d; }
.neon-line { width: 2px; background: rgba(0, 255, 157, 0.3); flex-grow: 1; margin-top: 5px; margin-bottom: -5px; }

.cyber-card { flex: 1; background: rgba(20,20,20,0.6); border: 1px solid rgba(0, 255, 157, 0.3); padding: 15px; margin-bottom: 20px; transition: all 0.2s; position: relative; overflow: hidden; }
.cyber-card:active { border-color: #00ff9d; background: rgba(0, 255, 157, 0.1); transform: scale(0.98); }

.row-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.task-time { color: #666; font-size: 12px; font-weight: bold; }
.status-badge { color: #000; background: #00ff9d; font-size: 10px; padding: 2px 6px; font-weight: 900; letter-spacing: 1px; }

.task-name { font-size: 16px; color: #fff; font-weight: bold; margin-bottom: 15px; display: block; text-shadow: 0 0 5px rgba(0, 255, 157, 0.3); }

.card-footer { display: flex; justify-content: space-between; border-top: 1px solid #333; padding-top: 10px; font-size: 10px; color: #888; align-items: center; }
.detail-link { color: #00ff9d; letter-spacing: 1px; }

.empty-box { text-align: center; margin-top: 80px; opacity: 0.6; }
.glitch-text { font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #444; }
.empty-sub { font-size: 14px; color: #666; margin-top: 10px; display: block; }
.empty-tip { font-size: 12px; color: #444; margin-top: 5px; display: block; }

.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-in { animation: slideIn 0.5s ease-out backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
</style>