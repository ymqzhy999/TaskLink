<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="nav-header">
      <view class="back-btn" @click="goBack">
        <text class="icon">❮</text> BACK
      </view>
      
      <picker mode="selector" :range="levelOptions" range-key="label" :value="currentLevelIndex" @change="handleLevelChange">
        <view class="level-selector">
          <text class="level-val">{{ levelOptions[currentLevelIndex].value }}</text>
          <text class="level-arrow">▼</text>
        </view>
      </picker>

      <view class="dict-btn" @click="goToDict">
         <text class="icon">🔍</text>
      </view>
    </view>

    <view class="progress-track">
      <view class="progress-bar" :style="{ width: ((currentIndex + 1) / vocabList.length) * 100 + '%' }"></view>
    </view>

    <view class="tool-bar">
      <view class="tool-left">
         <view class="tool-btn prev" :class="{ disabled: currentIndex === 0 }" @click="prevWord">
            <text>◀ PREV</text>
         </view>
      </view>

      <text class="progress-text">
        <text class="curr">{{ currentIndex + 1 }}</text> / {{ vocabList.length }}
      </text>

      <view class="tool-right">
         <view class="tool-btn save" :class="{ disabled: isFinished || sessionWords.length === 0 }" @click="saveProgress">
           <text>💾 SAVE</text>
         </view>
      </view>
    </view>

    <view class="main-content" v-if="currentWord && !isFinished">
      <view class="word-card" :class="{ 'card-active': showAnswer }">
        <text class="word-main">{{ currentWord.word }}</text>
        
        <view class="phonetic-row" @click.stop="playAudio">
           <text class="word-phonetic" v-if="currentWord.phonetic">[{{ currentWord.phonetic }}]</text>
           <text class="audio-icon">🔊</text>
        </view>
        
        <view class="details-area" v-if="showAnswer">
          <view class="divider"></view>
          <text class="meaning-text">{{ currentWord.translation }}</text>
          
          <view class="sentence-container">
            <view class="sentence-header">
              <text class="ai-label">SENTENCE</text>
              <text class="status-text" v-if="loadingSentence">COMPUTING...</text>
            </view>
            <view class="sentence-content">
              <view v-if="loadingSentence" class="loading-box">DATA RETRIEVAL IN PROGRESS...</view>
              <block v-else-if="aiSentence">
                <text class="en-s">"{{ aiSentence.en }}"</text>
                <text class="cn-s">{{ aiSentence.cn }}</text>
              </block>
              <view v-else class="gen-trigger" @click="getAiSentence">
                 [ 点击生成 AI 例句 & 近义词 ]
              </view>
            </view>
          </view>
          
          <view class="synonyms-box" v-if="aiSentence && aiSentence.synonyms && aiSentence.synonyms.length > 0">
             <text class="syn-label">SYNONYMS</text>
             <view class="syn-list">
               <view class="syn-tag" v-for="(syn, idx) in aiSentence.synonyms" :key="idx">{{ syn }}</view>
             </view>
           </view>
        </view>

        <view class="unlock-overlay" v-else @click="revealAnswer">
           <text class="unlock-text">点击查看释义</text>
        </view>
      </view>

      <view class="action-footer" v-if="showAnswer">
        <view class="rating-grid">
          <view class="rating-btn b-0" @click="submitResult(0)"><text class="r-val">0</text><text class="r-txt">忘记</text></view>
          <view class="rating-btn b-3" @click="submitResult(3)"><text class="r-val">3</text><text class="r-txt">模糊</text></view>
          <view class="rating-btn b-4" @click="submitResult(4)"><text class="r-val">4</text><text class="r-txt">认识</text></view>
          <view class="rating-btn b-5" @click="submitResult(5)"><text class="r-val">5</text><text class="r-txt">精通</text></view>
        </view>
      </view>
    </view>

    <view class="finished-state" v-if="isFinished">
      <view class="finish-hex">✔</view>
      <text class="f-title">MISSION COMPLETE</text>
      <button class="cyber-button-rect" @click="handleReload">再来一组</button>
    </view>

    <view class="history-fab" @click="openHistoryDrawer"><text>📜</text></view>
    <view class="drawer-mask" v-if="showHistory" @click="closeHistoryDrawer"></view>
    
    <view class="history-drawer" :class="{ open: showHistory }">
      <view class="drawer-header">
        <text class="dh-title">HISTORY LOGS</text>
        <text class="dh-close" @click="closeHistoryDrawer">✕</text>
      </view>
      
      <scroll-view scroll-y class="drawer-list" @scrolltolower="loadMoreHistory" lower-threshold="100">
        <view v-if="historySessions.length === 0" class="empty-log">暂无打卡记录</view>
        
        <view 
          class="session-item" 
          v-for="(item, index) in historySessions" 
          :key="index"
          @click="goToSessionDetail(item.id)"
          @longpress="deleteSession(item.id, index)"
        >
          <view class="s-left">
            <text class="s-date">{{ item.created_at }}</text>
            <text class="s-level">{{ item.level }}</text>
          </view>
          <view class="s-right">
             <text class="s-count">{{ item.total_words }} Words</text>
             <text class="s-status">{{ item.status === 1 ? 'DONE' : 'SAVED' }}</text>
          </view>
        </view>
        
        <view class="loading-more" v-if="historySessions.length > 0" @click="loadMoreHistory">
           {{ hasMoreHistory ? '⬇ 点击加载更多 (LOAD MORE)' : '--- END ---' }}
        </view>
        
        <view style="height: calc(80rpx + env(safe-area-inset-bottom));"></view>
      </scroll-view>
    </view>

  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const API_BASE = `http://101.35.132.175:5000`; // 请确保地址正确
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
const isLoadingHistory = ref(false); // 加载锁

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
    
    uni.showLoading({ title: 'SAVING...' });
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
                uni.showToast({ title: '已保存到历史', icon: 'success' });
                sessionWords.value = [];
            } else {
                uni.showToast({ title: '保存失败', icon: 'none' });
            }
        },
        fail: () => {
            uni.hideLoading();
            uni.showToast({ title: '网络错误', icon: 'none' });
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

// --- 历史记录分页逻辑 (修复版) ---
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
    
    uni.showLoading({ title: '加载记录...' });
    loadMoreHistory(); 
    setTimeout(() => uni.hideLoading(), 500);
};

