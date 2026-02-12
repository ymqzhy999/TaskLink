<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="nav-bar">
      <view class="nav-left">
        <view class="back-btn" @click="goBack">
          <text class="icon">⇇</text> BACK
        </view>
        
        <picker 
          mode="selector" 
          :range="levelOptions" 
          range-key="label" 
          :value="currentLevelIndex" 
          @change="handleLevelChange"
        >
          <view class="level-badge">
            <text class="tag">LVL.</text>{{ levelOptions[currentLevelIndex].value }}
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <view class="nav-right">
        <view class="dict-btn" @click="goToDict">
           <text class="search-icon">🔍</text> 词库
        </view>
        <text class="progress-info">{{ currentIndex + 1 }} / {{ vocabList.length }}</text>
      </view>
    </view>

    <view class="progress-container">
      <view class="progress-fill" :style="{ width: ((currentIndex + 1) / vocabList.length) * 100 + '%' }"></view>
    </view>

    <view class="main-content" v-if="currentWord && !isFinished">
      <view class="word-card" :class="{ 'card-active': showAnswer }">
        
        <text class="word-main">{{ currentWord.word }}</text>
        <text class="word-phonetic" v-if="currentWord.phonetic">[{{ currentWord.phonetic }}]</text>
        
        <view class="details-area" v-if="showAnswer">
          <view class="divider"></view>
          <text class="meaning-text">{{ currentWord.translation }}</text>
          
          <view class="sentence-container">
            <view class="sentence-header">
              <text class="ai-label"></text>
              <text class="status-text" v-if="loadingSentence">LOADING...</text>
            </view>
            <view class="sentence-content">
              <view v-if="loadingSentence" class="loading-box">
                DATA RETRIEVAL IN PROGRESS...
              </view>
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
             <text class="syn-label">SAME_WORDS</text>
             <view class="syn-list">
               <view class="syn-tag" v-for="(syn, idx) in aiSentence.synonyms" :key="idx">
                 {{ syn }}
               </view>
             </view>
           </view>

        </view>

        <view class="unlock-overlay" v-else @click="revealAnswer">
           <text class="unlock-text">点击查看释义</text>
        </view>
      </view>

      <view class="action-footer" v-if="showAnswer">
        <view class="rating-grid">
          <view class="rating-btn b-0" @click="submitResult(0)">
            <text class="r-val">0</text>
            <text class="r-txt">忘记</text>
          </view>
          <view class="rating-btn b-3" @click="submitResult(3)">
            <text class="r-val">3</text>
            <text class="r-txt">模糊</text>
          </view>
          <view class="rating-btn b-4" @click="submitResult(4)">
            <text class="r-val">4</text>
            <text class="r-txt">认识</text>
          </view>
          <view class="rating-btn b-5" @click="submitResult(5)">
            <text class="r-val">5</text>
            <text class="r-txt">精通</text>
          </view>
        </view>
      </view>
    </view>

    <view class="finished-state" v-if="isFinished">
      <view class="finish-hex">✔</view>
      <text class="f-title">MISSION COMPLETE</text>
      <button class="cyber-button-rect" @click="handleReload">再来一组</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const API_BASE = `http://101.35.132.175:5000`; 
const vocabList = ref([]);
const currentIndex = ref(0);
const currentWord = ref(null);
const isFinished = ref(false);
const showAnswer = ref(false);

// 🔥 修正后的等级映射 (前端显示 vs 后端数据库代码)
const levelOptions = [
    { label: '初中 (MiddleSchool)', value: 'JUNIOR' },
    { label: '高中 (HighSchool)', value: 'SENIOR' },
    { label: '四级 (CET-4)', value: 'CET4' },
    { label: '六级 (CET-6)', value: 'CET6' },
    { label: '托福 (TOEFL)', value: 'TOEFL' }
];
// 默认选中四级 (下标2)
const currentLevelIndex = ref(2); 

const aiSentence = ref(null);
const loadingSentence = ref(false);

const getToken = () => uni.getStorageSync('userInfo')?.token || '';

