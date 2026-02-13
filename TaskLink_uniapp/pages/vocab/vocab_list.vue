<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>
    
    <view class="fixed-header">
        <view class="search-bar">
          <input 
            class="cyber-input" 
            v-model="searchKeyword" 
            placeholder="SEARCH DATABASE..." 
            @confirm="doSearch(true)"
          />
          <view class="search-btn" @click="doSearch(true)">🔍</view>
        </view>

        <view class="level-filter-bar">
            <picker 
                mode="selector" 
                :range="levelOptions" 
                range-key="label" 
                :value="levelIndex" 
                @change="handleLevelChange"
            >
                <view class="level-select-btn">
                    <text class="l-label">LEVEL FILTER:</text>
                    <text class="l-value">{{ levelOptions[levelIndex].label }}</text>
                    <text class="l-arrow">▼</text>
                </view>
            </picker>
        </view>

        <scroll-view class="letter-index" scroll-x>
          <view v-for="l in letters" :key="l" class="letter-item" :class="{active: activeLetter === l}" @click="filterByLetter(l)">{{ l }}</view>
        </scroll-view>

        <view class="filter-tabs">
          <view class="tab" :class="{active: !showDifficult}" @click="toggleDifficult(false)">ALL_DATA</view>
          <view class="tab danger" :class="{active: showDifficult}" @click="toggleDifficult(true)">HARD_MODE</view>
        </view>
    </view>

    <scroll-view 
        class="list-area" 
        scroll-y="true" 
        @scrolltolower="loadMore"
        lower-threshold="50"
    >
      <view 
        v-for="(item, index) in displayList" 
        :key="index" 
        class="word-item"
        @click="playAudio(item.word)"
      >
        <view class="w-row">
          <text class="w-word">{{ item.word }}</text>
          <text class="w-level-tag">{{ item.level }}</text> 
          <text class="w-phonetic" v-if="item.phonetic">[{{ item.phonetic }}]</text>
          <text class="audio-hint">🔊</text>
        </view>
        <text class="w-trans">{{ item.translation }}</text>
      </view>
      
      <view class="loading-more">
        <text v-if="loading">LOADING MORE...</text>
        <text v-else-if="!hasMore">--- END OF FILE ---</text>
        <text v-else-if="displayList.length === 0">NO DATA FOUND</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const API_BASE = `http://101.35.132.175:5000`; 
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const displayList = ref([]);
const searchKeyword = ref('');
const activeLetter = ref('');
const showDifficult = ref(false);

const levelOptions = [
    { label: '全部 (ALL)', value: 'ALL' },
    { label: '初中 (JUNIOR)', value: 'JUNIOR' },
    { label: '高中 (SENIOR)', value: 'SENIOR' },
    { label: '四级 (CET-4)', value: 'CET4' },
    { label: '六级 (CET-6)', value: 'CET6' },
    { label: '托福 (TOEFL)', value: 'TOEFL' }
];
const levelIndex = ref(0); 

const page = ref(1);
const pageSize = 20;
const hasMore = ref(true);
const loading = ref(false);

const getToken = () => uni.getStorageSync('userInfo')?.token || '';

// 播放音频 (保留)
const playAudio = (word) => {
    const url = `https://dict.youdao.com/dictvoice?audio=${word}&type=2`;
    const audio = uni.createInnerAudioContext();
    audio.src = url;
    audio.play();
    uni.vibrateShort();
};

const handleLevelChange = (e) => {
    levelIndex.value = e.detail.value;
    doSearch(true); 
};

