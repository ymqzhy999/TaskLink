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
        <text class="empty-sub">暂无已完成的计划</text>
      </view>

      <view class="timeline-item slide-in" v-for="(plan, index) in archivedPlans" :key="index" @click="goToDetail(plan.id)">
        <view class="left-section">
          <view class="neon-dot completed"></view>
          <view class="neon-line" v-if="index < archivedPlans.length - 1"></view>
        </view>
        <view class="right-content cyber-card">
          <view class="row-top">
            <text class="task-time">{{ plan.created_at }}</text>
            <text class="status-badge">COMPLETE</text>
          </view>
          <text class="task-name">{{ plan.title }}</text>
          <view class="card-footer">
            <text class="type-code">CYCLES: {{ plan.total_days }}</text>
            <text class="detail-link">REVIEW >></text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const API_BASE = 'http://192.168.10.28:5000';
const archivedPlans = ref([]);

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) fetchArchived(user.id);
});

const fetchArchived = (userId) => {
  uni.request({
    // 使用 status=archived 获取已完成计划
    url: `${API_BASE}/api/plans?user_id=${userId}&status=archived`,
    success: (res) => {
      if (res.data.code === 200) {
        archivedPlans.value = res.data.data;
      }
    }
  });
};

const goToDetail = (id) => {
  uni.navigateTo({ url: `/pages/plan/detail?id=${id}` });
};
</script>

<style>
/* 继承之前的风格，微调细节 */
page { background-color: #050505; color: #ccc; font-family: 'Courier New', monospace; }
.container { padding: 20px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 10% 10%, #111 0%, #000 80%); z-index: -1; }

.header-box { margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 15px; }
.title { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 2px; }
.subtitle { font-size: 12px; color: #666; display: block; margin-top: 5px; }

.timeline-item { display: flex; padding-bottom: 10px; }
.left-section { width: 30px; display: flex; flex-direction: column; align-items: center; margin-right: 15px; }
.neon-dot { width: 12px; height: 12px; background: #000; border: 2px solid #666; border-radius: 50%; z-index: 2; }
.neon-dot.completed { border-color: #00ff9d; box-shadow: 0 0 10px #00ff9d; background: #00ff9d; }
.neon-line { width: 2px; background: #222; flex-grow: 1; margin-top: 5px; margin-bottom: -15px; }

.cyber-card { flex: 1; background: rgba(20,20,20,0.6); border: 1px solid #333; padding: 15px; margin-bottom: 20px; transition: all 0.2s; }
.cyber-card:active { border-color: #00ff9d; background: rgba(0, 255, 157, 0.05); }

.row-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.task-time { color: #666; font-size: 12px; }
.status-badge { color: #00ff9d; font-size: 10px; border: 1px solid #00ff9d; padding: 1px 4px; }
.task-name { font-size: 16px; color: #fff; font-weight: bold; margin-bottom: 15px; display: block; }

.card-footer { display: flex; justify-content: space-between; border-top: 1px solid #222; padding-top: 10px; font-size: 10px; color: #888; }
.detail-link { color: #00f3ff; }

.empty-box { text-align: center; margin-top: 100px; opacity: 0.5; }
.glitch-text { font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #333; }
.empty-sub { font-size: 12px; color: #555; margin-top: 10px; display: block; }

.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-in { animation: slideIn 0.5s ease-out both; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
</style>