// 切换等级
const handleLevelChange = (e) => {
    currentLevelIndex.value = e.detail.value;
    
    // 重置状态
    vocabList.value = [];
    isFinished.value = false;
    currentWord.value = null;
    currentIndex.value = 0;
    
    // 切换等级时，优先复习旧词 (forceNew=false)
    fetchDueVocab(false); 
};

// 获取单词数据
const fetchDueVocab = (forceNew = false) => {
    uni.showLoading({ title: '加载中...' });
    const user = uni.getStorageSync('userInfo');
    const level = levelOptions[currentLevelIndex.value].value;
    
    console.log(`正在请求: Level=${level}, ForceNew=${forceNew}`); 

    uni.request({
        // 🔥 传递 force_new 参数
        url: `${API_BASE}/api/vocab/due?user_id=${user.id}&level=${level}&force_new=${forceNew}`,
        header: { 'Authorization': getToken() },
        success: (res) => {
            uni.hideLoading();
            if (res.data.code === 200) {
                vocabList.value = res.data.data;
                console.log("获取到单词数量:", vocabList.value.length);

                if (vocabList.value.length > 0) {
                    // 有词 -> 开始学习
                    currentIndex.value = 0;
                    isFinished.value = false;
                    loadWord(0);
                } else {
                    // 没词 -> 完成状态
                    isFinished.value = true;
                    if (forceNew) {
                        uni.showToast({ title: '该等级词库已空！', icon: 'none' });
                    }
                }
            }
        },
        fail: () => {
            uni.hideLoading();
            uni.showToast({title: '网络错误', icon: 'none'});
        }
    });
};

// 再来一组 (强制拉新)
const handleReload = () => {
    fetchDueVocab(true);
};

// 加载单个单词
const loadWord = (index) => {
    if (index >= vocabList.value.length) {
        isFinished.value = true;
        currentWord.value = null;
        return;
    }
    currentIndex.value = index;
    currentWord.value = vocabList.value[index];
    showAnswer.value = false;
    aiSentence.value = null; // 重置 AI 数据
    isFinished.value = false;
};

// 显示答案
const revealAnswer = () => {
    showAnswer.value = true;
};

// 提交评分
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
    loadWord(currentIndex.value + 1);
};

// 获取 AI 例句和近义词
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

// 跳转词库页
const goToDict = () => {
    uni.navigateTo({ url: '/pages/vocab/vocab_list' });
};

const goBack = () => uni.navigateBack();

onMounted(() => fetchDueVocab());
</script>