const doSearch = (isRefresh = false) => {
  if (loading.value) return;
  
  if (isRefresh) {
    page.value = 1;
    displayList.value = [];
    hasMore.value = true;
  }
  
  if (!hasMore.value && !isRefresh) return;
  
  loading.value = true;
  const user = uni.getStorageSync('userInfo');
  const selectedLevel = levelOptions[levelIndex.value].value;

  uni.request({
    url: `${API_BASE}/api/vocab/search`,
    header: { 'Authorization': getToken() },
    data: {
      user_id: user.id,
      word: searchKeyword.value,
      cn: searchKeyword.value,
      letter: activeLetter.value,
      difficult: showDifficult.value,
      level: selectedLevel,
      page: page.value,
      page_size: pageSize
    },
    success: (res) => {
      loading.value = false;
      if (res.data.code === 200) {
        const newItems = res.data.data;
        if (isRefresh) {
            displayList.value = newItems;
        } else {
            displayList.value = [...displayList.value, ...newItems];
        }
        hasMore.value = res.data.has_more;
        if (hasMore.value) {
            page.value++;
        }
      }
    },
    fail: () => {
        loading.value = false;
        uni.showToast({ title: '网络错误', icon: 'none' });
    }
  });
};

const loadMore = () => { doSearch(false); };
const filterByLetter = (l) => { activeLetter.value = activeLetter.value === l ? '' : l; doSearch(true); };
const toggleDifficult = (val) => { showDifficult.value = val; doSearch(true); };

onMounted(() => doSearch(true));
</script>

<style scoped>
page { background-color: #050505; color: #00f3ff; font-family: 'Courier New', monospace; height: 100vh; overflow: hidden; }
.container { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.cyber-bg { position: fixed; width: 100%; height: 100%; background: radial-gradient(circle, #111 0%, #000 100%); z-index: -1; }
.fixed-header { background: #050505; z-index: 10; border-bottom: 1px solid #222; }

.search-bar { display: flex; padding: 30rpx; gap: 20rpx; }
.cyber-input { flex: 1; border: 1px solid #333; color: #fff; padding: 15rpx 20rpx; background: #0a0a0a; border-radius: 4rpx; }
.search-btn { padding: 15rpx 30rpx; background: #222; border: 1px solid #444; border-radius: 4rpx; }
.level-filter-bar { padding: 0 30rpx 20rpx; }
.level-select-btn { display: flex; justify-content: space-between; align-items: center; background: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff; padding: 15rpx 20rpx; border-radius: 4rpx; }
.l-label { font-size: 22rpx; color: #00f3ff; font-weight: bold; }
.l-value { font-size: 24rpx; color: #fff; }
.letter-index { white-space: nowrap; padding: 20rpx 0; border-top: 1px dashed #222; height: 80rpx; }
.letter-item { display: inline-block; padding: 10rpx 25rpx; color: #666; font-weight: bold; font-size: 28rpx; }
.letter-item.active { color: #00ff9d; border-bottom: 2px solid #00ff9d; }
.filter-tabs { display: flex; border-top: 1px solid #222; }
.tab { flex: 1; text-align: center; padding: 25rpx; color: #666; font-size: 24rpx; background: #080808; }
.tab.active { color: #fff; background: #1a1a1a; border-bottom: 2px solid #00f3ff; }
.list-area { flex: 1; padding: 0 30rpx; box-sizing: border-box; height: 0; overflow-y: scroll; }
.word-item { padding: 30rpx 0; border-bottom: 1px dashed #222; }
.word-item:active { background: #111; }
.w-row { display: flex; align-items: baseline; gap: 15rpx; margin-bottom: 10rpx; flex-wrap: wrap; }
.w-word { font-size: 36rpx; color: #fff; font-weight: bold; }
.w-level-tag { font-size: 18rpx; color: #000; background: #00f3ff; padding: 2rpx 8rpx; border-radius: 4rpx; font-weight: bold; vertical-align: middle; }
.w-phonetic { color: #00f3ff; font-size: 24rpx; font-family: sans-serif; }
.w-trans { display: block; color: #888; font-size: 26rpx; line-height: 1.4; }
.audio-hint { font-size: 24rpx; margin-left: auto; opacity: 0.5; }
.loading-more { text-align: center; padding: 40rpx; font-size: 22rpx; color: #444; }
</style>