<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="header-section fade-in">
      <text class="glitch-title" data-text="阿琪的贾维斯">阿琪的贾维斯</text>
      <text class="page-desc">// 专属战术制定 // 核心已连接</text>
    </view>

    <view class="form-container fade-in-up">
      
      <view class="cyber-card glow-card">
        <view class="card-header">
          <view class="decor-line bg-red"></view>
          <text class="section-label">核心目标</text>
          <view class="header-decoration">
            <text class="tech-text">输入_01</text>
          </view>
        </view>
        <view class="input-area">
          <textarea 
            class="cyber-textarea small" 
            v-model="planForm.goal" 
            placeholder="请输入您要学习或执行的主题..." 
            placeholder-class="cyber-placeholder"
            :maxlength="100"
          />
          <view class="corner-decor tr"></view>
        </view>
      </view>

      <view class="cyber-card glow-blue">
        <view class="card-header">
          <view class="decor-line bg-blue"></view>
          <text class="section-label">最终预期</text>
          <view class="header-decoration">
            <text class="tech-text">输入_02</text>
          </view>
        </view>
        <view class="input-area">
          <textarea 
            class="cyber-textarea" 
            v-model="planForm.expectation" 
            placeholder="请输入您希望达到的具体效果或程度..." 
            placeholder-class="cyber-placeholder"
            :maxlength="200"
          />
          <view class="corner-decor bl"></view>
        </view>
      </view>

      <view class="cyber-card">
        <view class="card-header">
          <view class="decor-line bg-yellow"></view>
          <text class="section-label">执行周期</text>
        </view>
        
        <view class="input-row">
          <input 
            class="cyber-input-num" 
            type="number" 
            v-model="planForm.days" 
            placeholder="7"
          />
          <text class="unit-large">天</text>
        </view>
        <text class="input-tip">// 提示: 超过10天将自动分阶段规划</text>
      </view>

      <view class="footer-action">
        <button 
          class="submit-btn plan-btn" 
          :class="{ loading: isGenerating }" 
          @click="generatePlan"
          :disabled="isGenerating"
        >
          <text class="btn-content">
            {{ isGenerating ? '正在连接贾维斯...' : '呼叫贾维斯 (生成战术)' }}
          </text>
          <view class="btn-glitch"></view>
        </button>
      </view>

    </view>

    <view class="generating-overlay" v-if="isGenerating">
      <view class="scanner-line"></view>
      <view class="terminal-window">
        <view class="terminal-header">
          <view class="status-box">
             <text class="status-dot blink-fast"></text>
             <text>贾维斯连接: 稳定</text>
          </view>
          <text class="timer-display">{{ elapsedTime }}s</text>
        </view>
        <scroll-view scroll-y class="log-scroll" :scroll-top="scrollTop" scroll-with-animation>
          <view v-for="(log, index) in logs" :key="index" class="log-line">
            <text class="log-time">[{{ log.time }}]</text>
            <text class="log-content" :class="log.type">{{ log.text }}</text>
          </view>
          <view class="cursor-block"></view>
        </scroll-view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';

const API_BASE = 'http://192.168.10.28:5000'; 
const planForm = ref({ goal: '', expectation: '', days: 7 });
const isGenerating = ref(false);

const logs = ref([]);
const scrollTop = ref(0);
const elapsedTime = ref('0.0');
let logInterval = null;
let timerInterval = null;
let startTime = 0;

// 🔥 动态生成日志：根据用户输入生成内容，避免重复感
const getProcessingLogs = (goal) => {
  // 截取前8个字，防止日志太长
  const shortGoal = goal.length > 8 ? goal.substring(0, 8) + '...' : goal;
  
  return [
    `正在解构目标语义: "${shortGoal}"`,
    "检索阿琪的记忆扇区 (Sector-7)...",
    `调用战术模块: 针对 [${shortGoal}] 进行优化`,
    "比对 12,049 份相似战术案例...",
    "检测到潜在难点，正在调整学习曲线...",
    "注入贾维斯逻辑协议 (Ver 4.0)...",
    "构建每日任务依赖树...",
    "正在计算时间片分配...",
    "模拟执行流程 (Iteration 3/10)...",
    "优化知识点颗粒度...",
    "生成 Markdown 渲染层...",
    "校验逻辑一致性...",
    "正在压缩数据包...",
    "等待核心服务器响应..."
  ];
};