<style scoped>
/* 基础样式 (无动画) */
page { background-color: #050505; color: #00f3ff; font-family: 'Courier New', monospace; height: 100vh; overflow: hidden; }
.container { height: 100%; display: flex; flex-direction: column; position: relative; }

/* 静态背景 */
.cyber-bg { position: fixed; width: 100%; height: 100%; background: radial-gradient(circle, #111 0%, #000 100%); z-index: -1; }

/* 导航栏 */
.nav-bar { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    /* 🔥 核心修改：大幅增加顶部内边距 */
    padding: 140rpx 30rpx 20rpx; 
    border-bottom: 1px solid #1a1a1a; 
}

.nav-left, .nav-right { display: flex; align-items: center; gap: 20rpx; }
.back-btn { color: #666; font-size: 24rpx; }
.level-badge { background: #111; border: 1px solid #00ff9d; color: #00ff9d; padding: 6rpx 16rpx; font-size: 20rpx; border-radius: 4rpx; }

/* 词库按钮 */
.dict-btn { 
    font-size: 22rpx; color: #fff; background: #222; 
    padding: 8rpx 20rpx; border-radius: 4rpx; border: 1px solid #444;
}
.search-icon { font-size: 20rpx; margin-right: 6rpx; }
.progress-info { font-size: 20rpx; color: #444; }

/* 进度条 */
.progress-container { position: relative; height: 6rpx; background: #111; margin: 0 30rpx; margin-top: 20rpx; border-radius: 3rpx; }
.progress-fill { height: 100%; background: #00f3ff; transition: width 0.2s; }

/* 主内容区 */
.main-content { flex: 1; padding: 40rpx; display: flex; flex-direction: column; justify-content: center; }

/* 单词卡片 (静态) */
.word-card { 
    background: #0a0a0a; border: 1px solid #333; padding: 60rpx 40rpx; 
    position: relative; border-radius: 8rpx; min-height: 500rpx; 
}
.card-active { border-color: #00f3ff; }

/* 单词字体大小调整 */
.word-main { font-size: 64rpx; font-weight: bold; color: #fff; text-align: center; display: block; margin-bottom: 10rpx; letter-spacing: 2rpx; }
.word-phonetic { font-size: 28rpx; color: #00f3ff; text-align: center; display: block; margin-top: 5rpx; opacity: 0.8; font-family: sans-serif; }

.unlock-overlay { 
    margin-top: 100rpx; display: flex; flex-direction: column; align-items: center; 
    gap: 20rpx; padding: 40rpx; border: 1px dashed #333; border-radius: 8rpx;
}
.unlock-icon { font-size: 40rpx; color: #444; }
.unlock-text { font-size: 22rpx; color: #666; }

.details-area { margin-top: 40rpx; padding-top: 40rpx; border-top: 1px solid #222; }
.meaning-text { font-size: 34rpx; color: #00ff9d; text-align: center; display: block; margin-bottom: 40rpx; font-weight: bold; line-height: 1.6; }

/* AI 盒子 */
.sentence-container { background: #0e0e0e; border: 1px solid #222; padding: 25rpx; margin-bottom: 20rpx; border-radius: 6rpx; }
.sentence-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15rpx; }
.ai-label { font-size: 20rpx; color: #666; font-weight: bold; }
.status-text { font-size: 18rpx; color: #00f3ff; }

.en-s { font-size: 28rpx; color: #ccc; display: block; margin-bottom: 10rpx; font-style: italic; line-height: 1.4; }
.cn-s { font-size: 24rpx; color: #666; display: block; }
.gen-trigger { font-size: 22rpx; color: #444; text-align: center; padding: 20rpx; border: 1px dashed #333; border-radius: 4rpx; }
.loading-box { color: #444; font-size: 22rpx; text-align: center; padding: 10rpx; }

/* 🔥 近义词样式 */
.synonyms-box {
  margin-top: 30rpx;
  padding-top: 20rpx;
  border-top: 1px dashed #222;
}
.syn-label {
  font-size: 20rpx; color: #666; font-weight: bold; display: block; margin-bottom: 15rpx;
}
.syn-list { display: flex; flex-wrap: wrap; gap: 15rpx; }
.syn-tag {
  font-size: 24rpx; color: #00ff9d; background: rgba(0, 255, 157, 0.1);
  border: 1px solid #00ff9d; padding: 6rpx 20rpx; border-radius: 4rpx; opacity: 0.8;
}

/* 评分按钮 */
.action-footer { margin-top: 40rpx; }
.rating-grid { display: flex; justify-content: space-between; gap: 15rpx; }
.rating-btn { 
    flex: 1; height: 110rpx; display: flex; flex-direction: column; align-items: center; justify-content: center; 
    background: #111; border: 1px solid #333; border-radius: 6rpx; 
}
.rating-btn:active { background: #222; }

/* 分数颜色区分 */
.b-0 { border-bottom: 3px solid #ff003c; } /* 忘记 */
.b-3 { border-bottom: 3px solid #ffaa00; } /* 模糊 */
.b-4 { border-bottom: 3px solid #00f3ff; } /* 认识 */
.b-5 { border-bottom: 3px solid #00ff9d; } /* 精通 */

.r-val { font-size: 32rpx; font-weight: bold; color: #fff; margin-bottom: 4rpx; }
.r-txt { font-size: 22rpx; color: #888; }

.finished-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.finish-hex { font-size: 80rpx; color: #00ff9d; margin-bottom: 40rpx; }
.f-title { font-size: 36rpx; color: #00ff9d; margin-bottom: 60rpx; letter-spacing: 2rpx; }
.cyber-button-rect { 
    background: #00f3ff; color: #000; border: none; padding: 20rpx 80rpx; 
    font-size: 28rpx; font-weight: bold; border-radius: 4rpx; 
}
</style>