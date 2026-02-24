<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="fixed-header">
      <view class="search-section">
        <view class="search-input-wrapper">
          <text class="search-icon">🔍</text>
          <input 
            class="custom-input" 
            v-model="searchKeyword" 
            placeholder="搜索单词或中文释义..." 
            placeholder-class="ph-style"
            @confirm="doSearch(true)"
          />
          <view class="clear-btn" v-if="searchKeyword" @click="searchKeyword='';doSearch(true)">✕</view>
        </view>
      </view>

      <view class="filter-toolbar">
        <picker 
          mode="selector" 
          :range="levelOptions" 
          range-key="label" 
          :value="levelIndex" 
          @change="handleLevelChange"
        >
          <view class="custom-dropdown" hover-class="btn-hover">
            <view class="dropdown-info">
              <text class="dropdown-label">LEVEL</text>
              <text class="dropdown-value">{{ levelOptions[levelIndex].label.split(' ')[0] }}</text>
            </view>
            <text class="dropdown-arrow">▼</text>
          </view>
        </picker>

        <view class="mode-capsule">
          <view class="mode-item" :class="{active: !showDifficult}" @click="toggleDifficult(false)" hover-class="tab-hover">全部</view>
          <view class="mode-item" :class="{active: showDifficult}" @click="toggleDifficult(true)" hover-class="tab-hover">困难</view>
        </view>
      </view>

      <scroll-view class="letter-scroll" scroll-x show-scrollbar="false">
        <view 
          v-for="l in letters" 
          :key="l" 
          class="letter-item" 
          :class="{active: activeLetter === l}" 
          @click="filterByLetter(l)"
        >{{ l }}</view>
      </scroll-view>
    </view>

    <scroll-view 
      class="list-area" 
      scroll-y="true" 
      @scrolltolower="loadMore"
      lower-threshold="100"
    >
      <view v-if="displayList.length > 0" class="list-wrapper">
        <view 
          v-for="(item, index) in displayList" 
          :key="index" 
          class="word-card"
          hover-class="item-hover"
          @click="playAudio(item.word)"
        >
          <view class="card-top">
            <text class="w-word">{{ item.word }}</text>
            <view class="w-tags">
              <text class="tag level-tag">{{ item.level }}</text>
              <text class="tag phonetic-tag" v-if="item.phonetic">[{{ item.phonetic }}]</text>
            </view>
            <text class="audio-icon">🔊</text>
          </view>
          <text class="w-trans">{{ item.translation }}</text>
        </view>
      </view>

      <view class="status-footer">
        <block v-if="loading">
          <view class="loading-spinner"></view>
          <text>正在检索数据库...</text>
        </block>
        <text v-else-if="!hasMore && displayList.length > 0">已经到底了</text>
        <view v-else-if="displayList.length === 0" class="empty-view">
          <text class="empty-icon">📂</text>
          <text>没有找到相关单词</text>
        </view>
      </view>
      
      <view style="height: 40rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useTheme } from '@/utils/useTheme';

const API_BASE = `http://101.35.132.175:5000`; 
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const displayList = ref([]);
const { isDarkMode } = useTheme();
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
        if (isRefresh) displayList.value = newItems;
        else displayList.value = [...displayList.value, ...newItems];
        hasMore.value = res.data.has_more;
        if (hasMore.value) page.value++;
      }
    },
    fail: () => {
        loading.value = false;
        uni.showToast({ title: '网络连接异常', icon: 'none' });
    }
  });
};

const loadMore = () => { doSearch(false); };
const filterByLetter = (l) => { activeLetter.value = activeLetter.value === l ? '' : l; doSearch(true); };
const toggleDifficult = (val) => { showDifficult.value = val; doSearch(true); };

onMounted(() => doSearch(true));
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
$dark-input-bg: #2C2C2C;

page { background-color: $color-bg; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }

.container { min-height: 100vh; position: relative; transition: all 0.3s; padding-top: var(--status-bar-height); }
.container.dark { background-color: $dark-bg !important; }

/* 2. Fixed Header */
.fixed-header { position: fixed; top: 0; left: 0; width: 100%; background: rgba(245, 245, 240, 0.98); z-index: 100; border-bottom: 1px solid rgba(0,0,0,0.05); padding-top: var(--status-bar-height); backdrop-filter: blur(10px); transition: background-color 0.3s, border-color 0.3s; }
.container.dark .fixed-header { background: rgba(18, 18, 18, 0.98); border-bottom: 1px solid rgba(255,255,255,0.05); }

/* Search Section */
.search-section { padding: 20rpx 30rpx; }
.search-input-wrapper { background: #FFFFFF; border-radius: 40rpx; height: 80rpx; display: flex; align-items: center; padding: 0 30rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.05); transition: background-color 0.3s, box-shadow 0.3s; }
.container.dark .search-input-wrapper { background: $dark-input-bg; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.3); }

.search-icon { font-size: 32rpx; margin-right: 16rpx; }

