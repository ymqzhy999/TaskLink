<template>
  <view class="container">
    <view class="nav-header">
      <view class="nav-left" @click="goBack">
        <text class="back-icon">←</text>
        <text class="back-text">Back</text>
      </view>
      
<view class="level-selector-wrapper">
  <picker mode="selector" :range="levelOptions" range-key="label" :value="currentLevelIndex" @change="handleLevelChange">
    <view class="custom-selector">
      <text class="selector-label">LEVEL</text>
      <text class="selector-value">{{ levelOptions[currentLevelIndex].label }}</text>
      <text class="selector-arrow">▾</text>
    </view>
  </picker>
</view>

      <view class="nav-right" @click="goToDict">
        <view class="icon-btn search-btn">
          <text>🔍</text>
        </view>
      </view>
    </view>

    <view class="progress-section">
      <view class="progress-track">
        <view class="progress-fill" :style="{ width: ((currentIndex + 1) / vocabList.length) * 100 + '%' }"></view>
      </view>
      <text class="progress-num">{{ currentIndex + 1 }} / {{ vocabList.length }}</text>
    </view>

    <view class="card-container" v-if="currentWord && !isFinished">
      <view class="word-card" :class="{ 'flipped': showAnswer }">
        <view class="card-front">
          <text class="word-text">{{ currentWord.word }}</text>
          <view class="phonetic-box" @click.stop="playAudio">
            <text class="phonetic-text" v-if="currentWord.phonetic">/{{ currentWord.phonetic }}/</text>
            <view class="audio-icon">🔊</view>
          </view>
          
          <view class="tap-hint" v-if="!showAnswer" @click="revealAnswer">
            <text>点击查看释义</text>
          </view>
        </view>

        <view class="card-back" v-if="showAnswer">
          <view class="divider"></view>
          <text class="meaning-text">{{ currentWord.translation }}</text>
          
          <view class="ai-section">
            <view class="ai-header">
              <text class="ai-tag">SENTENCE</text>
              <text class="ai-status" v-if="loadingSentence">Loading...</text>
            </view>
            
            <view class="ai-content">
              <block v-if="aiSentence">
                <text class="en-sentence">"{{ aiSentence.en }}"</text>
                <text class="cn-sentence">{{ aiSentence.cn }}</text>
              </block>
              <view v-else class="ai-placeholder" @click="getAiSentence">
                <text>✨ 点击生成 AI 例句 & 近义词</text>
              </view>
            </view>
          </view>

          <view class="synonyms-section" v-if="aiSentence && aiSentence.synonyms && aiSentence.synonyms.length > 0">
            <text class="syn-title">SAMEWORDS</text>
            <view class="syn-chips">
              <text class="syn-chip" v-for="(syn, idx) in aiSentence.synonyms" :key="idx">{{ syn }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view class="footer-control" v-if="!isFinished">
      <view class="rating-bar" v-if="showAnswer">
        <view class="rate-btn r-0" @click="submitResult(0)">
          <text class="rate-num">0</text>
          <text class="rate-label">忘记</text>
        </view>
        <view class="rate-btn r-3" @click="submitResult(3)">
          <text class="rate-num">3</text>
          <text class="rate-label">模糊</text>
        </view>
        <view class="rate-btn r-4" @click="submitResult(4)">
          <text class="rate-num">4</text>
          <text class="rate-label">认识</text>
        </view>
        <view class="rate-btn r-5" @click="submitResult(5)">
          <text class="rate-num">5</text>
          <text class="rate-label">精通</text>
        </view>
      </view>

      <view class="nav-btns" v-else>
        <view class="nav-btn prev" :class="{ disabled: currentIndex === 0 }" @click="prevWord">
          <text>Previous</text>
        </view>
        <view class="nav-btn save" :class="{ disabled: sessionWords.length === 0 }" @click="saveProgress">
          <text>Save Progress</text>
        </view>
      </view>
    </view>

    <view class="finished-view" v-if="isFinished">
      <view class="finish-icon">🎉</view>
      <text class="finish-title">Session Complete</text>
      <text class="finish-sub">本次训练已完成，请保持节奏。</text>
      <button class="restart-btn" @click="handleReload">再来一组</button>
    </view>

    <view class="history-fab" @click="openHistoryDrawer">
      <text>📜</text>
    </view>

    <view class="drawer-mask" v-if="showHistory" @click="closeHistoryDrawer"></view>
    <view class="history-drawer" :class="{ 'drawer-open': showHistory }">
      <view class="drawer-header">
        <text class="drawer-title">History Logs</text>
        <view class="close-icon" @click="closeHistoryDrawer">✕</view>
      </view>
      
      <scroll-view scroll-y class="drawer-body" @scrolltolower="loadMoreHistory">
        <view v-if="historySessions.length === 0" class="empty-state">
          <text>暂无训练记录</text>
        </view>
        
        <view 
          class="history-item" 
          v-for="(item, index) in historySessions" 
          :key="index"
          @click="goToSessionDetail(item.id)"
          @longpress="deleteSession(item.id, index)"
        >
          <view class="item-main">
            <text class="item-date">{{ item.created_at }}</text>
            <view class="item-tags">
              <text class="tag-level">{{ item.level }}</text>
              <text class="tag-status" :class="item.status === 1 ? 'done' : 'saved'">
                {{ item.status === 1 ? 'Done' : 'Saved' }}
              </text>
            </view>
          </view>
          <view class="item-count">
            <text class="count-num">{{ item.total_words }}</text>
            <text class="count-label">Words</text>
          </view>
        </view>
        
        <view class="load-more-text" v-if="historySessions.length > 0">
          {{ hasMoreHistory ? '加载更多...' : '- End -' }}
        </view>
      </scroll-view>
    </view>

  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`; 
const vocabList = ref([]);
const currentIndex = ref(0);
const currentWord = ref(null);
const isFinished = ref(false);
const showAnswer = ref(false);

const sessionWords = ref([]); 
const showHistory = ref(false);
const historySessions = ref([]);
const historyPage = ref(1);
const hasMoreHistory = ref(true);
const isLoadingHistory = ref(false);

const aiSentence = ref(null);
const loadingSentence = ref(false);

const levelOptions = [
    { label: "初中", value:"JUNIOR" },
    { label: "高中", value:"SENIOR" },
    { label: '四级 (CET-4)', value: 'CET4' },
    { label: '六级 (CET-6)', value: 'CET6' },
    { label: '托福 (TOEFL)', value: 'TOEFL' }
];
const currentLevelIndex = ref(0); 

const getToken = () => uni.getStorageSync('userInfo')?.token || '';

const playAudio = () => {
    const word = currentWord.value.word;
    const url = currentWord.value.audio_url || `https://dict.youdao.com/dictvoice?audio=${word}&type=2`;
    const audio = uni.createInnerAudioContext();
    audio.src = url;
    audio.play();
};

