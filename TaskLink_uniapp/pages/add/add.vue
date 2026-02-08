<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="header-section fade-in">
      <text class="glitch-title" data-text="NEURAL_PLANNER">NEURAL_PLANNER</text>
      <text class="page-desc">// 接入 DeepSeek 戰術核心 // 生成執行協議</text>
    </view>

    <view class="form-container fade-in-up">
      
      <view class="cyber-card glow-card">
        <view class="card-header">
          <view class="decor-line bg-red"></view>
          <text class="section-label">MISSION TARGET (目標鎖定)</text>
          <view class="header-decoration">
            <text class="tech-text">INPUT_STREAM</text>
          </view>
        </view>
        <view class="input-area">
          <textarea 
            class="cyber-textarea" 
            v-model="planForm.goal" 
            placeholder="請輸入您的最終目標..." 
            placeholder-class="cyber-placeholder"
            :maxlength="200"
          />
          <view class="corner-decor tr"></view>
          <view class="corner-decor bl"></view>
        </view>
        <view class="input-footer">
          <text class="char-count">{{ planForm.goal.length }}/200 BYTES</text>
        </view>
      </view>

      <view class="cyber-card">
        <view class="card-header">
          <view class="decor-line bg-yellow"></view>
          <text class="section-label">TIMELINE (執行週期)</text>
        </view>
        
        <view class="slider-container">
          <text class="slider-val">{{ planForm.days }} <text class="unit">DAYS</text></text>
          <slider 
            class="cyber-slider" 
            :value="planForm.days" 
            min="3" 
            max="30" 
            activeColor="#bc13fe" 
            backgroundColor="#333" 
            block-color="#00f3ff" 
            block-size="20"
            @change="(e) => planForm.days = e.detail.value"
          />
          <view class="slider-labels">
            <text>3D</text>
            <text>30D</text>
          </view>
        </view>
      </view>

      <view class="footer-action">
        <button 
          class="submit-btn plan-btn" 
          :class="{ loading: isGenerating }" 
          @click="generatePlan"
          :disabled="isGenerating"
        >
          <text class="btn-content">
            {{ isGenerating ? 'UPLOADING TO NEURAL NET...' : 'INITIALIZE PROTOCOL (生成計劃)' }}
          </text>
          <view class="btn-glitch"></view>
        </button>
      </view>

    </view>

    <view class="generating-overlay" v-if="isGenerating">
      <view class="scanner-line"></view>
      <view class="terminal-window">
        <text class="cmd-line">> ACCESSING CORE...</text>
        <text class="cmd-line">> ANALYZING TARGET: {{ planForm.goal.substring(0, 10) }}...</text>
        <text class="cmd-line blink">> GENERATING TACTICAL PATH...</text>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

// ⚠️ 請確保 IP 正確
const API_BASE = 'http://192.168.10.28:5000'; 

const planForm = ref({ goal: '', days: 7 });
const isGenerating = ref(false);

onShow(() => {
  // 每次進入頁面重置狀態，或者保留上次輸入（這裡選擇重置以獲得清爽體驗）
  // planForm.value = { goal: '', days: 7 };
});

const generatePlan = () => {
  if (!planForm.value.goal.trim()) {
    uni.showToast({ title: '請輸入目標指令', icon: 'none' });
    return;
  }

  const userInfo = uni.getStorageSync('userInfo');
  if (!userInfo) {
    uni.showToast({ title: '用戶未登錄', icon: 'none' });
    return;
  }
  
  isGenerating.value = true;
  
  // 調用後端 DeepSeek 接口
  uni.request({
    url: `${API_BASE}/api/plan/generate`,
    method: 'POST',
    data: { 
      user_id: userInfo.id, 
      goal: planForm.value.goal, 
      days: planForm.value.days 
    },
    timeout: 60000, // 60秒超時，給 AI 足夠思考時間
    success: (res) => {
      if (res.data.code === 200) {
        uni.vibrateShort(); // 震動反饋
        uni.showToast({ title: '協議已生成', icon: 'success' });
        
        // 獲取計劃 ID 並跳轉詳情頁
        const planId = res.data.data.plan_id;
        setTimeout(() => {
          isGenerating.value = false;
          uni.navigateTo({ url: `/pages/plan/detail?id=${planId}` });
        }, 1000);
      } else {
        isGenerating.value = false;
        uni.showToast({ title: '生成失敗: ' + res.data.msg, icon: 'none' });
      }
    },
    fail: (err) => {
      isGenerating.value = false;
      console.error(err);
      uni.showToast({ title: '網絡連接中斷', icon: 'none' });
    }
  });
};
</script>

