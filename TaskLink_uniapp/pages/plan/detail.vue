<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="nav-header">
      <view class="back-btn" @click="goBack">❮ 返回中枢</view>
      <text class="nav-title">TACTICAL DETAIL</text>
    </view>

    <view v-if="loading" class="loading-state">
      <text class="loading-text">正在解析战术数据...</text>
      <view class="loading-bar"></view>
    </view>

    <view v-else class="content-area">
      <view class="plan-overview fade-in">
        <text class="big-title">{{ plan.title }}</text>
        <view class="meta-row">
          <text class="meta-tag">核心目标: {{ plan.goal }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-tag blue">总周期: {{ plan.total_days }} 天</text>
          <text class="meta-tag purple">同步率: {{ plan.progress }}%</text>
        </view>
      </view>

      <view class="timeline">
        <view class="timeline-line"></view>
        
        <view v-for="(task, index) in tasks" :key="task.id" class="day-node slide-in" :style="{ animationDelay: index * 0.1 + 's' }">
          <view class="node-dot" :class="{ completed: task.is_completed }"></view>
          
          <view class="day-card" :class="{ active: activeDay === index }" @click="toggleDay(index)">
            <view class="day-header">
              <text class="day-idx">NODE {{ (index + 1).toString().padStart(2, '0') }}</text>
              <text class="day-title">{{ task.title }}</text>
              <view class="arrow" :class="{ rotated: activeDay === index }">▼</view>
            </view>
            
            <view class="day-body" v-if="activeDay === index">
              <text class="md-content typing-effect">{{ getDisplayContent(index) }}</text>
              
              <view class="cursor-line" v-if="typingIndex === index && !isTypingFinished"></view>
              
              <view class="action-bar fade-in-slow" v-if="isTypingFinished || typingIndex !== index">
                 <button class="mark-btn" :class="{ done: task.is_completed }" @click.stop="toggleComplete(task)">
                   {{ task.is_completed ? '✅ 节点已完成' : '⚡ 标记为完成' }}
                 </button>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

const API_BASE = 'http://192.168.10.28:5000'; 
const planId = ref(null);
const loading = ref(true);
const plan = ref({});
const tasks = ref([]);

const activeDay = ref(-1); 
const typingIndex = ref(-1);
const isTypingFinished = ref(true);
const displayTexts = ref({}); 
const timers = {}; 

onLoad((options) => {
  planId.value = options.id;
  if (planId.value) fetchDetail();
  else setTimeout(() => goBack(), 1000);
});

const goBack = () => {
  uni.switchTab({
    url: '/pages/index/index',
    fail: () => uni.navigateBack()
  });
};

const fetchDetail = () => {
  uni.request({
    url: `${API_BASE}/api/plan/detail?plan_id=${planId.value}`,
    success: (res) => {
      if (res.data.code === 200) {
        plan.value = res.data.data.info;
        tasks.value = res.data.data.tasks;
      } else {
        uni.showToast({ title: '数据损坏', icon: 'none' });
      }
      loading.value = false;
    },
    fail: () => {
      loading.value = false;
      uni.showToast({ title: '网络连接中断', icon: 'none' });
    }
  });
};

const toggleDay = (index) => {
  if (activeDay.value === index) {
    activeDay.value = -1; 
    return;
  }
  activeDay.value = index;
  // 仅首次展开触发打字机
  if (!displayTexts.value[index]) {
    const fullContent = tasks.value[index].content || "暂无数据...";
    startTypewriter(index, fullContent);
  }
};

const getDisplayContent = (index) => displayTexts.value[index] || '';

const startTypewriter = (index, fullText) => {
  if (timers[index]) clearInterval(timers[index]);
  typingIndex.value = index;
  isTypingFinished.value = false;
  displayTexts.value[index] = '';
  
  let i = 0;
  // 加快打字速度：5ms/字，减少等待焦虑
  timers[index] = setInterval(() => {
    if (i < fullText.length) {
      // 每次加2个字，提升渲染速度
      displayTexts.value[index] += fullText.substring(i, i+2);
      i += 2;
    } else {
      clearInterval(timers[index]);
      isTypingFinished.value = true;
    }
  }, 5); 
};

const toggleComplete = (task) => {
  task.is_completed = !task.is_completed;
  // 可以在这里加一个后端请求同步状态
  uni.showToast({ title: task.is_completed ? '节点已归档' : '状态重置', icon: 'none' });
};
</script>

<style>
page { background: #050505; color: #fff; font-family: 'Courier New', monospace; }
.container { padding: 20px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 10% 10%, #1a1a2e 0%, #000000 80%); z-index: -1; }

.nav-header { display: flex; align-items: center; margin-bottom: 30px; margin-top: 40px; }
.back-btn { color: #00f3ff; font-size: 14px; border: 1px solid #00f3ff; padding: 6px 12px; margin-right: 15px; cursor: pointer; background: rgba(0, 243, 255, 0.1); }
.nav-title { font-weight: 900; font-size: 18px; letter-spacing: 2px; }

.plan-overview { margin-bottom: 30px; border-bottom: 1px solid #333; padding-bottom: 20px; }
.big-title { font-size: 22px; font-weight: bold; color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.3); display: block; margin-bottom: 10px; }
.meta-tag { display: inline-block; background: #111; color: #888; padding: 4px 8px; font-size: 10px; margin-right: 10px; margin-bottom: 5px; border: 1px solid #333; }
.meta-tag.blue { color: #00f3ff; border-color: #00f3ff; }
.meta-tag.purple { color: #bc13fe; border-color: #bc13fe; }

.timeline { position: relative; padding-left: 20px; }
.timeline-line { position: absolute; left: 4px; top: 0; bottom: 0; width: 2px; background: #222; z-index: 0; }

.day-node { margin-bottom: 20px; position: relative; z-index: 1; }
.node-dot { width: 10px; height: 10px; background: #000; border: 2px solid #666; border-radius: 50%; position: absolute; left: -20px; top: 15px; z-index: 2; transition: all 0.3s; }
.node-dot.completed { background: #00ff9d; border-color: #00ff9d; box-shadow: 0 0 10px #00ff9d; }

.day-card { background: #111; border: 1px solid #333; transition: all 0.3s; }
.day-card.active { border-color: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.1); }

.day-header { padding: 15px; display: flex; align-items: center; justify-content: space-between; }
.day-idx { color: #00f3ff; font-weight: bold; margin-right: 10px; font-size: 16px; min-width: 70px; }
.day-title { flex: 1; color: #eee; font-size: 14px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.arrow { color: #666; font-size: 12px; transition: transform 0.3s; }
.arrow.rotated { transform: rotate(180deg); color: #00f3ff; }

.day-body { padding: 0 15px 15px 15px; border-top: 1px solid #222; }
.md-content { font-size: 13px; color: #aaa; line-height: 1.6; white-space: pre-wrap; display: inline; text-shadow: 0 0 2px rgba(0, 243, 255, 0.2); }
.cursor-line { display: inline-block; width: 8px; height: 14px; background: #00f3ff; animation: blink 0.8s infinite; margin-left: 2px; vertical-align: middle; }

.action-bar { margin-top: 20px; text-align: right; }
.mark-btn { background: transparent; border: 1px solid #00f3ff; color: #00f3ff; font-size: 12px; padding: 6px 15px; display: inline-block; }
.mark-btn:active { background: rgba(0, 243, 255, 0.2); }
.mark-btn.done { border-color: #00ff9d; color: #00ff9d; }

.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-in { animation: slideIn 0.5s ease-out backwards; }
.loading-state { text-align: center; margin-top: 100px; color: #00f3ff; }
.loading-bar { width: 100px; height: 2px; background: #00f3ff; margin: 10px auto; animation: loadingWidth 1.5s infinite ease-in-out; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes loadingWidth { 0% { width: 0; } 50% { width: 100px; } 100% { width: 0; } }
</style>