.custom-input { flex: 1; height: 100%; font-size: 28rpx; color: $color-text-main; transition: color 0.3s; }
.container.dark .custom-input { color: $dark-text-main; }

.ph-style { color: #B0BEC5; }
.clear-btn { font-size: 28rpx; color: $color-text-sub; padding: 10rpx; transition: color 0.3s; }
.container.dark .clear-btn { color: $dark-text-sub; }

/* Filter Toolbar */
.filter-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 0 30rpx 20rpx; }
.custom-dropdown { display: flex; align-items: center; background: rgba(74, 111, 165, 0.1); padding: 8rpx 24rpx; border-radius: 30rpx; transition: background-color 0.3s; }
.container.dark .custom-dropdown { background: rgba(74, 111, 165, 0.2); }

.dropdown-info { display: flex; flex-direction: column; margin-right: 16rpx; }
.dropdown-label { font-size: 16rpx; font-weight: 800; color: $color-text-sub; letter-spacing: 1px; transition: color 0.3s; }
.container.dark .dropdown-label { color: $dark-text-sub; }

.dropdown-value { font-size: 24rpx; font-weight: 700; color: $color-primary; }
.dropdown-arrow { font-size: 20rpx; color: $color-primary; }

.mode-capsule { display: flex; background: #E0E0E0; border-radius: 30rpx; padding: 4rpx; transition: background-color 0.3s; }
.container.dark .mode-capsule { background: #333; }

.mode-item { padding: 8rpx 24rpx; border-radius: 26rpx; font-size: 22rpx; font-weight: 600; color: $color-text-sub; transition: all 0.2s; }
.container.dark .mode-item { color: $dark-text-sub; }

.mode-item.active { background: #FFFFFF; color: $color-text-main; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1); }
.container.dark .mode-item.active { background: $dark-card; color: $dark-text-main; }

/* Letter Scroll */
.letter-scroll { white-space: nowrap; padding: 10rpx 30rpx 20rpx; border-top: 1px solid rgba(0,0,0,0.03); transition: border-color 0.3s; }
.container.dark .letter-scroll { border-top: 1px solid rgba(255,255,255,0.03); }

.letter-item { display: inline-block; padding: 8rpx 16rpx; font-size: 24rpx; font-weight: 700; color: $color-text-sub; border-radius: 8rpx; margin-right: 8rpx; transition: all 0.2s; }
.container.dark .letter-item { color: $dark-text-sub; }

.letter-item.active { background: $color-primary; color: #FFFFFF; }

/* 3. List Area */
.list-area { height: 100vh; padding-top: 320rpx; box-sizing: border-box; }
.list-wrapper { padding: 20rpx 30rpx; }

.word-card { background: $color-card; border-radius: 20rpx; padding: 30rpx; margin-bottom: 24rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02); display: flex; flex-direction: column; transition: background-color 0.3s, box-shadow 0.3s; }
.container.dark .word-card { background: $dark-card; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.3); }

.item-hover { transform: scale(0.98); opacity: 0.9; }

.card-top { display: flex; align-items: center; margin-bottom: 12rpx; }
.w-word { font-size: 36rpx; font-weight: 700; color: $color-text-main; margin-right: 16rpx; transition: color 0.3s; }
.container.dark .w-word { color: $dark-text-main; }

.w-tags { flex: 1; display: flex; gap: 10rpx; }
.tag { font-size: 20rpx; padding: 2rpx 10rpx; border-radius: 6rpx; font-weight: 600; }
.level-tag { background: rgba(74, 111, 165, 0.1); color: $color-primary; transition: background-color 0.3s; }
.container.dark .level-tag { background: rgba(74, 111, 165, 0.2); }

.phonetic-tag { background: #F5F5F5; color: $color-text-sub; font-family: monospace; transition: background-color 0.3s, color 0.3s; }
.container.dark .phonetic-tag { background: #333; color: $dark-text-sub; }

.audio-icon { font-size: 32rpx; color: $color-text-sub; padding: 10rpx; transition: color 0.3s; }
.container.dark .audio-icon { color: $dark-text-sub; }

.w-trans { font-size: 26rpx; color: $color-text-sub; line-height: 1.4; transition: color 0.3s; }
.container.dark .w-trans { color: $dark-text-sub; }

/* Status Footer */
.status-footer { text-align: center; padding: 40rpx 0; display: flex; flex-direction: column; align-items: center; font-size: 24rpx; color: $color-text-sub; transition: color 0.3s; }
.container.dark .status-footer { color: $dark-text-sub; }

.loading-spinner { width: 30rpx; height: 30rpx; border: 4rpx solid #E0E0E0; border-top-color: $color-primary; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16rpx; transition: border-color 0.3s; }
.container.dark .loading-spinner { border-color: #444; border-top-color: $color-primary; }

.empty-view { display: flex; flex-direction: column; align-items: center; margin-top: 60rpx; }
.empty-icon { font-size: 60rpx; margin-bottom: 20rpx; filter: grayscale(1); }

@keyframes spin { to { transform: rotate(360deg); } }
</style>