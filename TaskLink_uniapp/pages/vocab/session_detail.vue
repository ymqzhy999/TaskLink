<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>
    
    <view class="header">
      <view class="back-btn" @click="goBack">⇇ BACK</view>
      <text class="title">LOG DETAILS</text>
    </view>

    <scroll-view scroll-y class="list-area">
      <view class="word-item" v-for="(item, index) in list" :key="index">
        <view class="w-main">
          <text class="w-text">{{ item.word }}</text>
          <view class="w-audio" @click="playAudio(item.word)">🔊</view>
        </view>
        <text class="w-trans">{{ item.trans }}</text>
        <view class="w-badge" :class="'q-' + item.quality">
          {{ getQualityLabel(item.quality) }}
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';                
import { onLoad } from '@dcloudio/uni-app';   
const API_BASE = `http://101.35.132.175:5000`;
const list = ref([]);

onLoad((options) => {
  if (options.id) {
    fetchDetail(options.id);
  }
});

const fetchDetail = (sessionId) => {
  uni.showLoading({ title: 'LOADING...' });
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

<style scoped>
page { background-color: #050505; color: #00f3ff; font-family: 'Courier New', monospace; }
.container { height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; width: 100%; height: 100%; background: #111; z-index: -1; }
.header { padding: 40rpx 30rpx; border-bottom: 1px solid #333; display: flex; align-items: center; justify-content: space-between; margin-top: 40rpx;}
.back-btn { font-size: 24rpx; color: #666; }	
.title { font-size: 32rpx; font-weight: bold; letter-spacing: 2rpx; }
.list-area { flex: 1; padding: 20rpx; box-sizing: border-box; }
.word-item { background: #1a1a1a; padding: 25rpx; margin-bottom: 20rpx; border-left: 4rpx solid #333; border-radius: 4rpx; }
.w-main { display: flex; align-items: center; margin-bottom: 10rpx; }
.w-text { font-size: 36rpx; color: #fff; font-weight: bold; margin-right: 20rpx; }
.w-audio { font-size: 30rpx; padding: 10rpx; }
.w-trans { font-size: 24rpx; color: #888; display: block; margin-bottom: 15rpx; }
.w-badge { display: inline-block; font-size: 20rpx; padding: 4rpx 12rpx; background: #000; border: 1px solid #333; border-radius: 4rpx; }
.q-0 { color: #ff003c; border-color: #ff003c; }
.q-5 { color: #00ff9d; border-color: #00ff9d; }
</style>