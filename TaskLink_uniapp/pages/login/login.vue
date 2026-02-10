<template>
  <view class="container">
    <view class="cyber-bg"></view>
    
    <view class="login-box">
      <view class="logo-area">
        <view class="glitch-logo">TASK<br/>LINK</view>
        <text class="sub-text terminal-font">{{ terminalText }}</text>
      </view>

      <view class="form-area">
        <view class="input-group">
          <text class="label">USERNAME // 用户名</text>
          <input class="cyber-input" v-model="username" placeholder="ENTER ID" placeholder-class="ph-style" />
        </view>
        
        <view class="input-group">
          <text class="label">PASSWORD // 密码</text>
          <input class="cyber-input" v-model="password" password placeholder="ACCESS CODE" placeholder-class="ph-style" />
        </view>

        <view v-if="isRegister" class="input-group" style="position: relative;">
          <text class="label">INVITATION CODE // 邀请码</text>
          <input 
            class="cyber-input" 
            v-model="invitationCode" 
            placeholder="6-DIGIT CODE" 
            maxlength="6"
            placeholder-class="ph-style" 
          />
          <view class="get-code-link" @click="showContactInfo">
            <text>GET CODE ></text>
          </view>
        </view>

        <button class="login-btn" @click="handleAction" :loading="loading">
          {{ isRegister ? 'REGISTER // 注册' : 'LOGIN // 接入' }}
        </button>
        
        <view class="toggle-area" @click="toggleMode">
          <text class="toggle-text">
            {{ isRegister ? '<< BACK TO LOGIN' : 'NEW USER REGISTRATION >>' }}
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
// 🔥 引入生命周期钩子
import { ref, onMounted, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';

// 配置你的后端地址

const API_BASE = `http://101.35.132.175:5000`; // Flask 后端

const username = ref('');
const password = ref('');
const invitationCode = ref(''); 
const isRegister = ref(false);
const loading = ref(false);

// --- 🔥 新增：终端打字机逻辑 ---
const terminalText = ref('');
const statusLines = [
  "INITIALIZING NEURAL LINK...",
  "BYPASSING FIREWALLS...",
  "DECRYPTING GATEWAY...",
  "ACCESS GRANTED.",
  "NEURAL CONNECTION ESTABLISHED"
];
let lineIndex = 0;
let charIndex = 0;
let typeTimer = null;

const typeWriter = () => {
  // 如果所有行都打完了，停止
  if (lineIndex >= statusLines.length) return;

  const currentLine = statusLines[lineIndex];
  
  // 逐字显示当前行
  if (charIndex < currentLine.length) {
    // 加个下划线 "_" 模拟光标
    terminalText.value = currentLine.substring(0, charIndex + 1) + "_";
    charIndex++;
    // 随机打字速度，更有真实感
    typeTimer = setTimeout(typeWriter, 30 + Math.random() * 70);
  } else {
    // 这一行打完了，准备下一行
    lineIndex++;
    charIndex = 0;
    // 行与行之间停顿 0.8 秒
    typeTimer = setTimeout(typeWriter, 800);
  }
};

// 页面加载时启动动画
onMounted(() => {
  typeWriter();
});

// 页面卸载时清除定时器，防止内存泄漏
onUnmounted(() => {
  if (typeTimer) clearTimeout(typeTimer);
});
// ----------------------------

const showContactInfo = () => {
  const qqNumber = '2335016055';
  
  uni.showModal({
    title: '获取邀请码',
    content: `请联系管理员获取邀请码\nQQ: ${qqNumber}`,
    confirmText: '复制QQ',
    cancelText: '关闭',
    success: (res) => {
      if (res.confirm) {
        uni.setClipboardData({
          data: qqNumber,
          success: () => {
            uni.showToast({ title: 'QQ号已复制', icon: 'success' });
          }
        });
      }
    }
  });
};

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  username.value = '';
  password.value = '';
  invitationCode.value = '';
};

const handleAction = () => {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请输入账号密码', icon: 'none' });
    return;
  }
  
  if (isRegister.value && !invitationCode.value) {
    uni.showToast({ title: '请输入邀请码', icon: 'none' });
    return;
  }

  loading.value = true;
  
  let postData = {
    username: username.value,
    password: password.value
  };
  
  if (isRegister.value) {
    postData.invitation_code = invitationCode.value;
  }

  const endpoint = isRegister.value ? '/api/register' : '/api/login';

  uni.request({
    url: `${API_BASE}${endpoint}`,
    method: 'POST',
    data: postData,
    success: (res) => {
      loading.value = false;
      
      if (res.data.code === 200) {
        if (!isRegister.value) {
           uni.setStorageSync('userInfo', res.data.data);
           uni.showToast({ title: '接入成功' });
           setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 500);
        } else {
           uni.showToast({ title: '注册成功，请登录', icon: 'success' });
           isRegister.value = false;
           password.value = '';
           invitationCode.value = '';
        }
      } else {
        uni.showToast({ 
            title: res.data.msg || '操作失败', 
            icon: 'none', 
            duration: 3000 
        });
      }
    },
    fail: () => {
      loading.value = false;
      uni.showToast({ title: '无法连接服务器', icon: 'none' });
    }
  });
};
</script>

