<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>
    
    <view class="header-box">
      <text class="title">{{ t.title }}</text>
      <text class="subtitle">{{ t.subtitle }}</text>
    </view>

    <scroll-view scroll-y class="history-list">
      <view v-if="logs.length === 0" class="empty-box">
        <text class="glitch-text">{{ t.empty }}</text>
      </view>

      <view class="timeline-item" v-for="(log, index) in logs" :key="index" @click="showDetail(log)">
        <view class="left-section">
          <view class="neon-dot" :class="{ fail: log.status === 'FAIL' }"></view>
          <view class="neon-line" v-if="index < logs.length - 1"></view>
        </view>
        <view class="right-content cyber-card">
          <view class="row-top">
            <text class="task-time">{{ formatTime(log.executed_at) }}</text>
            <text class="status-badge" :class="{ fail: log.status === 'FAIL' }">
              {{ log.status === 'SUCCESS' ? t.status_ok : t.status_err }}
            </text>
          </view>
          <text class="task-name">{{ log.task_title }}</text>
          <view class="card-footer">
            <text class="type-code">{{ t.type_label }} {{ log.task_type }}</text>
            <text class="detail-link">{{ t.link_detail }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import messages from '@/utils/language.js';

const API_BASE = 'http://192.168.10.28:5000';
const logs = ref([]);
const t = ref(messages.zh.history);

onShow(() => {
  const lang = uni.getStorageSync('lang') || 'zh';
  t.value = messages[lang].history;

  const userInfo = uni.getStorageSync('userInfo');
  if (userInfo) getLogs(userInfo.id);
});

// ... getLogs, formatTime 逻辑保持不变 ...
// 为了节省篇幅，假设函数已定义
const getLogs = (userId) => { uni.request({ url: `${API_BASE}/api/logs?user_id=${userId}`, success: (res) => { if (res.data.code === 200) logs.value = res.data.data; } }); };
const formatTime = (t) => t ? t.substring(5, 16) : '';

const showDetail = (log) => {
  uni.showModal({
    title: t.value.modal_title,
    content: `TASK: ${log.task_title}\nSTATUS: ${log.status}\nTIME: ${log.executed_at}\n\nRESPONSE:\n${log.result || 'NULL'}`,
    showCancel: false,
    confirmText: t.value.modal_close
  });
};
</script>

<style>
/* ... CSS 样式与之前提供的 History 赛博风一致，请直接复用 ... */
page { background-color: #050505; color: #ccc; }
.container { padding: 20px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 10% 10%, #111 0%, #000 80%); z-index: -1; }
.header-box { margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 10px; }
.title { font-size: 24px; font-weight: 900; color: #fff; letter-spacing: 2px; }
.subtitle { font-size: 12px; color: #00f3ff; display: block; margin-top: 5px; }
.timeline-item { display: flex; padding-bottom: 0; }
.left-section { width: 30px; display: flex; flex-direction: column; align-items: center; margin-right: 15px; position: relative; }
.neon-dot { width: 10px; height: 10px; background: #000; border: 2px solid #00ff9d; border-radius: 50%; box-shadow: 0 0 10px #00ff9d; z-index: 2; flex-shrink: 0; }
.neon-dot.fail { border-color: #ff003c; box-shadow: 0 0 10px #ff003c; }
.neon-line { width: 1px; background: rgba(0, 243, 255, 0.3); flex-grow: 1; margin-top: 5px; margin-bottom: -15px; box-shadow: 0 0 5px rgba(0, 243, 255, 0.2); }
.cyber-card { flex: 1; background: rgba(20,20,20,0.8); border: 1px solid #333; padding: 15px; margin-bottom: 20px; backdrop-filter: blur(5px); clip-path: polygon(0 0, 100% 0, 100% 90%, 95% 100%, 0 100%); }
.task-time { color: #00f3ff; font-weight: bold; font-size: 16px; text-shadow: 0 0 5px rgba(0, 243, 255, 0.3); }
.status-badge { font-size: 12px; color: #00ff9d; font-weight: bold; }
.status-badge.fail { color: #ff003c; }
.task-name { font-size: 14px; color: #fff; margin: 10px 0; display: block; }
.card-footer { display: flex; justify-content: space-between; border-top: 1px solid #333; padding-top: 8px; }
.type-code { font-size: 10px; color: #666; }
.detail-link { font-size: 10px; color: #bc13fe; }
.empty-box { text-align: center; margin-top: 50px; }
.glitch-text { font-size: 20px; font-weight: bold; color: #333; letter-spacing: 5px; }
</style>