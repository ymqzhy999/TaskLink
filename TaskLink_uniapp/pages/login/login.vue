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
        <view class="slogan">DESIGN FOR FOCUS.</view>
      </view>

      <view class="form-section">
        <view class="input-group" :class="{ 'is-focused': activeField === 'username' }">
          <text class="input-label">USERNAME</text>
          <input 
            class="custom-input" 
            type="text" 
            placeholder="Please enter username" 
            placeholder-class="placeholder-style"
            @focus="onFocus('username')"
            @blur="onBlur"
            v-model="formData.username"
          />
          <view class="input-line"></view>
        </view>

        <view class="input-group" :class="{ 'is-focused': activeField === 'password' }">
          <text class="input-label">PASSWORD</text>
          <input 
            class="custom-input" 
            type="password" 
            placeholder="Please enter password" 
            placeholder-class="placeholder-style"
            @focus="onFocus('password')"
            @blur="onBlur"
            v-model="formData.password"
          />
          <view class="input-line"></view>
        </view>

        <view v-if="!isLogin" class="input-group invitation-box" :class="{ 'is-focused': activeField === 'invitation' }">
          <view class="input-wrapper">
            <view class="invitation-input-area">
               <text class="input-label">INVITATION</text>
               <input 
                 class="custom-input" 
                 type="text" 
                 placeholder="Code" 
                 placeholder-class="placeholder-style"
                 @focus="onFocus('invitation')"
                 @blur="onBlur"
                 v-model="formData.invitation"
               />
               <view class="input-line"></view>
            </view>
            <view class="get-btn" hover-class="get-btn-hover">获取</view>
          </view>
        </view>
      </view>

      <view class="action-section">
        <button class="main-btn" hover-class="main-btn-active" @tap="handleSubmit">
          <text>{{ isLogin ? 'LOGIN' : 'SIGN UP' }}</text>
          <text class="arrow-icon">→</text>
        </button>
        
        <view class="toggle-area" @tap="toggleMode">
          <text class="toggle-text">{{ isLogin ? 'Create an account' : 'Back to Login' }}</text>
        </view>
      </view>
    </view>

    <view class="footer-copyright">
      © 2026 TaskLink Inc.
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      isLogin: true, // true为登录，false为注册
      activeField: '', // 当前聚焦的输入框
      formData: {
        username: '',
        password: '',
        invitation: ''
      }
    };
  },
  methods: {
    toggleMode() {
      this.isLogin = !this.isLogin;
      // 清空表单或重置状态可在此处添加
    },
    onFocus(field) {
      this.activeField = field;
    },
    onBlur() {
      this.activeField = '';
    },
    handleSubmit() {
      // 模拟交互反馈
      const type = this.isLogin ? '登录' : '注册';
      uni.showToast({
        title: `${type}中...`,
        icon: 'none'
      });
    }
  }
};
</script>

<style lang="scss" scoped>
/* 1. 色彩体系定义 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 辅助文字 */
$color-placeholder: #CFD8DC;
$color-footer: #D7CCC8;    /* 浅棕 */

/* 2. 布局与结构 */
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
  border-radius: 24rpx;
  padding: 80rpx 60rpx;
  box-sizing: border-box;
  /* 卡片阴影：极简悬浮感 */
  box-shadow: 0 20rpx 60rpx rgba(74, 111, 165, 0.08);
  position: relative;
  z-index: 10;
}

/* 3. 品牌区设计 */
.brand-section {
  margin-bottom: 80rpx;
  text-align: left;
}

.logo-text {
  display: flex;
  align-items: baseline;
  margin-bottom: 16rpx;
}

.logo-task {
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 56rpx;
  font-weight: 900;
  color: $color-text-main;
  letter-spacing: -1px;
}

.logo-link {
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 56rpx;
  font-weight: 400;
  color: $color-accent;
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
  font-size: 20rpx;
  color: $color-text-sub;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 500;
}

/* 4. 表单区设计 */
.form-section {
  margin-bottom: 60rpx;
}

.input-group {
  margin-bottom: 50rpx;
  position: relative;
}

.input-label {
  font-size: 22rpx;
  color: $color-text-sub;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 10rpx;
  display: block;
  transition: color 0.3s ease;
}

.custom-input {
  width: 100%;
  height: 80rpx;
  font-size: 32rpx;
  color: $color-text-main;
  font-weight: 400;
  border: none;
  background: transparent;
}

.placeholder-style {
  color: $color-placeholder;
  font-weight: 300;
}

/* 下划线动画 */
.input-line {
  width: 100%;
  height: 1px;
  background-color: #E0E0E0;
  margin-top: 4rpx;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 聚焦状态联动 */
.input-group.is-focused .input-label {
  color: $color-primary;
}

.input-group.is-focused .input-line {
  background-color: $color-primary;
  height: 2px;
  transform: scaleX(1); /* 可选：增加延展动画 */
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
  font-size: 26rpx;
  color: $color-primary;
  font-weight: 600;
  padding: 10rpx 0;
  margin-bottom: 10rpx;
  transition: opacity 0.2s;
}
.get-btn-hover {
  opacity: 0.7;
}

/* 5. 按钮与交互 */
.main-btn {
  background-color: $color-primary;
  color: #FFFFFF;
  border-radius: 8rpx; /* 4px */
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
  letter-spacing: 2px;
  border: none;
  /* 按钮阴影 */
  box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.3);
  transition: all 0.3s ease;
  overflow: hidden;
}

.main-btn::after {
  border: none;
}

.arrow-icon {
  margin-left: 16rpx;
  font-weight: 400;
  transition: transform 0.3s ease;
}

/* 按钮点击态：变珊瑚橙 + 上浮 + 阴影加深 + 箭头位移 */
.main-btn-active {
  background-color: $color-accent !important;
  transform: translateY(-4rpx);
  box-shadow: 0 16rpx 40rpx rgba(255, 138, 101, 0.4);
}

/* H5/小程序中 hover-class 触发时不仅仅改变背景，还需要配合子元素选择器(如果有) */
/* 注意：UniApp hover-class 在松开手后会恢复，这里主要利用active态 */

/* 底部切换链接 */
.toggle-area {
  margin-top: 40rpx;
  text-align: center;
  padding: 20rpx;
}

.toggle-text {
  font-size: 26rpx;
  color: $color-text-sub;
  border-bottom: 1px dashed $color-text-sub;
  padding-bottom: 2rpx;
}

/* 6. 底部版权 */
.footer-copyright {
  position: absolute;
  bottom: 60rpx;
  width: 100%;
  text-align: center;
  font-size: 22rpx;
  color: $color-footer;
  font-weight: 500;
}

/* 7. 进场动画 */
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