<style>
page { background-color: #050505; color: #e0e0e0; font-family: 'Courier New', monospace; }
.container { padding: 25px; min-height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 10%, #1a1a2e 0%, #000000 80%); z-index: -1; }

/* 頭部樣式 */
.header-section { margin-bottom: 40px; margin-top: 20px; border-left: 5px solid #00f3ff; padding-left: 20px; }
.glitch-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: 2px; text-shadow: 2px 2px 0px #bc13fe; display: block; }
.page-desc { font-size: 12px; color: #00f3ff; margin-top: 8px; opacity: 0.8; letter-spacing: 1px; }

/* 動畫類 */
.fade-in { animation: fadeIn 0.8s ease-out; }
.fade-in-up { animation: fadeInUp 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

/* 卡片通用 */
.cyber-card { background: rgba(20, 20, 25, 0.8); border: 1px solid rgba(255,255,255,0.1); padding: 25px; margin-bottom: 30px; border-radius: 4px; backdrop-filter: blur(5px); }
.glow-card { border-color: rgba(188, 19, 254, 0.5); box-shadow: 0 0 20px rgba(188, 19, 254, 0.1); }

.card-header { display: flex; align-items: center; margin-bottom: 20px; position: relative; }
.decor-line { width: 4px; height: 18px; margin-right: 12px; }
.bg-red { background: #ff003c; box-shadow: 0 0 8px #ff003c; }
.bg-yellow { background: #f3ff00; box-shadow: 0 0 8px #f3ff00; }
.section-label { font-size: 14px; font-weight: bold; color: #fff; letter-spacing: 1px; }
.header-decoration { position: absolute; right: 0; }
.tech-text { font-size: 10px; color: #444; border: 1px solid #333; padding: 2px 4px; }

/* 輸入區 */
.input-area { position: relative; margin: 10px 0; }
.cyber-textarea { width: 100%; height: 120px; background: #0a0a0a; color: #00f3ff; padding: 15px; font-size: 16px; border: 1px solid #333; box-sizing: border-box; font-weight: bold; line-height: 1.5; }
.cyber-placeholder { color: #333; font-weight: normal; }
.corner-decor { position: absolute; width: 10px; height: 10px; border: 2px solid #bc13fe; pointer-events: none; }
.tr { top: -2px; right: -2px; border-bottom: none; border-left: none; }
.bl { bottom: -2px; left: -2px; border-top: none; border-right: none; }
.input-footer { text-align: right; }
.char-count { font-size: 10px; color: #555; }

/* 滑塊區 */
.slider-container { text-align: center; padding: 10px 0; }
.slider-val { font-size: 48px; font-weight: 900; color: #fff; text-shadow: 0 0 15px rgba(255,255,255,0.3); display: block; margin-bottom: 10px; }
.unit { font-size: 14px; color: #bc13fe; font-weight: normal; }
.cyber-slider { width: 100%; }
.slider-labels { display: flex; justify-content: space-between; color: #666; font-size: 12px; margin-top: 5px; }

/* 按鈕 */
.footer-action { margin-top: 20px; }
.submit-btn { 
  background: linear-gradient(90deg, #bc13fe, #00f3ff); 
  color: #000; 
  font-weight: 900; 
  height: 60px; 
  line-height: 60px; 
  font-size: 18px; 
  border: none; 
  clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
  position: relative;
  overflow: hidden;
}
.submit-btn:active { transform: scale(0.98); opacity: 0.9; }
.submit-btn.loading { filter: grayscale(1); opacity: 0.8; }
.btn-glitch { position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: rgba(255,255,255,0.2); transform: skewX(-20deg); animation: glitch-slide 3s infinite; }
@keyframes glitch-slide { 0% { left: -100%; } 20% { left: 200%; } 100% { left: 200%; } }

/* 生成遮罩 */
.generating-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 999; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.scanner-line { position: absolute; width: 100%; height: 2px; background: #00f3ff; box-shadow: 0 0 20px #00f3ff; animation: scan 2s infinite ease-in-out; top: 0; }
.terminal-window { width: 80%; }
.cmd-line { display: block; color: #00ff9d; font-size: 14px; margin-bottom: 10px; font-family: 'Courier New', monospace; }
.blink { animation: blink 0.5s infinite; }
@keyframes scan { 0% { top: 0; opacity: 1; } 50% { top: 100%; opacity: 0.5; } 100% { top: 0; opacity: 1; } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
</style>