<style>
/* 保持原有赛博风样式 */
page { background-color: #000; color: #00f3ff; font-family: 'Courier New', monospace; }
.container { height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.cyber-bg { position: absolute; width: 200%; height: 200%; background: radial-gradient(circle, #111 10%, #000 60%); z-index: -1; animation: pulse 5s infinite; }
@keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }

.login-box { width: 80%; }
.logo-area { margin-bottom: 50px; text-align: center; }

/* 🔥 修改：高级故障风 Logo 样式 */
.glitch-logo { 
  font-size: 40px; 
  font-weight: 900; 
  letter-spacing: 5px; 
  color: #fff; 
  position: relative;
  display: inline-block;
  line-height: 1.2;
}

/* 创建两个重影层 */
.glitch-logo::before,
.glitch-logo::after {
  content: "TASK\A LINK"; /* \A 是换行符 */
  white-space: pre;       /* 保持换行 */
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #000;       /* 背景色遮挡，制造撕裂感 */
}

/* 第一层：红色重影 + 随机位移 */
.glitch-logo::before {
  color: #ff003c;
  z-index: -1;
  text-shadow: 2px 0 #ff003c;
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
  animation: glitch-anim-1 3s infinite linear alternate-reverse;
}

/* 第二层：蓝色重影 + 随机位移 */
.glitch-logo::after {
  color: #00f3ff;
  z-index: -2;
  text-shadow: -2px 0 #00f3ff;
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
  animation: glitch-anim-2 2.5s infinite linear alternate-reverse;
}

/* 🔥 新增：关键帧动画 */
@keyframes glitch-anim-1 {
  0% { clip-path: polygon(0 2%, 100% 2%, 100% 5%, 0 5%); transform: translate(2px,0); }
  20% { clip-path: polygon(0 15%, 100% 15%, 100% 15%, 0 15%); transform: translate(-2px,0); }
  40% { clip-path: polygon(0 10%, 100% 10%, 100% 20%, 0 20%); transform: translate(2px,0); }
  60% { clip-path: polygon(0 1%, 100% 1%, 100% 2%, 0 2%); transform: translate(-2px,0); }
  80% { clip-path: polygon(0 33%, 100% 33%, 100% 33%, 0 33%); transform: translate(0,0); }
  100% { clip-path: polygon(0 44%, 100% 44%, 100% 46%, 0 46%); transform: translate(2px,0); }
}

@keyframes glitch-anim-2 {
  0% { clip-path: polygon(0 25%, 100% 25%, 100% 30%, 0 30%); transform: translate(-2px,0); }
  20% { clip-path: polygon(0 3%, 100% 3%, 100% 3%, 0 3%); transform: translate(2px,0); }
  40% { clip-path: polygon(0 5%, 100% 5%, 100% 20%, 0 20%); transform: translate(-2px,0); }
  60% { clip-path: polygon(0 20%, 100% 20%, 100% 20%, 0 20%); transform: translate(0,0); }
  80% { clip-path: polygon(0 40%, 100% 40%, 100% 40%, 0 40%); transform: translate(2px,0); }
  100% { clip-path: polygon(0 52%, 100% 52%, 100% 59%, 0 59%); transform: translate(-2px,0); }
}

/* 🔥 新增：打字机字体样式 */
.terminal-font {
  font-family: 'Courier New', monospace;
  color: #00ff9d; /* 黑客绿 */
  font-weight: bold;
  text-shadow: 0 0 5px #00ff9d;
  min-height: 20px;
}

.sub-text { font-size: 10px; color: #666; letter-spacing: 2px; margin-top: 10px; display: block; }

.input-group { margin-bottom: 25px; border-bottom: 1px solid #333; padding-bottom: 5px; }
.label { font-size: 10px; color: #666; display: block; margin-bottom: 5px; letter-spacing: 1px; }
.cyber-input { color: #fff; font-size: 18px; letter-spacing: 1px; }
.ph-style { color: #333; }

.get-code-link {
  position: absolute;
  right: 0;
  top: 20px; 
  font-size: 12px;
  color: #ff003c; 
  text-decoration: underline;
  z-index: 10;
  padding: 5px;
}
.get-code-link:active { opacity: 0.7; }

.login-btn { 
  background: #00f3ff; color: #000; border-radius: 0; border: none; 
  font-weight: 900; letter-spacing: 1px; margin-top: 40px;
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.4);
  clip-path: polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%);
}
.login-btn:active { background: #fff; }

.toggle-area { margin-top: 20px; text-align: center; padding: 10px; }
.toggle-text { color: #666; font-size: 12px; text-decoration: underline; }
</style>