const generatePlan = () => {
  if (!planForm.value.goal.trim()) return uni.showToast({ title: '请输入核心目标', icon: 'none' });
  const d = parseInt(planForm.value.days);
  if (!d || d <= 0) return uni.showToast({ title: '请输入有效天数', icon: 'none' });

  const userInfo = uni.getStorageSync('userInfo');
  if (!userInfo) return uni.showToast({ title: '用户未登录', icon: 'none' });
  
  isGenerating.value = true;
  logs.value = []; 
  // 传入目标，启动动态日志
  startCyberLogs(planForm.value.goal); 
  
  uni.request({
    url: `${API_BASE}/api/plan/generate`,
    method: 'POST',
    data: { 
      user_id: userInfo.id, 
      goal: planForm.value.goal, 
      days: d,
      expectation: planForm.value.expectation
    },
    timeout: 120000, 
    success: (res) => {
      stopCyberLogs(); 
      if (res.data.code === 200) {
        addLog("✅ 战术协议生成完毕。", 'success');
        uni.vibrateShort();
        setTimeout(() => {
          isGenerating.value = false;
          uni.navigateTo({ url: `/pages/plan/detail?id=${res.data.data.plan_id}` });
        }, 1500);
      } else {
        isGenerating.value = false;
        uni.showToast({ title: '生成失败: ' + res.data.msg, icon: 'none' });
      }
    },
    fail: (err) => {
      stopCyberLogs();
      isGenerating.value = false;
      uni.showToast({ title: '网络连接中断', icon: 'none' });
    }
  });
};

const startCyberLogs = (goal) => {
  startTime = Date.now();
  timerInterval = setInterval(() => { elapsedTime.value = ((Date.now() - startTime) / 1000).toFixed(1); }, 100);
  
  addLog("正在唤醒贾维斯核心...", 'info');
  addLog("生物特征认证...通过", 'info');
  
  // 生成针对该目标的日志池
  const dynamicPool = getProcessingLogs(goal);
  let poolIndex = 0;
  
  // 🔴 速度放慢到 2.5秒 一条，避免刷屏太快，缓解等待焦虑
  logInterval = setInterval(() => {
    
    if (poolIndex < dynamicPool.length) {
      // 顺序播放动态日志
      addLog(dynamicPool[poolIndex], 'normal');
      poolIndex++;
    } else {
      // 没词了？开始随机产生 "深度思考" 噪音
      const noise = [
        `内存分配: 0x${Math.floor(Math.random()*9999).toString(16)}`, 
        "等待神经元响应...", 
        "深度推理中 (Thinking)...", 
        "同步率: 99.9%"
      ];
      addLog(noise[Math.floor(Math.random() * noise.length)], 'dim');
    }
  }, 2500); 
};

const addLog = (text, type = 'normal') => {
  const timeStr = `T+${((Date.now() - startTime) / 1000).toFixed(1)}s`;
  logs.value.push({ time: timeStr, text: text, type: type });
  // 保持少量，看起来更清爽
  if (logs.value.length > 12) logs.value.shift(); 
  // 滚动动画
  setTimeout(() => { scrollTop.value = logs.value.length * 100; }, 100);
};

const stopCyberLogs = () => {
  if (logInterval) clearInterval(logInterval);
  if (timerInterval) clearInterval(timerInterval);
};

onUnmounted(() => { stopCyberLogs(); });
</script>

