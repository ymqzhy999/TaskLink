<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="bg-layer"></view>

    <view class="login-card fade-in-up">
      <view class="brand-section">
        <view class="logo-text">
          <text class="logo-task">Task</text>
          <text class="logo-link">Link</text>
          <view class="logo-dot"></view>
        </view>
        <view class="slogan">为 专 注 而 设 计</view>
      </view>

      <view class="form-section">
        <view class="input-group" :class="{ 'is-focused': focusField === 'user' }">
          <text class="input-label">账 号</text>
          <input 
            class="custom-input" 
            type="text" 
            placeholder="请输入账号" 
            placeholder-class="placeholder-style"
            v-model="username"
            @focus="focusField = 'user'"
            @blur="focusField = ''"
          />
          <view class="input-line"></view>
        </view>

        <view class="input-group" :class="{ 'is-focused': focusField === 'pass' }">
          <text class="input-label">密 码</text>
          <input 
            class="custom-input" 
            type="password" 
            placeholder="请输入密码" 
            placeholder-class="placeholder-style"
            v-model="password"
            @focus="focusField = 'pass'"
            @blur="focusField = ''"
          />
          <view class="input-line"></view>
        </view>

        <view v-if="isRegister" class="input-group invitation-box" :class="{ 'is-focused': focusField === 'code' }">
          <view class="input-wrapper">
            <view class="invitation-input-area">
               <text class="input-label">邀 请 码</text>
               <input 
                 class="custom-input" 
                 type="text" 
                 placeholder="6位邀请码" 
                 maxlength="6"
                 placeholder-class="placeholder-style"
                 v-model="invitationCode"
                 @focus="focusField = 'code'"
                 @blur="focusField = ''"
               />
               <view class="input-line"></view>
            </view>
            <view class="get-btn" hover-class="get-btn-hover" @click="showContactInfo">获 取</view>
          </view>
        </view>
      </view>

      <view class="action-section">
        <button 
          class="main-btn" 
          hover-class="main-btn-active" 
          :loading="loading"
          @click="handleAction"
        >
          <text>{{ isRegister ? '立 即 注 册' : '登 录' }}</text>
          <text class="arrow-icon">→</text>
        </button>
        
        <view class="toggle-area" @click="toggleMode">
          <text class="toggle-text">{{ isRegister ? '已有账号？返回登录' : '没有账号？注册新用户' }}</text>
        </view>
      </view>
    </view>

    <view class="footer-copyright">
      © 2026 TaskLink Space
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

/* =================================================================
   核心业务逻辑 (保持原样，未修改任何接口和参数)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;

const username = ref('');
const password = ref('');
const invitationCode = ref(''); 
const isRegister = ref(false);
const loading = ref(false);
const isDarkMode = ref(false);

onShow(() => {
  // 同步主题状态
  const theme = uni.getStorageSync('theme');
  isDarkMode.value = theme === 'dark';
});
const focusField = ref(''); // 用于控制UI高亮

const showContactInfo = () => {
  const qqNumber = '2335016055';
  uni.setClipboardData({
    data: qqNumber,
    success: () => uni.showToast({ title: 'QQ已复制', icon: 'none' })
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
    uni.showToast({ title: '请输入完整信息', icon: 'none' });
    return;
  }
  if (isRegister.value && !invitationCode.value) {
    uni.showToast({ title: '请输入邀请码', icon: 'none' });
    return;
  }
  
  loading.value = true;
  let postData = { username: username.value, password: password.value };
  if (isRegister.value) postData.invitation_code = invitationCode.value;
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
           const app = getApp();
           if(app.initSocket) app.initSocket();
           // 使用 reLaunch 避免返回
           uni.reLaunch({ url: '/pages/index/index' });
        } else {
           uni.showToast({ title: '注册成功', icon: 'success' });
           isRegister.value = false;
        }
      } else {
        uni.showToast({ title: res.data.msg || '操作失败', icon: 'none' });
      }
    },
    fail: () => {
      loading.value = false;
      uni.showToast({ title: '网络连接失败', icon: 'none' });
    }
  });
};
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

.container { min-height: 100vh; padding: 0 40rpx; display: flex; flex-direction: column; justify-content: center; position: relative; overflow: hidden; transition: background-color 0.3s; }
.container.dark { background-color: $dark-bg; }

/* 2. Bg Layer */
.bg-layer { position: absolute; top: -200rpx; right: -200rpx; width: 600rpx; height: 600rpx; background: radial-gradient(circle, rgba(74, 111, 165, 0.1) 0%, rgba(245, 245, 240, 0) 70%); border-radius: 50%; z-index: 0; pointer-events: none; transition: opacity 0.3s; }
.container.dark .bg-layer { background: radial-gradient(circle, rgba(74, 111, 165, 0.15) 0%, rgba(18, 18, 18, 0) 70%); }

