<template>
  <view class="container">
    <view class="cyber-bg"></view>
    
    <view class="login-box">
      <view class="logo-area">
        <view class="glitch-logo">TASK<br/>LINK</view>
        <text class="sub-text">{{ t.subtitle }}</text>
      </view>

      <view class="form-area">
        <view class="input-group">
          <text class="label">{{ t.label_user }}</text>
          <input class="cyber-input" v-model="username" :placeholder="t.ph_user" placeholder-class="ph-style" />
        </view>
        
        <view class="input-group">
          <text class="label">{{ t.label_pass }}</text>
          <input class="cyber-input" v-model="password" password :placeholder="t.ph_pass" placeholder-class="ph-style" />
        </view>

        <button class="login-btn" @click="handleLogin" :loading="loading">
          {{ isRegister ? t.btn_reg : t.btn_login }}
        </button>
        
        <view class="toggle-area" @click="isRegister = !isRegister">
          <text class="toggle-text">
            {{ isRegister ? t.link_login : t.link_reg }}
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import messages from '@/utils/language.js'; 

const API_BASE = 'http://192.168.10.26:5000'; // ⚠️ 确认IP
const username = ref('');
const password = ref('');
const isRegister = ref(false);
const loading = ref(false);
const t = ref(messages.zh.login); 

onShow(() => {
  const lang = uni.getStorageSync('lang') || 'zh';
  t.value = messages[lang].login;
});

const handleLogin = () => {
  if (!username.value || !password.value) {
    uni.showToast({ title: 'MISSING DATA', icon: 'none' });
    return;
  }
  loading.value = true;
  const endpoint = isRegister.value ? '/api/register' : '/api/login';

  uni.request({
    url: `${API_BASE}${endpoint}`,
    method: 'POST',
    data: { username: username.value, password: password.value },
    success: (res) => {
      loading.value = false;
      
      // ✅ 成功的情况 (Code 200)
      if (res.data.code === 200) {
        if (!isRegister.value) {
           // 登录成功
           uni.setStorageSync('userInfo', res.data.data);
           uni.showToast({ title: t.value.toast_succ });
           setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 500);
        } else {
           // 注册成功
           uni.showToast({ title: t.value.toast_reg, icon: 'success' });
           isRegister.value = false; // 切回登录模式
        }
      } 
      // ❌ 失败的情况 (Code 400/401/500)
      else {
        // 🔥 关键修改：直接显示后端的 res.data.msg
        // 设置 icon: 'none' 是为了能显示更长的文字（比如复杂的密码规则）
        // 设置 duration: 3000 让用户有足够时间看完提示
        uni.showToast({ 
            title: res.data.msg || '未知错误', 
            icon: 'none',
            duration: 3000 
        });
      }
    },
    fail: () => {
      loading.value = false;
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    }
  });
};
</script>

<style>
/* 保持原有赛博风样式不变 */
page { background-color: #000; color: #00f3ff; font-family: 'Courier New', monospace; }
.container { height: 100vh; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.cyber-bg { position: absolute; width: 200%; height: 200%; background: radial-gradient(circle, #111 10%, #000 60%); z-index: -1; animation: pulse 5s infinite; }
@keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }

.login-box { width: 80%; }
.logo-area { margin-bottom: 50px; text-align: center; }
.glitch-logo { font-size: 40px; font-weight: 900; letter-spacing: 5px; text-shadow: 2px 2px #ff003c, -2px -2px #00f3ff; color: #fff; line-height: 1.2; }
.sub-text { font-size: 10px; color: #666; letter-spacing: 2px; margin-top: 10px; display: block; }

.input-group { margin-bottom: 25px; border-bottom: 1px solid #333; padding-bottom: 5px; }
.label { font-size: 10px; color: #666; display: block; margin-bottom: 5px; letter-spacing: 1px; }
.cyber-input { color: #fff; font-size: 18px; letter-spacing: 1px; }
.ph-style { color: #333; }

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