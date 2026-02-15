<template>
  <view class="container">
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
$color-bg: #F5F5F0;
$color-card: #FFFFFF;
$color-primary: #4A6FA5;
$color-accent: #FF8A65;
$color-text-main: #2C3E50;
$color-text-sub: #95A5A6;
$color-line: #E0E0E0;

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
  overflow: hidden;
}

.container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.fixed-header {
  background-color: $color-bg;
  padding-top: var(--status-bar-height);
  z-index: 100;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
}

/* 搜索栏 */
.search-section { padding: 30rpx 40rpx 10rpx; }
.search-input-wrapper {
  background: #FFF;
  height: 80rpx;
  border-radius: 12rpx; /* 改为稍微方正的圆角更高级 */
  display: flex;
  align-items: center;
  padding: 0 30rpx;
  border: 1px solid rgba(74, 111, 165, 0.1);
  box-shadow: 0 4rpx 16rpx rgba(74, 111, 165, 0.04);
}
.search-icon { font-size: 28rpx; color: $color-text-sub; margin-right: 16rpx; }
.custom-input { flex: 1; font-size: 28rpx; color: $color-text-main; }
.clear-btn { padding: 10rpx; color: #CFD8DC; font-size: 24rpx; }

/* 筛选工具栏重构 */
.filter-toolbar {
  padding: 20rpx 40rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.custom-dropdown {
  background: #FFF;
  flex: 1;
  height: 80rpx;
  padding: 0 24rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid rgba(74, 111, 165, 0.15);
  box-shadow: 0 4rpx 12rpx rgba(74, 111, 165, 0.05);
}

.dropdown-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.dropdown-label {
  font-size: 16rpx;
  color: $color-text-sub;
  font-weight: 800;
  letter-spacing: 1px;
  line-height: 1;
  margin-bottom: 4rpx;
}

.dropdown-value {
  font-size: 24rpx;
  color: $color-primary;
  font-weight: 700;
  line-height: 1;
}

.dropdown-arrow { font-size: 18rpx; color: #CFD8DC; }

.mode-capsule {
  display: flex;
  background: rgba(0,0,0,0.04);
  padding: 6rpx;
  border-radius: 12rpx; /* 统一圆角 */
  height: 80rpx;
  box-sizing: border-box;
}

.mode-item {
  padding: 0 30rpx;
  font-size: 24rpx;
  color: $color-text-sub;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  transition: all 0.3s;
}

.mode-item.active {
  background: #FFF;
  color: $color-primary;
  font-weight: 700;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.08);
}

.btn-hover, .tab-hover { opacity: 0.8; transform: scale(0.98); }

/* 字母索引 */
.letter-scroll {
  white-space: nowrap;
  padding: 10rpx 0;
  height: 80rpx;
  border-top: 1px solid rgba(0,0,0,0.02);
}
.letter-item {
  display: inline-block;
  padding: 10rpx 30rpx;
  font-size: 26rpx;
  color: $color-text-sub;
  font-weight: 600;
}
.letter-item.active {
  color: $color-primary;
  position: relative;
  &::after {
    content: '';
    position: absolute;
    bottom: 4rpx;
    left: 30rpx;
    right: 30rpx;
    height: 4rpx;
    background: $color-primary;
    border-radius: 4rpx;
  }
}

/* 列表 */
.list-area { flex: 1; height: 0; }
.list-wrapper { padding: 20rpx 40rpx; }
.word-card {
  background: #FFF;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.02);
  border: 1px solid transparent;
}
.item-hover { border-color: rgba(74, 111, 165, 0.2); background-color: #FAFAFA; }

.card-top { display: flex; align-items: center; margin-bottom: 12rpx; }
.w-word { font-size: 34rpx; font-weight: 700; color: $color-text-main; margin-right: 16rpx; }
.w-tags { flex: 1; display: flex; align-items: center; gap: 12rpx; }
.tag { font-size: 18rpx; padding: 2rpx 10rpx; border-radius: 6rpx; font-weight: 600; }
.level-tag { background: rgba(74, 111, 165, 0.1); color: $color-primary; }
.phonetic-tag { color: $color-text-sub; font-family: 'Times New Roman', serif; }
.audio-icon { font-size: 28rpx; opacity: 0.3; }
.w-trans { font-size: 26rpx; color: #546E7A; line-height: 1.4; display: block; }

/* 状态页脚 */
.status-footer {
  padding: 60rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 22rpx;
  color: $color-text-sub;
}
.loading-spinner {
  width: 32rpx; height: 32rpx;
  border: 3rpx solid rgba(74, 111, 165, 0.2);
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16rpx;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-view { display: flex; flex-direction: column; align-items: center; margin-top: 100rpx; }
.empty-icon { font-size: 80rpx; margin-bottom: 20rpx; opacity: 0.5; }
.ph-style { color: #CFD8DC; font-weight: 300; }
</style>