<template>
  <view class="container">
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

/* =================================================================
   核心业务逻辑 (保持原样，未修改任何接口和参数)
   ================================================================= */
const API_BASE = `http://101.35.132.175:5000`;

const username = ref('');
const password = ref('');
const invitationCode = ref(''); 
const isRegister = ref(false);
const loading = ref(false);
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
/* =================================================================
   视觉样式重构 (莫兰迪极简高级感)
   ================================================================= */

/* 1. 色彩变量 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 辅助文字 */
$color-placeholder: #CFD8DC;
$color-footer: #D7CCC8;    /* 浅棕 */

/* 2. 布局容器 */
.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: $color-bg;
  position: relative;
  overflow: hidden;
}

.login-card {
  width: 650rpx;
  background: $color-card;
  border-radius: 12rpx; /* 适度圆角 */
  padding: 80rpx 60rpx;
  box-sizing: border-box;
  /* 核心：莫兰迪色系弥散阴影 */
  box-shadow: 0 20rpx 60rpx rgba(74, 111, 165, 0.08);
  position: relative;
  z-index: 10;
}

/* 3. 品牌区 */
.brand-section {
  margin-bottom: 80rpx;
  text-align: left;
}

.logo-text {
  display: flex;
  align-items: baseline;
  margin-bottom: 20rpx;
}

.logo-task {
  font-family: 'Inter', sans-serif;
  font-size: 56rpx;
  font-weight: 900;
  color: $color-text-main;
  letter-spacing: -1px;
}

.logo-link {
  font-family: 'Inter', sans-serif;
  font-size: 56rpx;
  font-weight: 400;
  color: $color-accent; /* 珊瑚橙点缀 */
  margin-left: 4rpx;
}

.logo-dot {
  width: 12rpx;
  height: 12rpx;
  background-color: $color-primary;
  border-radius: 50%;
  margin-left: 8rpx;
}

.slogan {
  font-size: 24rpx;
  color: $color-text-sub;
  letter-spacing: 6rpx; /* 增加汉字呼吸感 */
  font-weight: 400;
  opacity: 0.8;
}

/* 4. 表单区 */
.form-section {
  margin-bottom: 60rpx;
}

.input-group {
  margin-bottom: 50rpx;
  position: relative;
}

.input-label {
  font-size: 24rpx;
  color: $color-text-sub;
  font-weight: 500;
  letter-spacing: 2rpx;
  margin-bottom: 12rpx;
  display: block;
  transition: color 0.3s ease;
}

.custom-input {
  width: 100%;
  height: 80rpx;
  font-size: 30rpx;
  color: $color-text-main;
  font-weight: 400;
  border: none;
  background: transparent;
}

.placeholder-style {
  color: $color-placeholder;
  font-weight: 300;
  font-size: 28rpx;
}

/* 动态下划线 */
.input-line {
  width: 100%;
  height: 1px;
  background-color: #E0E0E0;
  margin-top: 4rpx;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 聚焦交互 */
.input-group.is-focused .input-label {
  color: $color-primary;
}

.input-group.is-focused .input-line {
  background-color: $color-primary;
  height: 2px;
}

/* 邀请码特殊布局 */
.input-wrapper {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}
.invitation-input-area {
  flex: 1;
  margin-right: 30rpx;
}
.get-btn {
  font-size: 28rpx;
  color: $color-primary;
  font-weight: 500;
  padding: 10rpx 0;
  margin-bottom: 14rpx; /* 对齐基线 */
  transition: opacity 0.2s;
  letter-spacing: 2rpx;
}
.get-btn-hover { opacity: 0.6; }

/* 5. 按钮与操作 */
.main-btn {
  background-color: $color-primary;
  color: #FFFFFF;
  border-radius: 8rpx;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 500;
  letter-spacing: 8rpx; /* 按钮文字加宽间距 */
  text-indent: 8rpx;
  border: none;
  box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.3);
  transition: all 0.3s ease;
}

.main-btn::after { border: none; }

.arrow-icon {
  margin-left: 8rpx;
  font-weight: 400;
  letter-spacing: 0;
  text-indent: 0;
  transition: transform 0.3s ease;
}

/* 按钮点击态：变珊瑚橙 + 上浮 */
.main-btn-active {
  background-color: $color-accent !important;
  transform: translateY(-4rpx);
  box-shadow: 0 16rpx 40rpx rgba(255, 138, 101, 0.4);
}

.toggle-area {
  margin-top: 40rpx;
  text-align: center;
  padding: 20rpx;
}

.toggle-text {
  font-size: 26rpx;
  color: $color-text-sub;
  border-bottom: 1px dashed $color-text-sub;
  padding-bottom: 4rpx;
  letter-spacing: 1rpx;
}

/* 6. 版权与动画 */
.footer-copyright {
  position: absolute;
  bottom: 40rpx;
  width: 100%;
  text-align: center;
  font-size: 20rpx;
  color: $color-footer;
  letter-spacing: 1rpx;
}

.fade-in-up {
  animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  opacity: 0;
  transform: translateY(60rpx);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>