<style>
/* 保持背景样式 */
page { background-color: #050505; color: #e0e0e0; font-family: 'Courier New', monospace; }
.container { padding: 25px; min-height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 10%, #1a1a2e 0%, #000000 80%); z-index: -1; }

.header-section { margin-bottom: 30px; margin-top: 10px; border-left: 5px solid #00f3ff; padding-left: 20px; }
.glitch-title { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: 2px; text-shadow: 2px 2px 0px #bc13fe; display: block; }
.page-desc { font-size: 12px; color: #00f3ff; margin-top: 8px; opacity: 0.8; letter-spacing: 1px; }

.cyber-card { background: rgba(20, 20, 25, 0.8); border: 1px solid rgba(255,255,255,0.1); padding: 20px; margin-bottom: 25px; border-radius: 4px; backdrop-filter: blur(5px); }
.glow-card { border-color: rgba(255, 0, 60, 0.5); box-shadow: 0 0 15px rgba(255, 0, 60, 0.1); }
.glow-blue { border-color: rgba(0, 243, 255, 0.5); box-shadow: 0 0 15px rgba(0, 243, 255, 0.1); }
.card-header { display: flex; align-items: center; margin-bottom: 15px; position: relative; }
.decor-line { width: 4px; height: 18px; margin-right: 12px; }
.bg-red { background: #ff003c; box-shadow: 0 0 8px #ff003c; }
.bg-blue { background: #00f3ff; box-shadow: 0 0 8px #00f3ff; }
.bg-yellow { background: #f3ff00; box-shadow: 0 0 8px #f3ff00; }
.section-label { font-size: 14px; font-weight: bold; color: #fff; letter-spacing: 1px; }
.header-decoration { position: absolute; right: 0; }
.tech-text { font-size: 10px; color: #444; border: 1px solid #333; padding: 2px 4px; }

.input-area { position: relative; margin: 5px 0; }
.cyber-textarea { width: 100%; background: #0a0a0a; color: #00f3ff; padding: 15px; font-size: 14px; border: 1px solid #333; box-sizing: border-box; font-weight: bold; line-height: 1.5; }
.cyber-textarea.small { height: 80px; } 
.cyber-textarea:not(.small) { height: 100px; }
.cyber-placeholder { color: #333; font-weight: normal; }
.corner-decor { position: absolute; width: 10px; height: 10px; border: 2px solid #bc13fe; pointer-events: none; }
.tr { top: -2px; right: -2px; border-bottom: none; border-left: none; }
.bl { bottom: -2px; left: -2px; border-top: none; border-right: none; }

/* 🔥 数字输入框样式优化 */
.input-row { display: flex; align-items: baseline; justify-content: center; padding: 10px 0; }
.cyber-input-num { 
  font-size: 40px; 
  color: #fff; 
  font-weight: 900; 
  background: transparent; 
  border: none; 
  border-bottom: 2px solid #bc13fe; 
  width: 200px; /* 加宽到 200px */
  height: 60px; 
  line-height: 60px;
  text-align: center; 
  margin-right: 10px; 
  font-family: 'Courier New';
}
.unit-large { font-size: 14px; color: #bc13fe; }
.input-tip { font-size: 10px; color: #666; display: block; text-align: center; margin-top: 5px; }

.footer-action { margin-top: 10px; }
.submit-btn { background: linear-gradient(90deg, #bc13fe, #00f3ff); color: #000; font-weight: 900; height: 60px; line-height: 60px; font-size: 18px; border: none; clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px); position: relative; overflow: hidden; }
.submit-btn:active { transform: scale(0.98); opacity: 0.9; }
.submit-btn.loading { filter: grayscale(1); opacity: 0.8; }
.btn-glitch { position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: rgba(255,255,255,0.2); transform: skewX(-20deg); animation: glitch-slide 3s infinite; }
@keyframes glitch-slide { 0% { left: -100%; } 20% { left: 200%; } 100% { left: 200%; } }

/* 终端样式升级 */
.generating-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); z-index: 999; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.scanner-line { position: absolute; width: 100%; height: 2px; background: #00f3ff; box-shadow: 0 0 20px #00f3ff; animation: scan 2s infinite ease-in-out; top: 0; }
@keyframes scan { 0% { top: 0; opacity: 1; } 50% { top: 100%; opacity: 0.5; } 100% { top: 0; opacity: 1; } }
.terminal-window { width: 85%; height: 300px; background: #050505; border: 1px solid #00f3ff; padding: 15px; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0, 243, 255, 0.2); font-family: 'Courier New', monospace; }
.terminal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px; color: #00f3ff; font-size: 12px; font-weight: bold; }
.status-box { display: flex; align-items: center; }
.status-dot { width: 8px; height: 8px; background: #00ff9d; border-radius: 50%; margin-right: 8px; }
.blink-fast { animation: blink 0.5s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.timer-display { color: #bc13fe; font-weight: bold; }
.log-scroll { flex: 1; height: 0; }
.log-line { font-size: 12px; margin-bottom: 8px; line-height: 1.4; display: block; word-wrap: break-word; }
.log-time { color: #555; margin-right: 8px; font-size: 10px; }

/* 日志颜色分类 */
.log-content { color: #aaa; }
.log-content.success { color: #00ff9d; font-weight: bold; }
.log-content.info { color: #00f3ff; }
.log-content.dim { color: #444; font-style: italic; }
.cursor-block { width: 10px; height: 14px; background: #00f3ff; animation: blink 1s infinite; display: inline-block; }
.fade-in { animation: fadeIn 0.8s ease-out; }
.fade-in-up { animation: fadeInUp 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>