const saveProgress = () => {
    if (sessionWords.value.length === 0) return;
    
    uni.showLoading({ title: 'Saving...' });
    const user = uni.getStorageSync('userInfo');
    const level = levelOptions[currentLevelIndex.value].value;

    uni.request({
        url: `${API_BASE}/api/training/save`,
        method: 'POST',
        header: { 'Authorization': getToken() },
        data: {
            user_id: user.id,
            level: level,
            status: isFinished.value ? 1 : 0,
            details: sessionWords.value
        },
        success: (res) => {
            uni.hideLoading();
            if (res.data.code === 200) {
                uni.showToast({ title: 'Saved', icon: 'success' });
                sessionWords.value = [];
            } else {
                uni.showToast({ title: 'Error', icon: 'none' });
            }
        },
        fail: () => {
            uni.hideLoading();
            uni.showToast({ title: 'Network Error', icon: 'none' });
        }
    });
};

const submitResult = (quality) => {
    const user = uni.getStorageSync('userInfo');
    uni.request({
        url: `${API_BASE}/api/vocab/review`,
        method: 'POST',
        header: { 'Authorization': getToken() },
        data: {
            user_id: user.id,
            word_id: currentWord.value.id,
            quality: quality
        }
    });

    sessionWords.value.push({
        word_id: currentWord.value.id,
        word: currentWord.value.word,
        trans: currentWord.value.translation,
        quality: quality
    });

    loadWord(currentIndex.value + 1);
};

const getAiSentence = () => {
    if (!currentWord.value || loadingSentence.value) return;
    loadingSentence.value = true;
    
    uni.request({
        url: `${API_BASE}/api/vocab/sentence`,
        method: 'POST',
        header: { 'Authorization': getToken() },
        data: { word: currentWord.value.word },
        success: (res) => {
            loadingSentence.value = false;
            if (res.data.code === 200) {
                aiSentence.value = res.data.data;
            }
        },
        fail: () => { loadingSentence.value = false; }
    });
};