const closeHistoryDrawer = () => showHistory.value = false;

const goToSessionDetail = (sessionId) => {
    uni.navigateTo({ url: `/pages/vocab/session_detail?id=${sessionId}` });
};

const deleteSession = (sessionId, index) => {
    uni.showModal({
        title: 'DELETE?',
        content: '确认删除这条打卡记录吗？',
        success: (res) => {
            if (res.confirm) {
                const user = uni.getStorageSync('userInfo');
                uni.request({
                    url: `${API_BASE}/api/training/delete`,
                    method: 'POST',
                    data: { session_id: sessionId, user_id: user.id },
                    success: () => {
                        historySessions.value.splice(index, 1);
                        uni.showToast({ title: '已删除' });
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
    uni.showLoading({ title: 'SYNC...' });
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

<style scoped>
/* 基础设置 */
page { background-color: #050505; color: #00f3ff; font-family: 'Courier New', monospace; height: 100vh; overflow: hidden; }
.container { height: 100%; display: flex; flex-direction: column; position: relative; }
.cyber-bg { position: fixed; width: 100%; height: 100%; background: radial-gradient(circle, #111 0%, #000 100%); z-index: -1; }

/* 1. 顶部导航栏 */
.nav-header { 
  display: flex; justify-content: space-between; align-items: center; 
  padding: 100rpx 30rpx 20rpx; 
  background: rgba(5, 5, 5, 0.9);
  z-index: 10;
}
.back-btn { color: #666; font-size: 24rpx; display: flex; align-items: center; }
.back-btn .icon { font-size: 30rpx; margin-right: 6rpx; }

.level-selector { 
  display: flex; align-items: center; justify-content: center;
  border: 1px solid #00f3ff; border-radius: 4rpx; 
  padding: 6rpx 20rpx; background: rgba(0, 243, 255, 0.1);
}
.level-val { font-size: 24rpx; font-weight: bold; color: #fff; margin-right: 10rpx; }
.level-arrow { font-size: 20rpx; color: #00f3ff; }

.dict-btn { width: 60rpx; height: 60rpx; display: flex; align-items: center; justify-content: center; border: 1px solid #333; border-radius: 50%; background: #111; }
.dict-btn .icon { font-size: 28rpx; }

/* 2. 进度条 */
.progress-track { height: 4rpx; background: #222; width: 100%; margin-top: 0; }
.progress-bar { height: 100%; background: #00f3ff; transition: width 0.3s; box-shadow: 0 0 10rpx #00f3ff; }

/* 3. 工具控制栏 */
.tool-bar { 
  display: flex; justify-content: space-between; align-items: center; 
  padding: 20rpx 40rpx; border-bottom: 1px solid #1a1a1a; 
  background: #080808;
}
.tool-btn { 
  font-size: 22rpx; font-weight: bold; padding: 10rpx 20rpx; border-radius: 4rpx; 
  display: flex; align-items: center; border: 1px solid #444; color: #888;
}
.tool-btn.prev:active { background: #222; color: #fff; }
.tool-btn.save { border-color: #ffaa00; color: #ffaa00; }
.tool-btn.save:active { background: rgba(255, 170, 0, 0.1); }
.tool-btn.disabled { opacity: 0.3; pointer-events: none; border-color: #333; color: #444; }

.progress-text { font-size: 24rpx; color: #444; font-family: sans-serif; }
.progress-text .curr { color: #00f3ff; font-size: 32rpx; font-weight: bold; }

/* 主内容区 */
.main-content { flex: 1; padding: 30rpx 40rpx; display: flex; flex-direction: column; justify-content: center; }
.word-card { background: #0a0a0a; border: 1px solid #333; padding: 60rpx 40rpx; position: relative; border-radius: 8rpx; min-height: 500rpx; display: flex; flex-direction: column; align-items: center; }
.card-active { border-color: #00f3ff; box-shadow: 0 0 20rpx rgba(0, 243, 255, 0.1); }
.word-main { font-size: 64rpx; font-weight: bold; color: #fff; text-align: center; display: block; margin-bottom: 10rpx; letter-spacing: 2rpx; }

.phonetic-row { display: flex; align-items: center; gap: 15rpx; margin-top: 10rpx; opacity: 0.8; }
.word-phonetic { font-size: 28rpx; color: #00f3ff; font-family: sans-serif; }
.audio-icon { font-size: 32rpx; }

.unlock-overlay { margin-top: auto; margin-bottom: auto; padding: 40rpx; border: 1px dashed #333; border-radius: 8rpx; width: 80%; text-align: center; }
.unlock-text { font-size: 22rpx; color: #666; }

.details-area { width: 100%; margin-top: 40rpx; padding-top: 40rpx; border-top: 1px solid #222; }
.meaning-text { font-size: 34rpx; color: #00ff9d; text-align: center; display: block; margin-bottom: 30rpx; font-weight: bold; line-height: 1.6; }

.sentence-container { background: #0e0e0e; border: 1px solid #222; padding: 20rpx; margin-bottom: 20rpx; border-radius: 6rpx; }
.sentence-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.ai-label { font-size: 20rpx; color: #666; font-weight: bold; }
.status-text { font-size: 18rpx; color: #00f3ff; }
.en-s { font-size: 26rpx; color: #ccc; display: block; margin-bottom: 8rpx; font-style: italic; line-height: 1.4; }
.cn-s { font-size: 22rpx; color: #666; display: block; }
.gen-trigger { font-size: 22rpx; color: #444; text-align: center; padding: 15rpx; border: 1px dashed #333; }
.synonyms-box { margin-top: 20rpx; padding-top: 15rpx; border-top: 1px dashed #222; }
.syn-label { font-size: 20rpx; color: #666; font-weight: bold; margin-bottom: 10rpx; display: block; }
.syn-list { display: flex; flex-wrap: wrap; gap: 10rpx; }
.syn-tag { font-size: 22rpx; color: #00ff9d; background: rgba(0, 255, 157, 0.1); border: 1px solid #00ff9d; padding: 4rpx 12rpx; border-radius: 4rpx; }

/* 底部评分 */
.action-footer { margin-top: 40rpx; }
.rating-grid { display: flex; justify-content: space-between; gap: 15rpx; }
.rating-btn { flex: 1; height: 100rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #111; border: 1px solid #333; border-radius: 6rpx; }
.b-0 { border-bottom: 3px solid #ff003c; } 
.b-3 { border-bottom: 3px solid #ffaa00; } 
.b-4 { border-bottom: 3px solid #00f3ff; } 
.b-5 { border-bottom: 3px solid #00ff9d; } 
.r-val { font-size: 32rpx; font-weight: bold; color: #fff; margin-bottom: 4rpx; }
.r-txt { font-size: 20rpx; color: #888; }

/* 历史记录浮窗 */
.finished-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.finish-hex { font-size: 80rpx; color: #00ff9d; margin-bottom: 40rpx; }
.f-title { font-size: 36rpx; color: #00ff9d; margin-bottom: 60rpx; letter-spacing: 2rpx; }
.cyber-button-rect { background: #00f3ff; color: #000; border: none; padding: 20rpx 80rpx; font-size: 28rpx; font-weight: bold; border-radius: 4rpx; }

.history-fab { position: fixed; right: 40rpx; bottom: 100rpx; width: 80rpx; height: 80rpx; background: rgba(0,0,0,0.8); border: 1px solid #00f3ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 36rpx; box-shadow: 0 0 15rpx rgba(0, 243, 255, 0.3); z-index: 100; }
.drawer-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 101; }
.history-drawer { position: fixed; bottom: 0; left: 0; width: 100%; height: 60vh; background: #0f0f0f; border-top: 2px solid #00f3ff; z-index: 102; transform: translateY(100%); transition: transform 0.3s; display: flex; flex-direction: column; }
.history-drawer.open { transform: translateY(0); }
.drawer-header { padding: 20rpx 30rpx; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; background: #111; }
.dh-title { color: #00f3ff; font-weight: bold; font-size: 28rpx; }
.dh-close { color: #666; font-size: 32rpx; padding: 10rpx; }

.drawer-list { 
  flex: 1; 
  padding: 20rpx; 
  box-sizing: border-box; 
  height: 0; 
  width: 100%;
}

.session-item { display: flex; justify-content: space-between; align-items: center; padding: 25rpx; margin-bottom: 15rpx; background: #161616; border-left: 3rpx solid #444; }
.session-item:active { background: #222; }
.s-date { color: #fff; font-size: 24rpx; font-weight: bold; display: block; margin-bottom: 6rpx; }
.s-level { color: #666; font-size: 20rpx; background: #000; padding: 2rpx 8rpx; border-radius: 4rpx; }
.s-count { color: #00f3ff; font-size: 28rpx; font-weight: bold; display: block; margin-bottom: 6rpx; text-align: right; }
.s-status { color: #888; font-size: 20rpx; }
.loading-more { text-align: center; color: #444; padding: 20rpx; font-size: 20rpx; }
.empty-log { text-align: center; color: #444; padding: 50rpx; font-size: 24rpx; }
</style>