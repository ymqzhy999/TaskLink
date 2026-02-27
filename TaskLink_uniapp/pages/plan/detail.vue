<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
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
import { onLoad, onShow } from '@dcloudio/uni-app';
import { useTheme } from '@/utils/useTheme';
import { usePet } from '@/composables/usePet';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;
const planId = ref(null);
const loading = ref(true);
const plan = ref({});
const { isDarkMode } = useTheme();
const tasks = ref([]);

const activeDay = ref(-1); 
const typingIndex = ref(-1);
const isTypingFinished = ref(true);
const displayTexts = ref({}); 
const timers = {}; 

onLoad((options) => {
  if (options.id) {
    planId.value = options.id;
    fetchDetail(options.id);
  } else {
    uni.showToast({ title: '参数错误', icon: 'none' });
    setTimeout(() => uni.navigateBack(), 1000);
  }
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

const { onTaskCompleted } = usePet();

const toggleComplete = (task) => {
  const originalStatus = task.is_completed;
  task.is_completed = !task.is_completed;
  
  uni.request({
    url: `${API_BASE}/api/plan/task/${task.id}/toggle`,
    method: 'POST',
    success: (res) => {
      if (res.data.code === 200) {
        uni.showToast({ title: task.is_completed ? '已完成' : '已撤销', icon: 'none' });
        // 如果标记为完成，触发宠物响应
        if (task.is_completed && !originalStatus) {
          onTaskCompleted();
        }
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

/* 2. Nav Header */
.nav-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40rpx; transition: background-color 0.3s; }
.back-btn { display: flex; align-items: center; font-size: 28rpx; font-weight: 600; color: $color-text-sub; transition: color 0.3s; }
.container.dark .back-btn { color: $dark-text-sub; }

.back-icon { font-size: 36rpx; margin-right: 8rpx; }

.page-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; transition: color 0.3s; }
.container.dark .page-title { color: $dark-text-main; }

/* 3. Plan Header */
.plan-header-card { 
  background: $color-card; 
  border-radius: 20rpx; 
  padding: 40rpx 30rpx; 
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.03); 
  margin-bottom: 60rpx; 
  transition: background-color 0.3s, box-shadow 0.3s; 
}
.container.dark .plan-header-card { background: $dark-card; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.3); }

.plan-title { font-size: 40rpx; font-weight: 800; color: $color-text-main; margin-bottom: 24rpx; line-height: 1.3; transition: color 0.3s; }
.container.dark .plan-title { color: $dark-text-main; }

.plan-meta-row { margin-bottom: 40rpx; }
.meta-tag { display: inline-flex; flex-direction: column; }
.tag-label { font-size: 20rpx; font-weight: 700; color: $color-text-sub; letter-spacing: 1px; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .tag-label { color: $dark-text-sub; }

.tag-value { font-size: 26rpx; color: $color-text-main; font-weight: 500; transition: color 0.3s; }
.container.dark .tag-value { color: $dark-text-main; }

.plan-stats-row { display: flex; justify-content: space-around; align-items: center; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 30rpx; transition: border-color 0.3s; }
.container.dark .plan-stats-row { border-top: 1px solid rgba(255,255,255,0.05); }

.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 36rpx; font-weight: 800; color: $color-text-main; margin-bottom: 4rpx; transition: color 0.3s; }
.container.dark .stat-num { color: $dark-text-main; }
.highlight { color: $color-primary; }

.stat-label { font-size: 22rpx; color: $color-text-sub; font-weight: 600; transition: color 0.3s; }
.container.dark .stat-label { color: $dark-text-sub; }

.stat-divider { width: 1px; height: 40rpx; background: rgba(0,0,0,0.05); transition: background-color 0.3s; }
.container.dark .stat-divider { background: rgba(255,255,255,0.05); }

/* 4. Timeline */
.timeline-section { position: relative; padding-left: 20rpx; }
.timeline-line { position: absolute; left: 34rpx; top: 40rpx; bottom: 0; width: 4rpx; background: rgba(0,0,0,0.06); z-index: 0; transition: background-color 0.3s; }
.container.dark .timeline-line { background: rgba(255,255,255,0.06); }

.timeline-item { display: flex; margin-bottom: 40rpx; position: relative; z-index: 1; align-items: flex-start; }

.timeline-node { 
  width: 32rpx; 
  height: 32rpx; 
  background: $color-bg; 
  border: 4rpx solid $color-text-sub; 
  border-radius: 50%; 
  margin-right: 30rpx; 
  margin-top: 36rpx; 
  flex-shrink: 0; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  transition: all 0.3s; 
}
.container.dark .timeline-node { background: $dark-bg; border-color: $dark-text-sub; }

.timeline-node.completed { border-color: $color-primary; background: $color-primary; }
.node-center { width: 12rpx; height: 12rpx; background: #FFF; border-radius: 50%; opacity: 0; transition: opacity 0.3s; }
.timeline-node.completed .node-center { opacity: 1; }

/* 任务卡片 */
.task-card { 
  flex: 1; 
  background: $color-card; 
  border-radius: 16rpx; 
  padding: 30rpx; 
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.02); 
  transition: all 0.3s ease; 
}
.container.dark .task-card { background: $dark-card; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.3); }

.task-card.active { box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.1); }
.container.dark .task-card.active { box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.4); }