const loadMoreHistory = () => {
    if (!hasMoreHistory.value || isLoadingHistory.value) return;
    
    isLoadingHistory.value = true;
    const user = uni.getStorageSync('userInfo');
    
    uni.request({
        url: `${API_BASE}/api/training/history`,
        method: 'GET',
        data: {
            user_id: user.id,
            page: historyPage.value,
            page_size: 6 
        },
        success: (res) => {
            if (res.data.code === 200) {
                const newItems = res.data.data;
                historySessions.value = [...historySessions.value, ...newItems];
                
                hasMoreHistory.value = res.data.has_more;
                if (hasMoreHistory.value) {
                    historyPage.value++;
                }
            }
        },
        complete: () => {
            isLoadingHistory.value = false;
        }
    });
};

const openHistoryDrawer = () => {
    showHistory.value = true;
    historyPage.value = 1;        
    historySessions.value = [];  
    hasMoreHistory.value = true; 
    
    uni.showLoading({ title: 'Loading...' });
    loadMoreHistory(); 
    setTimeout(() => uni.hideLoading(), 500);
};

const closeHistoryDrawer = () => showHistory.value = false;

const goToSessionDetail = (sessionId) => {
    uni.navigateTo({ url: `/pages/vocab/session_detail?id=${sessionId}` });
};

const deleteSession = (sessionId, index) => {
    uni.showModal({
        title: 'Delete',
        content: 'Delete this record?',
        confirmColor: '#EF5350',
        success: (res) => {
            if (res.confirm) {
                const user = uni.getStorageSync('userInfo');
                uni.request({
                    url: `${API_BASE}/api/training/delete`,
                    method: 'POST',
                    data: { session_id: sessionId, user_id: user.id },
                    success: () => {
                        historySessions.value.splice(index, 1);
                        uni.showToast({ title: 'Deleted' });
                    }
                });
            }
        }
    });
};

const handleLevelChange = (e) => {
    currentLevelIndex.value = e.detail.value;
    fetchDueVocab(false); 
};

const fetchDueVocab = (forceNew = false) => {
    uni.showLoading({ title: 'Syncing...' });
    const user = uni.getStorageSync('userInfo');
    const level = levelOptions[currentLevelIndex.value].value;
    
    uni.request({
        url: `${API_BASE}/api/vocab/due?user_id=${user.id}&level=${level}&force_new=${forceNew}`,
        header: { 'Authorization': getToken() },
        success: (res) => {
            uni.hideLoading();
            if (res.data.code === 200) {
                vocabList.value = res.data.data;
                sessionWords.value = []; 
                if (vocabList.value.length > 0) {
                    currentIndex.value = 0;
                    isFinished.value = false;
                    loadWord(0);
                } else {
                    isFinished.value = true;
                }
            }
        }
    });
};

const loadWord = (index) => {
    if (index >= vocabList.value.length) {
        isFinished.value = true;
        if (sessionWords.value.length > 0) saveProgress();
        return;
    }
    currentIndex.value = index;
    currentWord.value = vocabList.value[index];
    showAnswer.value = false;
    aiSentence.value = null;
};

const prevWord = () => {
    if (currentIndex.value > 0) loadWord(currentIndex.value - 1);
};

const revealAnswer = () => showAnswer.value = true;
const handleReload = () => fetchDueVocab(true);
const goToDict = () => uni.navigateTo({ url: '/pages/vocab/vocab_list' });
const goBack = () => uni.navigateBack();

onMounted(() => fetchDueVocab());
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
  overflow: hidden;
}

.container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 2. 顶部导航 */
.nav-header {
  height: 88rpx;
  padding-top: var(--status-bar-height);
  padding-left: 30rpx;
  padding-right: 30rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: $color-bg;
}

.nav-left {
  display: flex;
  align-items: center;
  color: $color-primary;
}
.back-icon { font-size: 36rpx; margin-right: 4rpx; margin-top: -4rpx; }
.back-text { font-size: 28rpx; font-weight: 500; }

/* 替换原有的 .level-picker 相关样式 */

.level-selector-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
}

