<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="nav-header">
      <view class="back-btn" @click="goBack">
        <text class="back-icon">←</text>
        <text>返回</text>
      </view>
      <text class="page-title">训练详情</text>
      <view style="width: 80rpx;"></view>
    </view>

    <scroll-view scroll-y class="list-area">
      <view class="list-wrapper">
        <view 
          class="word-card" 
          v-for="(item, index) in list" 
          :key="index"
          :class="'border-q' + item.quality"
        >
          <view class="card-main">
            <view class="word-row">
              <text class="w-text">{{ item.word }}</text>
              <view class="audio-btn" @click="playAudio(item.word)">
                <text>🔊</text>
              </view>
            </view>
            <text class="w-trans">{{ item.trans }}</text>
          </view>
          
          <view class="card-footer">
            <view class="quality-badge" :class="'q-' + item.quality">
              {{ getQualityLabel(item.quality) }}
            </view>
          </view>
        </view>
      </view>
      
      <view style="height: 40rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';                
import { onLoad, onShow } from '@dcloudio/uni-app';   
import { useTheme } from '@/utils/useTheme';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;
const list = ref([]);
const { isDarkMode } = useTheme();

onLoad((options) => {
  if (options.id) {
    fetchDetail(options.id);
  }
});

const fetchDetail = (sessionId) => {
  uni.showLoading({ title: '加载中...' });
  uni.request({
    url: `${API_BASE}/api/training/detail?session_id=${sessionId}`,
    success: (res) => {
      if (res.data.code === 200) {
        list.value = res.data.data;
      }
    },
    complete: () => uni.hideLoading()
  });
};

const playAudio = (word) => {
  const url = `https://dict.youdao.com/dictvoice?audio=${word}&type=2`;
  const audio = uni.createInnerAudioContext();
  audio.src = url;
  audio.play();
};

const getQualityLabel = (q) => {
  const map = { 0: '忘记', 3: '模糊', 4: '认识', 5: '精通' };
  return map[q] || '未评';
};

const goBack = () => uni.navigateBack();
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */

/* 深色模式变量 */
$dark-bg: #121212;
$dark-card: #1E1E1E;
$dark-text-main: #E0E0E0;
$dark-text-sub: #A0A0A0;

/* 评分配色 */
$q0: #EF9A9A; /* 柔和红 */
$q3: #FFE082; /* 柔和黄 */
$q4: #90CAF9; /* 莫兰迪蓝 */
$q5: #A5D6A7; /* 莫兰迪绿 */

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
  transition: background-color 0.3s;
}

.container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}

.container.dark {
  background-color: $dark-bg !important;
}

/* 2. 导航栏 */
.nav-header {
  height: 88rpx;
  padding-top: var(--status-bar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 30rpx;
  padding-right: 30rpx;
  background-color: $color-bg;
  transition: background-color 0.3s;
}

.container.dark .nav-header {
  background-color: $dark-bg;
}

.back-btn {
  display: flex;
  align-items: center;
  color: $color-primary;
  font-size: 28rpx;
  font-weight: 500;
  transition: color 0.3s;
}

.container.dark .back-btn {
  color: $dark-text-main;
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
  transition: color 0.3s;
}

.container.dark .page-title {
  color: $dark-text-main;
}

/* 3. 列表区域 */
.list-area {
  flex: 1;
  height: 0;
}

.list-wrapper {
  padding: 30rpx;
}

.word-card {
  background: $color-card;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(74, 111, 165, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 8rpx solid transparent;
  transition: transform 0.2s, background-color 0.3s, box-shadow 0.3s;
}

.container.dark .word-card {
  background: $dark-card;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.3);
}

.word-card:active { transform: scale(0.98); }

/* 侧边评分装饰条 */
.border-q0 { border-left-color: $q0; }
.border-q3 { border-left-color: $q3; }
.border-q4 { border-left-color: $q4; }
.border-q5 { border-left-color: $q5; }

.card-main {
  flex: 1;
}

.word-row {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.w-text {
  font-size: 34rpx;
  font-weight: 700;
  color: $color-text-main;
  margin-right: 20rpx;
  transition: color 0.3s;
}

.container.dark .w-text {
  color: $dark-text-main;
}

.audio-btn {
  padding: 10rpx;
  font-size: 28rpx;
  opacity: 0.3;
}

.w-trans {
  font-size: 26rpx;
  color: $color-text-sub;
  display: block;
  transition: color 0.3s;
}

.container.dark .w-trans {
  color: $dark-text-sub;
}

/* 4. 评分标签 */
.card-footer {
  margin-left: 20rpx;
}

.quality-badge {
  font-size: 20rpx;
  font-weight: 600;
  padding: 6rpx 16rpx;
  border-radius: 10rpx;
  color: #FFF;
}

.q-0 { background-color: $q0; }
.q-3 { background-color: $q3; color: #795548; }
.q-4 { background-color: $q4; }
.q-5 { background-color: $q5; }

/* 统一字体呼吸感 */
.w-text { letter-spacing: 0.5px; }
.w-trans { line-height: 1.4; }
</style>