<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="dashboard-header fade-in">
      <view class="header-title">
        <text class="glitch-text" data-text="TACTICAL_MAP">计划中心</text>
        
      </view>
      <view class="system-status">
        <view class="status-dot online"></view>
        <text>SYS_ONLINE</text>
      </view>
    </view>

    <view class="stats-row fade-in">
      <view class="stat-card">
        <text class="stat-num">{{ activePlans.length }}</text>
        <text class="stat-label">(进行中)</text>
      </view>
      <view class="stat-card">
        <text class="stat-num">{{ totalProgress }}%</text>
        <text class="stat-label">(同步率)</text>
      </view>
    </view>

    <scroll-view scroll-y class="plan-list-scroll">
      
      <view v-if="activePlans.length === 0" class="empty-state">
        <text class="empty-icon">∅</text>
        <text>NO ACTIVE TACTICS DETECTED</text>
        <text class="empty-tip">请前往 [新建] 生成计划</text>
      </view>

      <view 
        v-for="(plan, index) in activePlans" 
        :key="plan.id" 
        class="plan-card slide-up"
        :style="{ animationDelay: index * 0.1 + 's' }"
        @click="goToDetail(plan.id)"
        @longpress="onLongPressPlan(plan)"
      >
        <view class="card-line"></view>
        <view class="card-content">
          <view class="card-top">
            <text class="plan-title">{{ plan.title }}</text>
            <text class="plan-days">{{ plan.total_days }} DAYS</text>
          </view>
          
          <text class="plan-goal">{{ plan.goal }}</text>
          
          <view class="progress-container">
            <view class="progress-bar">
              <view class="progress-fill" :style="{ width: plan.progress + '%' }"></view>
            </view>
            <text class="progress-val">{{ plan.progress }}%</text>
          </view>
          
          <view class="card-footer">
            <text class="status-text">● EXECUTING</text>
            <text class="arrow">ACCESS >></text>
          </view>
        </view>
      </view>
      
      <view style="height: 40px;"></view>
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


const onLongPressPlan = (plan) => {
  uni.vibrateShort();
  uni.showModal({
    title: '⚠️ 销毁协议',
    content: `确认要永久销毁战术计划：\n【${plan.title}】吗？`,
    confirmText: '销毁',
    confirmColor: '#ff003c',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        deletePlan(plan.id);
      }
    }
  });
};

const deletePlan = (id) => {
  uni.showLoading({ title: 'DELETING...' });
  
  uni.request({
    url: `${API_BASE}/api/plan/${id}`,
    method: 'DELETE',
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        uni.showToast({ title: '战术已销毁', icon: 'success' });
        fetchPlans();
      } else {
        uni.showToast({ title: '删除失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: '连接中断', icon: 'none' });
    }
  });
};
</script>

<style>
page { background-color: #050505; color: #e0e0e0; font-family: 'Courier New', monospace; }
.container { padding: 20px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 10%, #0a192f 0%, #000000 85%); z-index: -1; }
.dashboard-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px; margin-top: 10px; }
.glitch-text { font-size: 24px; font-weight: 900; color: #fff; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0, 243, 255, 0.5); }
.sub-text { font-size: 10px; color: #666; display: block; margin-top: 5px; }
.system-status { display: flex; align-items: center; font-size: 10px; color: #00f3ff; border: 1px solid rgba(0, 243, 255, 0.3); padding: 2px 6px; border-radius: 2px; background: rgba(0, 243, 255, 0.05); }
.status-dot { width: 6px; height: 6px; background: #00f3ff; border-radius: 50%; margin-right: 6px; animation: blink 2s infinite; box-shadow: 0 0 8px #00f3ff; }
.stats-row { display: flex; gap: 15px; margin-bottom: 30px; }
.stat-card { flex: 1; background: rgba(15, 23, 42, 0.6); border: 1px solid #334155; padding: 15px; text-align: center; }
.stat-num { font-size: 32px; font-weight: 900; color: #fff; display: block; }
.stat-label { font-size: 10px; color: #94a3b8; letter-spacing: 1px; margin-top: 5px; }
.section-label { font-size: 12px; color: #888; margin-bottom: 15px; border-bottom: 1px solid #222; padding-bottom: 5px; display: inline-block; }
.empty-state { text-align: center; margin-top: 50px; color: #444; }
.empty-icon { font-size: 40px; display: block; margin-bottom: 10px; }
.empty-tip { font-size: 12px; color: #00f3ff; margin-top: 10px; }
.plan-card { position: relative; background: #0b1120; margin-bottom: 20px; border: 1px solid #334155; overflow: hidden; transition: all 0.2s; }
.plan-card:active { border-color: #00f3ff; transform: scale(0.99); background: #111827; }
.card-line { position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }
.card-content { padding: 20px 20px 20px 24px; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.plan-title { font-size: 16px; font-weight: bold; color: #fff; letter-spacing: 1px; }
.plan-days { font-size: 10px; color: #00f3ff; background: rgba(0, 243, 255, 0.1); border: 1px solid rgba(0, 243, 255, 0.3); padding: 2px 6px; font-weight: bold; font-family: monospace; }
.plan-goal { font-size: 12px; color: #94a3b8; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 32px; margin-bottom: 15px; line-height: 1.4; }
.progress-container { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
.progress-bar { flex: 1; height: 4px; background: #1e293b; position: relative; overflow: hidden; border-radius: 2px; }
.progress-fill { 
  height: 100%; 
  background: linear-gradient(90deg, #0ea5e9, #00f3ff);
  box-shadow: 0 0 10px rgba(0, 243, 255, 0.3); 
  transition: width 0.5s ease; 
}
.progress-val { font-size: 12px; color: #00f3ff; font-weight: bold; font-family: monospace; text-shadow: 0 0 5px rgba(0, 243, 255, 0.5); }
.card-footer { display: flex; justify-content: space-between; font-size: 10px; border-top: 1px solid #1e293b; padding-top: 10px; }
.status-text { color: #0ea5e9; font-weight: bold; letter-spacing: 1px; }
.arrow { color: #475569; font-weight: bold; }
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s ease-out backwards; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>