.custom-selector {
  background-color: #FFFFFF;
  border: 1px solid rgba(74, 111, 165, 0.2); /* 莫兰迪蓝淡边框 */
  padding: 10rpx 24rpx;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column; /* 纵向排列，上方小标签，下方是大值 */
  align-items: center;
  min-width: 180rpx;
  position: relative;
  box-shadow: 0 4rpx 12rpx rgba(74, 111, 165, 0.05);
  transition: all 0.3s ease;

  &:active {
    transform: scale(0.97);
    background-color: #F0F4F8;
  }
}

.selector-label {
  font-size: 18rpx;
  color: #95A5A6; /* 辅助灰色 */
  font-weight: 700;
  letter-spacing: 2rpx;
  margin-bottom: 4rpx;
}

.selector-value {
  font-size: 26rpx;
  color: #4A6FA5; /* 莫兰迪蓝主色 */
  font-weight: 600;
}

.selector-arrow {
  position: absolute;
  right: 12rpx;
  bottom: 8rpx;
  font-size: 18rpx;
  color: #CFD8DC;
}
.level-text { font-size: 24rpx; font-weight: 600; color: $color-text-main; margin-right: 8rpx; }
.picker-arrow { font-size: 18rpx; color: $color-text-sub; }

.icon-btn {
  width: 60rpx;
  height: 60rpx;
  background: $color-card;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}