.task-card.card-completed { opacity: 0.8; }
.task-card.card-completed .task-title { text-decoration: line-through; color: $color-text-sub; }
.container.dark .task-card.card-completed .task-title { color: $dark-text-sub; }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.header-left { display: flex; flex-direction: column; }

.day-index { font-size: 20rpx; font-weight: 800; color: $color-text-sub; letter-spacing: 1px; margin-bottom: 8rpx; transition: color 0.3s; }
.container.dark .day-index { color: $dark-text-sub; }

.task-title { font-size: 30rpx; font-weight: 700; color: $color-text-main; line-height: 1.4; transition: color 0.3s; }
.container.dark .task-title { color: $dark-text-main; }

.expand-icon { font-size: 20rpx; color: $color-text-sub; transition: transform 0.3s; margin-top: 10rpx; }
.expand-icon.rotated { transform: rotate(180deg); }

/* 展开内容 */
.card-body { margin-top: 30rpx; padding-top: 30rpx; border-top: 1px solid rgba(0,0,0,0.05); transition: border-color 0.3s; }
.container.dark .card-body { border-top: 1px solid rgba(255,255,255,0.05); }

.task-content { font-size: 26rpx; color: $color-text-main; line-height: 1.8; white-space: pre-wrap; transition: color 0.3s; }
.container.dark .task-content { color: $dark-text-main; }

.action-bar { margin-top: 30rpx; display: flex; justify-content: flex-end; }
.complete-btn { 
  background: #F0F2F5; 
  padding: 12rpx 30rpx; 
  border-radius: 8rpx; 
  font-size: 24rpx; 
  font-weight: 600; 
  color: $color-text-sub; 
  transition: all 0.3s; 
}
.container.dark .complete-btn { background: #333; color: $dark-text-sub; }

.btn-done { background: rgba(76, 175, 80, 0.1); color: #4CAF50; }
.container.dark .btn-done { background: rgba(76, 175, 80, 0.2); color: #4CAF50; }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; }
.loading-spinner { width: 60rpx; height: 60rpx; border: 6rpx solid rgba(0,0,0,0.1); border-top-color: $color-primary; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20rpx; transition: border-color 0.3s; }
.container.dark .loading-spinner { border-color: rgba(255,255,255,0.1); border-top-color: $color-primary; }

.loading-text { font-size: 24rpx; color: $color-text-sub; font-weight: 600; transition: color 0.3s; }
.container.dark .loading-text { color: $dark-text-sub; }

/* 5. 动画 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.slide-up { animation: slideUp 0.6s ease-out backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
</style>