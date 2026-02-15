<template>
  <view class="container">
    <view class="nav-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">←</text>
        <text>返回</text>
      </view>
      <text class="page-title">计划详情</text>
      <view style="width: 80rpx;"></view> </view>

    <view v-if="loading" class="loading-state">
      <view class="loading-spinner"></view>
      <text class="loading-text">Loading Plan...</text>
    </view>

    <view v-else class="content-area fade-in">
      <view class="plan-header-card">
        <text class="plan-title">{{ plan.title }}</text>
        <view class="plan-meta-row">
          <view class="meta-tag primary">
            <text class="tag-label">GOAL</text>
            <text class="tag-value">{{ plan.goal }}</text>
          </view>
        </view>
        <view class="plan-stats-row">
          <view class="stat-item">
            <text class="stat-num">{{ plan.total_days }}</text>
            <text class="stat-label">Days</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-num highlight">{{ plan.progress }}%</text>
            <text class="stat-label">Done</text>
          </view>
        </view>
      </view>

      <view class="timeline-section">
        <view class="timeline-line"></view>
        
        <view 
          v-for="(task, index) in tasks" 
          :key="task.id" 
          class="timeline-item slide-up" 
          :style="{ animationDelay: index * 0.05 + 's' }"
        >
          <view class="timeline-node" :class="{ 'completed': task.is_completed }">
            <view class="node-center"></view>
          </view>
          
          <view 
            class="task-card" 
            :class="{ 'active': activeDay === index, 'card-completed': task.is_completed }" 
            @click="toggleDay(index)"
          >
            <view class="card-header">
              <view class="header-left">
                <text class="day-index">DAY {{ (index + 1).toString().padStart(2, '0') }}</text>
                <text class="task-title">{{ task.title }}</text>
              </view>
              <view class="expand-icon" :class="{ 'rotated': activeDay === index }">
                <text>▼</text>
              </view>
            </view>
            
            <view v-if="activeDay === index" class="card-body">
              <text class="task-content">{{ getDisplayContent(index) }}</text>
              
              <view class="cursor-blink" v-if="typingIndex === index && !isTypingFinished"></view>
              
              <view class="action-bar fade-in" v-if="isTypingFinished || typingIndex !== index">
                <view 
                  class="complete-btn" 
                  :class="{ 'btn-done': task.is_completed }" 
                  @click.stop="toggleComplete(task)"
                >
                  <text>{{ task.is_completed ? '已完成' : '标记完成' }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <view style="height: 60rpx;"></view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;
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
  // 尝试返回上一页，如果不行则跳转首页
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.switchTab({ url: '/pages/index/index' });
  }
};