/* 3. 进度条 */
.progress-section {
  padding: 20rpx 40rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.progress-track {
  flex: 1;
  height: 6rpx;
  background: #E0E0E0;
  border-radius: 3rpx;
  margin-right: 20rpx;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: $color-primary;
  border-radius: 3rpx;
  transition: width 0.3s ease;
}
.progress-num { font-size: 22rpx; color: $color-text-sub; font-weight: 500; }



.word-text {
  font-size: 64rpx;
  font-weight: 700;
  color: $color-text-main;
  text-align: center;
  display: block;
  margin-bottom: 20rpx;
}

.phonetic-box {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
}
.phonetic-text { font-size: 28rpx; color: $color-text-sub; margin-right: 12rpx; font-family: 'Times New Roman', serif; }
.audio-icon { font-size: 32rpx; opacity: 0.6; }

.tap-hint {
  margin-top: auto;
  margin-bottom: auto;
  text-align: center;
  padding: 30rpx;
  border: 2rpx dashed #E0E0E0;
  border-radius: 12rpx;
}
.tap-hint text { font-size: 24rpx; color: $color-text-sub; }

/* 背面内容 */
.card-back {
  animation: fadeIn 0.4s ease;
}
.divider { height: 1px; background: #F0F0F0; margin: 20rpx 0 40rpx; }
.meaning-text { 
  font-size: 32rpx; 
  color: $color-primary; 
  font-weight: 600; 
  text-align: center; 
  display: block; 
  margin-bottom: 40rpx;
  line-height: 1.5;
}

.ai-section {
  background: #FAFAFA;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}
.ai-header { display: flex; justify-content: space-between; margin-bottom: 10rpx; }
.ai-tag { font-size: 20rpx; color: $color-text-sub; font-weight: 700; }
.ai-status { font-size: 20rpx; color: $color-primary; }

.en-sentence { font-size: 26rpx; color: $color-text-main; font-style: italic; display: block; margin-bottom: 8rpx; line-height: 1.4; }
.cn-sentence { font-size: 24rpx; color: $color-text-sub; }
.ai-placeholder { text-align: center; color: $color-primary; font-size: 24rpx; padding: 10rpx; }

.synonyms-section { margin-top: 20rpx; }
.syn-title { font-size: 20rpx; color: $color-text-sub; font-weight: 700; margin-bottom: 8rpx; display: block; }
.syn-chips { display: flex; flex-wrap: wrap; gap: 10rpx; }
.syn-chip { 
  font-size: 22rpx; 
  color: $color-text-main; 
  background: #F0F0F0; 
  padding: 4rpx 16rpx; 
  border-radius: 8rpx; 
}/* --- 找到并修改以下样式 --- */

/* --- 核心优化：紧凑且具有呼吸感的卡片样式 --- */

.card-container {
  padding: 30rpx 40rpx;
  display: flex;
  flex-direction: column;
  /* 移除原本的 min-height 750rpx，改为自适应居中 */
  justify-content: center;
  align-items: center;
  flex: 1; /* 让容器占据中间区域 */
}

.word-card {
  width: 100%;
  background: $color-card;
  border-radius: 32rpx;
  box-shadow: 0 12rpx 48rpx rgba(74, 111, 165, 0.08);
  /* 调整内边距：上下紧凑，左右适中 */
  padding: 50rpx 50rpx 40rpx; 
  display: flex;
  flex-direction: column;
  position: relative;
  transition: all 0.3s ease;
  
  /* 设置一个更合理的自适应高度范围 */
  height: auto;
  min-height: 480rpx; /* 保证卡片最基础的体量感 */
  max-height: 65vh; 
  overflow-y: auto; /* 内容过多时内部滚动 */
}

/* 单词主体：缩小底部间距 */
.word-text {
  font-size: 68rpx; 
  font-weight: 700;
  color: $color-text-main;
  text-align: center;
  display: block;
  letter-spacing: 1rpx;
  margin-bottom: 12rpx;
}

/* 音标：大幅缩小底部间距，让释义靠上来 */
.phonetic-box {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx; 
}

.phonetic-text {
  font-size: 30rpx;
  color: $color-text-sub;
  font-family: 'Inter', sans-serif;
}

/* 分割线：紧凑化 */
.divider { 
  height: 1px; 
  background: #F5F5F5; 
  margin: 10rpx 0 24rpx; 
}

/* 释义：通过行高撑起质感，而不是靠物理间距 */
.meaning-text { 
  font-size: 34rpx; 
  color: $color-primary; 
  font-weight: 600; 
  text-align: center; 
  display: block; 
  margin-bottom: 24rpx; /* 缩小与例句的距离 */
  line-height: 1.6;
}

/* AI 例句：同样紧凑处理 */
.ai-section {
  background: #F8F9FA;
  padding: 24rpx 30rpx;
  border-radius: 16rpx;
  margin-top: 10rpx;
}

/* --- 底部评分区：向上贴近卡片 --- */
.footer-control {
  padding: 10rpx 40rpx 60rpx; /* 减小顶部 padding，让按钮组更靠近卡片 */
  z-index: 5;
}

.rating-bar { 
  display: flex; 
  justify-content: space-between; 
  gap: 16rpx; 
  /* 移除可能存在的过大 margin */
}

.rate-btn { 
  flex: 1; 
  height: 96rpx; 
  border-radius: 16rpx; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center;
  background: $color-card;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}

/* 历史球：位置调优，防止视觉重合感过强 */
.history-fab {
  position: fixed;
  right: 40rpx;
  bottom: 210rpx; /* 稍微下调，避开卡片主视觉 */
  width: 90rpx;
  height: 90rpx;
  background: rgba(255, 255, 255, 0.9); 
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 24rpx rgba(0,0,0,0.08);
  font-size: 40rpx;
  z-index: 100;
  border: 1px solid rgba(74, 111, 165, 0.1);
}

.word-card {
  background: $color-card;
  border-radius: 32rpx;
  box-shadow: 0 12rpx 48rpx rgba(74, 111, 165, 0.1);
  /* 增加内边距，让文字离边框远一点 */
  padding: 80rpx 60rpx; 
  display: flex;
  flex-direction: column;
  position: relative;
  transition: all 0.3s ease;
  
  /* 允许卡片高度随内容增长，但最高不超过屏幕的 60% */
  height: auto;
  max-height: 60vh; 
}

/* 单词主体：加大字号并增加字间距 */
.word-text {
  font-size: 72rpx; 
  font-weight: 700;
  color: $color-text-main;
  text-align: center;
  display: block;
  letter-spacing: 2rpx;
  margin-bottom: 24rpx;
}

/* 音标：增加上下间距 */
.phonetic-box {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 60rpx; 
}

.phonetic-text {
  font-size: 32rpx;
  color: $color-text-sub;
  font-family: 'Inter', sans-serif;
}

/* 释义：关键在于行高 */
.meaning-text { 
  font-size: 36rpx; 
  color: $color-primary; 
  font-weight: 600; 
  text-align: center; 
  display: block; 
  margin-bottom: 40rpx;
  /* 增加行高，防止中文挤在一起 */
  line-height: 1.8; 
  letter-spacing: 1px;
}

/* 例句区域：优化阅读间距 */
.ai-section {
  background: #F8F9FA;
  padding: 32rpx;
  border-radius: 16rpx;
  margin-top: 20rpx;
}

.en-sentence { 
  font-size: 28rpx; 
  color: $color-text-main; 
  display: block; 
  margin-bottom: 16rpx; 
  /* 英文行高 */
  line-height: 1.6; 
}

.cn-sentence { 
  font-size: 26rpx; 
  color: $color-text-sub; 
  line-height: 1.6;
}


/* 5. 底部控制栏 */
.footer-control {
  padding: 30rpx 40rpx 60rpx;
}

.rating-bar { display: flex; justify-content: space-between; gap: 20rpx; }
.rate-btn { 
  flex: 1; 
  height: 100rpx; 
  border-radius: 16rpx; 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  justify-content: center;
  background: $color-card;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}
.rate-num { font-size: 32rpx; font-weight: 700; margin-bottom: 4rpx; }
.rate-label { font-size: 20rpx; color: #FFF; padding: 2rpx 8rpx; border-radius: 6rpx; }

.r-0 .rate-num { color: #EF5350; }
.r-0 .rate-label { background: #EF5350; }

.r-3 .rate-num { color: #FFCA28; }
.r-3 .rate-label { background: #FFCA28; }

.r-4 .rate-num { color: #42A5F5; }
.r-4 .rate-label { background: #42A5F5; }

.r-5 .rate-num { color: #66BB6A; }
.r-5 .rate-label { background: #66BB6A; }

.nav-btns { display: flex; justify-content: space-between; gap: 30rpx; }
.nav-btn {
  flex: 1;
  height: 90rpx;
  border-radius: 45rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 600;
}
.nav-btn.prev { background: #E0E0E0; color: $color-text-sub; }
.nav-btn.save { background: $color-accent; color: #FFF; box-shadow: 0 6rpx 20rpx rgba(255, 138, 101, 0.3); }
.nav-btn.disabled { opacity: 0.5; pointer-events: none; }

/* 6. 完成状态 */
.finished-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.finish-icon { font-size: 80rpx; margin-bottom: 20rpx; }
.finish-title { font-size: 36rpx; font-weight: 700; color: $color-text-main; margin-bottom: 10rpx; }
.finish-sub { font-size: 24rpx; color: $color-text-sub; margin-bottom: 50rpx; }
.restart-btn { 
  background: $color-primary; 
  color: #FFF; 
  padding: 20rpx 80rpx; 
  border-radius: 40rpx; 
  font-size: 28rpx; 
  box-shadow: 0 6rpx 20rpx rgba(74, 111, 165, 0.3);
}

/* 7. 历史记录 */
.history-fab {
  position: fixed;
  right: 40rpx;
  bottom: 180rpx;
  width: 90rpx;
  height: 90rpx;
  background: $color-card;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.1);
  font-size: 40rpx;
  z-index: 100;
}

.drawer-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.3);
  z-index: 200;
}

.history-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 60vh;
  background: #F9F9F9;
  border-radius: 30rpx 30rpx 0 0;
  z-index: 201;
  transform: translateY(100%);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
}
.drawer-open { transform: translateY(0); }

.drawer-header {
  padding: 30rpx 40rpx;
  background: #FFF;
  border-radius: 30rpx 30rpx 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.drawer-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; }
.close-icon { font-size: 32rpx; color: $color-text-sub; padding: 10rpx; }

.drawer-body { flex: 1; padding: 20rpx 40rpx; box-sizing: border-box; }

.history-item {
  background: #FFF;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.02);
}

.item-main { display: flex; flex-direction: column; }
.item-date { font-size: 26rpx; font-weight: 600; color: $color-text-main; margin-bottom: 8rpx; }
.item-tags { display: flex; gap: 10rpx; }
.tag-level { font-size: 20rpx; background: #F0F0F0; color: $color-text-sub; padding: 2rpx 8rpx; border-radius: 4rpx; }
.tag-status { font-size: 20rpx; padding: 2rpx 8rpx; border-radius: 4rpx; }
.tag-status.done { background: rgba(76, 175, 80, 0.1); color: #4CAF50; }
.tag-status.saved { background: rgba(255, 152, 0, 0.1); color: #FF9800; }

.item-count { text-align: right; }
.count-num { font-size: 36rpx; font-weight: 700; color: $color-primary; display: block; }
.count-label { font-size: 20rpx; color: $color-text-sub; }

.empty-state, .load-more-text {
  text-align: center;
  color: $color-text-sub;
  font-size: 24rpx;
  padding: 40rpx;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>