/* 3. Login Card */
.login-card { background: $color-card; border-radius: 30rpx; padding: 60rpx 40rpx; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.05); position: relative; z-index: 1; transition: background-color 0.3s, box-shadow 0.3s; }
.container.dark .login-card { background: $dark-card; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.3); }

.brand-section { margin-bottom: 60rpx; text-align: center; }
.logo-text { font-size: 60rpx; font-weight: 800; letter-spacing: -2px; margin-bottom: 10rpx; display: flex; align-items: baseline; justify-content: center; }

.logo-task { color: $color-text-main; transition: color 0.3s; }
.container.dark .logo-task { color: $dark-text-main; }

.logo-link { color: $color-primary; }
.logo-dot { width: 12rpx; height: 12rpx; background: $color-accent; border-radius: 50%; margin-left: 4rpx; }

.slogan { font-size: 20rpx; font-weight: 600; color: $color-text-sub; letter-spacing: 4px; text-transform: uppercase; transition: color 0.3s; }
.container.dark .slogan { color: $dark-text-sub; }

/* 4. Form */
.form-section { margin-bottom: 50rpx; }
.input-group { margin-bottom: 40rpx; position: relative; }
.input-label { font-size: 22rpx; font-weight: 700; color: $color-text-sub; margin-bottom: 10rpx; display: block; letter-spacing: 1px; transition: color 0.3s; }
.container.dark .input-label { color: $dark-text-sub; }

.custom-input { height: 80rpx; font-size: 30rpx; color: $color-text-main; font-weight: 600; transition: color 0.3s; }
.container.dark .custom-input { color: $dark-text-main; }

.input-line { height: 2px; background: #F0F0F0; margin-top: 4rpx; transition: background-color 0.3s; }
.container.dark .input-line { background: #333; }

.is-focused .input-line { background: $color-primary; }

/* Invitation Code */
.invitation-box { display: flex; align-items: flex-end; }
.input-wrapper { flex: 1; display: flex; align-items: flex-end; gap: 20rpx; }
.invitation-input-area { flex: 1; }

.get-btn { font-size: 22rpx; font-weight: 700; color: $color-primary; border: 2rpx solid rgba(74, 111, 165, 0.2); padding: 10rpx 24rpx; border-radius: 30rpx; white-space: nowrap; height: fit-content; margin-bottom: 10rpx; transition: all 0.2s; }
.get-btn-hover { background: rgba(74, 111, 165, 0.1); }

/* 5. Actions */
.main-btn { background: $color-text-main; color: #FFF; height: 100rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: space-between; padding: 0 40rpx; font-size: 30rpx; font-weight: 700; box-shadow: 0 10rpx 30rpx rgba(44, 62, 80, 0.2); transition: all 0.3s; border: none; }
.container.dark .main-btn { background: $color-primary; box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.4); }

.main-btn-active { transform: scale(0.98); opacity: 0.9; }
.arrow-icon { font-size: 36rpx; font-weight: 300; }

.toggle-area { margin-top: 30rpx; text-align: center; padding: 20rpx; }
.toggle-text { font-size: 24rpx; color: $color-text-sub; text-decoration: underline; transition: color 0.3s; }
.container.dark .toggle-text { color: $dark-text-sub; }

/* 6. Footer */
.footer-copyright { position: absolute; bottom: 40rpx; left: 0; width: 100%; text-align: center; font-size: 20rpx; color: $color-text-sub; opacity: 0.6; font-family: monospace; transition: color 0.3s; }
.container.dark .footer-copyright { color: $dark-text-sub; }

/* Animation */
.fade-in-up { animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(40rpx); } to { opacity: 1; transform: translateY(0); } }
</style>