const fetchDetail = () => {
  uni.request({
    url: `${API_BASE}/api/plan/detail?plan_id=${planId.value}`,
    success: (res) => {
      if (res.data.code === 200) {
        plan.value = res.data.data.info;
        tasks.value = res.data.data.tasks;
      } else {
        uni.showToast({ title: '数据加载失败', icon: 'none' });
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
  if (!displayTexts.value[index]) {
    const fullContent = tasks.value[index].content || "暂无详细内容...";
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
  // 稍微加快打字速度
  timers[index] = setInterval(() => {
    if (i < fullText.length) {
      displayTexts.value[index] += fullText.substring(i, i+3);
      i += 3;
    } else {
      clearInterval(timers[index]);
      isTypingFinished.value = true;
    }
  }, 10); 
};

const toggleComplete = (task) => {
  const originalStatus = task.is_completed;
  task.is_completed = !task.is_completed;
  
  uni.request({
    url: `${API_BASE}/api/plan/task/${task.id}/toggle`,
    method: 'POST',
    success: (res) => {
      if (res.data.code === 200) {
        uni.showToast({ title: task.is_completed ? '已完成' : '已撤销', icon: 'none' });
      } else {
        task.is_completed = originalStatus;
        uni.showToast({ title: '操作失败', icon: 'none' });
      }
    },
    fail: () => {
      task.is_completed = originalStatus;
      uni.showToast({ title: '网络错误', icon: 'none' });
    }
  });
};
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */
$color-line: #E0E0E0;

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
}

.container {
  min-height: 100vh;
  background-color: $color-bg;
  padding: 0 30rpx;
  box-sizing: border-box;
}

/* 2. 导航栏 */
.nav-header {
  height: 88rpx;
  padding-top: var(--status-bar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.back-btn {
  display: flex;
  align-items: center;
  color: $color-primary;
  font-size: 28rpx;
  font-weight: 500;
  padding: 10rpx;
}

.back-icon {
  font-size: 36rpx;
  margin-right: 4rpx;
  margin-top: -4rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $color-text-main;
}

/* 3. 计划概览卡片 */
.plan-header-card {
  background: $color-card;
  border-radius: 20rpx;
  padding: 40rpx;
  margin-bottom: 50rpx;
  box-shadow: 0 10rpx 40rpx rgba(74, 111, 165, 0.08);
}

.plan-title {
  font-size: 40rpx;
  font-weight: 700;
  color: $color-text-main;
  margin-bottom: 24rpx;
  display: block;
}

.plan-meta-row {
  margin-bottom: 40rpx;
}

.meta-tag {
  display: inline-flex;
  flex-direction: column;
}

.tag-label {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 6rpx;
}

.tag-value {
  font-size: 26rpx;
  color: $color-text-main;
  line-height: 1.4;
}

.plan-stats-row {
  display: flex;
  align-items: center;
  border-top: 1px solid #F0F0F0;
  padding-top: 30rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-num {
  font-size: 44rpx;
  font-weight: 700;
  color: $color-text-main;
  line-height: 1;
  margin-bottom: 8rpx;
}

.stat-num.highlight { color: $color-primary; }

.stat-label {
  font-size: 22rpx;
  color: $color-text-sub;
}

.stat-divider {
  width: 1px;
  height: 50rpx;
  background: #F0F0F0;
}

/* 4. 时间轴区域 */
.timeline-section {
  position: relative;
  padding-left: 20rpx;
}

.timeline-line {
  position: absolute;
  left: 29rpx; /* 调整至节点中心 */
  top: 0;
  bottom: 0;
  width: 2rpx;
  background: #E0E0E0;
  z-index: 0;
}

.timeline-item {
  position: relative;
  padding-left: 60rpx; /* 为节点留出空间 */
  margin-bottom: 40rpx;
  z-index: 1;
}

/* 节点样式 */
.timeline-node {
  position: absolute;
  left: 10rpx;
  top: 40rpx;
  width: 40rpx;
  height: 40rpx;
  background: $color-bg; /* 遮挡线条 */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.node-center {
  width: 16rpx;
  height: 16rpx;
  background: $color-text-sub;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.timeline-node.completed .node-center {
  background: $color-accent;
  transform: scale(1.2);
}

/* 任务卡片 */
.task-card {
  background: $color-card;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid transparent;
}

.task-card:active { transform: scale(0.99); }

.task-card.active {
  box-shadow: 0 16rpx 40rpx rgba(74, 111, 165, 0.1);
  border-color: rgba(74, 111, 165, 0.2);
}

.task-card.card-completed {
  opacity: 0.8;
}

.task-card.card-completed .task-title {
  text-decoration: line-through;
  color: $color-text-sub;
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.day-index {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 700;
  margin-bottom: 8rpx;
  letter-spacing: 0.5px;
}

.task-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $color-text-main;
  line-height: 1.4;
}

.expand-icon {
  font-size: 20rpx;
  color: $color-text-sub;
  transition: transform 0.3s ease;
  margin-left: 20rpx;
  margin-top: 10rpx;
}

.expand-icon.rotated {
  transform: rotate(180deg);
  color: $color-primary;
}

/* 卡片展开内容 */
.card-body {
  margin-top: 30rpx;
  padding-top: 30rpx;
  border-top: 1px solid #F5F5F5;
}

.task-content {
  font-size: 26rpx;
  color: $color-text-main;
  line-height: 1.8;
  white-space: pre-wrap;
}

.cursor-blink {
  display: inline-block;
  width: 4rpx;
  height: 28rpx;
  background: $color-primary;
  margin-left: 4rpx;
  vertical-align: middle;
  animation: blink 1s infinite;
}

/* 操作栏 */
.action-bar {
  margin-top: 40rpx;
  display: flex;
  justify-content: flex-end;
}

.complete-btn {
  font-size: 24rpx;
  color: $color-primary;
  background: rgba(74, 111, 165, 0.1);
  padding: 12rpx 30rpx;
  border-radius: 30rpx;
  font-weight: 600;
  transition: all 0.2s;
}

.complete-btn:active { background: rgba(74, 111, 165, 0.2); }

.complete-btn.btn-done {
  background: rgba(255, 138, 101, 0.1);
  color: $color-accent;
}

/* 动画与加载 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
}

.loading-spinner {
  width: 50rpx;
  height: 50rpx;
  border: 4rpx solid rgba(74, 111, 165, 0.2);
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20rpx;
}

.loading-text {
  font-size: 24rpx;
  color: $color-text-sub;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes blink { 50% { opacity: 0; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
.fade-in { animation: slideUp 0.5s ease-out; }
.slide-up { animation: slideUp 0.5s ease-out backwards; }
</style>