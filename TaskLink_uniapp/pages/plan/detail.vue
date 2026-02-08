<template>
  <view class="container dark-theme">
    <view class="nav-header">
      <view class="back-btn" @click="uni.navigateBack()">❮ BACK</view>
      <text class="nav-title">TACTICAL DETAIL</text>
    </view>

    <view v-if="loading" class="loading-state">
      <text class="loading-text">DECODING DATA...</text>
    </view>

    <view v-else class="content-area">
      <view class="plan-overview">
        <text class="big-title">{{ plan.title }}</text>
        <view class="meta-row">
          <text class="meta-tag">TARGET: {{ plan.goal }}</text>
        </view>
        <view class="meta-row">
          <text class="meta-tag blue">{{ plan.total_days }} DAYS CYCLE</text>
          <text class="meta-tag purple">PROGRESS: {{ plan.progress }}%</text>
        </view>
      </view>

      <view class="timeline">
        <view class="timeline-line"></view>
        
        <view v-for="(task, index) in tasks" :key="task.id" class="day-node">
          <view class="node-dot" :class="{ completed: task.is_completed }"></view>
          
          <view class="day-card" :class="{ active: activeDay === index }" @click="toggleDay(index)">
            <view class="day-header">
              <text class="day-idx">DAY {{ task.day < 10 ? '0'+task.day : task.day }}</text>
              <text class="day-title">{{ task.title }}</text>
              <view class="arrow" :class="{ rotated: activeDay === index }">▼</view>
            </view>
            
            <view class="day-body" v-if="activeDay === index">
              <text class="md-content">{{ task.content }}</text>
              
              <view class="action-bar">
                 <button class="mark-btn" @click.stop="toggleComplete(task)">
                   {{ task.is_completed ? '✅ MISSION COMPLETE' : '⚡ MARK AS DONE' }}
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
const activeDay = ref(0); // 默认展开第一天

onLoad((options) => {
  planId.value = options.id;
  fetchDetail();
});

const fetchDetail = () => {
  uni.request({
    url: `${API_BASE}/api/plan/detail?plan_id=${planId.value}`,
    success: (res) => {
      if (res.data.code === 200) {
        plan.value = res.data.data.info;
        tasks.value = res.data.data.tasks;
      }
      loading.value = false;
    }
  });
};

const toggleDay = (index) => {
  activeDay.value = activeDay.value === index ? -1 : index;
};

// 模拟完成功能 (你可以根据需要添加后端接口)
const toggleComplete = (task) => {
  task.is_completed = !task.is_completed;
  uni.showToast({ title: task.is_completed ? 'COMPLETED' : 'RESET', icon: 'none' });
};
</script>

<style>
page { background: #000; color: #fff; font-family: 'Courier New'; }
.container { padding: 20px; }

/* 导航 */
.nav-header { display: flex; align-items: center; margin-bottom: 30px; margin-top: 40px; }
.back-btn { color: #00f3ff; font-size: 14px; border: 1px solid #00f3ff; padding: 4px 10px; margin-right: 15px; }
.nav-title { font-weight: 900; font-size: 18px; letter-spacing: 2px; }

/* 总览 */
.plan-overview { margin-bottom: 40px; border-bottom: 1px solid #333; padding-bottom: 20px; }
.big-title { font-size: 24px; font-weight: bold; color: #fff; text-shadow: 0 0 10px rgba(255,255,255,0.3); display: block; margin-bottom: 10px; }
.meta-tag { display: inline-block; background: #111; color: #888; padding: 4px 8px; font-size: 10px; margin-right: 10px; margin-bottom: 5px; border: 1px solid #333; }
.meta-tag.blue { color: #00f3ff; border-color: #00f3ff; }
.meta-tag.purple { color: #bc13fe; border-color: #bc13fe; }

/* 时间轴系统 */
.timeline { position: relative; padding-left: 20px; }
.timeline-line { position: absolute; left: 4px; top: 0; bottom: 0; width: 2px; background: #222; z-index: 0; }

.day-node { margin-bottom: 20px; position: relative; z-index: 1; }
.node-dot { width: 10px; height: 10px; background: #000; border: 2px solid #666; border-radius: 50%; position: absolute; left: -20px; top: 15px; z-index: 2; transition: all 0.3s; }
.node-dot.completed { background: #00ff9d; border-color: #00ff9d; box-shadow: 0 0 10px #00ff9d; }

.day-card { background: #111; border: 1px solid #333; transition: all 0.3s; }
.day-card.active { border-color: #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.1); }

.day-header { padding: 15px; display: flex; align-items: center; justify-content: space-between; }
.day-idx { color: #00f3ff; font-weight: bold; margin-right: 10px; font-size: 16px; }
.day-title { flex: 1; color: #eee; font-size: 14px; font-weight: bold; }
.arrow { color: #666; font-size: 12px; transition: transform 0.3s; }
.arrow.rotated { transform: rotate(180deg); color: #00f3ff; }

/* 内容区 */
.day-body { padding: 0 15px 15px 15px; border-top: 1px solid #222; animation: slideDown 0.3s ease-out; }
@keyframes slideDown { from {opacity: 0; transform: translateY(-10px);} to {opacity: 1; transform: translateY(0);} }

.md-content { 
  font-size: 13px; 
  color: #aaa; 
  line-height: 1.6; 
  white-space: pre-wrap; /* 核心：防止文字重叠，保留换行 */
  display: block; 
  margin-top: 10px; 
}

.action-bar { margin-top: 15px; text-align: right; }
.mark-btn { background: transparent; border: 1px solid #444; color: #fff; font-size: 10px; display: inline-block; padding: 5px 15px; }
.mark-btn:active { background: #00ff9d; color: #000; border-color: #00ff9d; }

.loading-state { text-align: center; margin-top: 100px; color: #00f3ff; animation: blink 1s infinite; }
</style>