<template>
  <view class="container">
    <view class="profile-header-bg"></view>

    <view class="profile-card fade-in">
      <view class="avatar-section" @click="uploadAvatar">
        <view class="avatar-wrapper">
          <image 
            class="avatar" 
            :src="getAvatarUrl()" 
            mode="aspectFill"
          ></image>
          <view class="camera-icon">
            <text>📷</text>
          </view>
        </view>
      </view>
      
      <view class="info-section">
        <text class="username">{{ userInfo.username || 'Unknown' }}</text>
        <text class="user-id">ID: {{ userInfo.id ? '#' + String(userInfo.id).padStart(4, '0') : '--' }}</text>
        <view class="role-badge" :class="{ 'admin': userInfo.role === 1 }">
          <text>{{ userInfo.role === 1 ? 'ADMINISTRATOR' : 'MEMBER' }}</text>
        </view>
      </view>
    </view>

    <view class="menu-list slide-up">
      
      <view class="menu-group">
        <view class="menu-item" @click="openPasswordModal">
          <view class="item-left">
            <view class="icon-box blue">
              <text class="menu-icon">🔐</text>
            </view>
            <text class="menu-text">修改密码</text> 
          </view>
          <text class="arrow">></text>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item" @click="startVocabularyTraining">
          <view class="item-left">
            <view class="icon-box orange">
              <text class="menu-icon">📚</text>
            </view>
            <text class="menu-text">每日单词</text>
          </view>
          <text class="arrow">></text>
        </view>

        <view class="menu-item" @click="goToHelp">
          <view class="item-left">
            <view class="icon-box green">
              <text class="menu-icon">💡</text>
            </view>
            <text class="menu-text">系统帮助</text>
          </view>
          <text class="arrow">></text>
        </view>
      </view>

      <view v-if="userInfo.role === 1" class="menu-group">
        <view class="menu-item" @click="goToAdmin">
          <view class="item-left">
            <view class="icon-box purple">
              <text class="menu-icon">🛡️</text>
            </view>
            <text class="menu-text">用户管理</text>
          </view>
          <text class="arrow">></text>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item logout-item" @click="handleLogout">
          <view class="item-left">
            <text class="menu-text logout-text">退出登录</text>
          </view>
        </view>
      </view>

    </view>

    <view class="footer-version">Version 1.5.0</view>

    <view class="modal-mask" v-if="showPwdModal" @click.self="closePasswordModal">
      <view class="modal-card scale-in">
        <view class="modal-header">
          <text class="modal-title">修改密码</text>
          <view class="close-icon" @click="closePasswordModal">✕</view>
        </view>
        
        <view class="modal-body">
          <view class="input-field">
            <text class="field-label">旧密码</text>
            <input class="field-input" type="password" v-model="pwdForm.old" placeholder="请输入当前密码" placeholder-class="ph" />
          </view>
          <view class="input-field">
            <text class="field-label">新密码</text>
            <input class="field-input" type="password" v-model="pwdForm.new" placeholder="请输入新密码 (至少6位)" placeholder-class="ph" />
          </view>
        </view>

        <view class="modal-footer">
          <button class="modal-btn cancel" @click="closePasswordModal">取消</button>
          <button class="modal-btn confirm" @click="submitPasswordChange">确认修改</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';

/* =================================================================
   核心业务逻辑 (保持原样)
   ================================================================= */
const SERVICE_HOST = '101.35.132.175';
const API_BASE = `http://${SERVICE_HOST}:5000`;

const userInfo = ref({});
const showPwdModal = ref(false);
const pwdForm = ref({ old: '', new: '' });

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) userInfo.value = user;
});

const goToHelp = () => {
   uni.navigateTo({ url: '/pages/help/help' });
};

const goToAdmin = () => {
  uni.navigateTo({ url: '/pages/admin/manager' });
};

const startVocabularyTraining = () => {
  uni.navigateTo({
    url: '/pages/vocab/training'
  });
};

const getAvatarUrl = () => {
  if (userInfo.value.avatar) {
    if (userInfo.value.avatar.startsWith('http')) return userInfo.value.avatar;
    return `${API_BASE}${userInfo.value.avatar}`;
  }
  return '/static/logo.png';
};

const uploadAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (chooseImageRes) => {
      const tempFilePaths = chooseImageRes.tempFilePaths;
      uni.showLoading({ title: '上传中...' });
      
      uni.uploadFile({
        url: `${API_BASE}/api/upload_avatar`,
        filePath: tempFilePaths[0],
        name: 'file',
        formData: { 'user_id': userInfo.value.id },
        success: (uploadFileRes) => {
          uni.hideLoading();
          try {
             const res = JSON.parse(uploadFileRes.data);
             if (res.code === 200) {
               userInfo.value.avatar = res.data.avatar;
               uni.setStorageSync('userInfo', userInfo.value);
               uni.showToast({ title: '头像已更新', icon: 'none' });
             } else {
               uni.showToast({ title: '上传失败', icon: 'none' });
             }
          } catch(e) {
             uni.showToast({ title: '服务器错误', icon: 'none' });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({ title: '网络连接错误', icon: 'none' });
        }
      });
    }
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmColor: '#FF8A65', // 珊瑚橙
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('userInfo');
        uni.reLaunch({ url: '/pages/login/login' });
      }
    }
  });
};

const openPasswordModal = () => {
  pwdForm.value = { old: '', new: '' };
  showPwdModal.value = true;
};

const closePasswordModal = () => {
  showPwdModal.value = false;
};

const submitPasswordChange = () => {
  if (!pwdForm.value.old || !pwdForm.value.new) {
    uni.showToast({ title: '请输入完整信息', icon: 'none' });
    return;
  }
  
  if (pwdForm.value.new.length < 6) {
    uni.showToast({ title: '新密码至少6位', icon: 'none' });
    return;
  }

  uni.showLoading({ title: '提交中...' });

  uni.request({
    url: `${API_BASE}/api/user/password`,
    method: 'POST',
    data: {
      user_id: userInfo.value.id,
      old_password: pwdForm.value.old,
      new_password: pwdForm.value.new
    },
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        uni.showToast({ title: '修改成功' });
        closePasswordModal();
        setTimeout(() => {
          uni.removeStorageSync('userInfo');
          uni.reLaunch({ url: '/pages/login/login' });
        }, 1500);
      } else {
        uni.showToast({ title: res.data.msg || '修改失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: '网络错误', icon: 'none' });
    }
  });
};
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
}

.container {
  min-height: 100vh;
  padding: 0 30rpx;
  box-sizing: border-box;
  position: relative;
  overflow-x: hidden;
}

/* 顶部装饰背景 */
.profile-header-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 300rpx;
  background: linear-gradient(180deg, rgba(74, 111, 165, 0.1) 0%, rgba(245, 245, 240, 0) 100%);
  z-index: 0;
}

/* 2. 个人信息卡片 */
.profile-card {
  margin-top: 140rpx; /* 留出顶部空间 */
  background: $color-card;
  border-radius: 24rpx;
  padding: 50rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 10rpx 40rpx rgba(74, 111, 165, 0.08);
  position: relative;
  z-index: 1;
  margin-bottom: 50rpx;
}

.avatar-section {
  position: absolute;
  top: -70rpx;
}

.avatar-wrapper {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  background: $color-card;
  padding: 6rpx;
  box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.05);
  position: relative;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #E0E0E0;
}

.camera-icon {
  position: absolute;
  bottom: 0;
  right: 0;
  background: $color-primary;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid $color-card;
}

.camera-icon text { font-size: 22rpx; color: #FFF; }

.info-section {
  margin-top: 80rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.username {
  font-size: 36rpx;
  font-weight: 700;
  color: $color-text-main;
  margin-bottom: 10rpx;
}

.user-id {
  font-size: 24rpx;
  color: $color-text-sub;
  margin-bottom: 20rpx;
}

.role-badge {
  background: #F0F2F5;
  padding: 6rpx 20rpx;
  border-radius: 30rpx;
}

.role-badge text {
  font-size: 20rpx;
  color: $color-text-sub;
  font-weight: 600;
  letter-spacing: 1px;
}

.role-badge.admin {
  background: rgba(74, 111, 165, 0.1);
}
.role-badge.admin text { color: $color-primary; }

/* 3. 菜单列表 */
.menu-list {
  padding-bottom: 60rpx;
}

.menu-group {
  background: $color-card;
  border-radius: 20rpx;
  margin-bottom: 30rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 30rpx;
  border-bottom: 1px solid #F5F5F5;
}

.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #FAFAFA; }

.item-left {
  display: flex;
  align-items: center;
}

.icon-box {
  width: 60rpx;
  height: 60rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 24rpx;
  background: #F5F5F5;
}

.icon-box.blue { background: rgba(74, 111, 165, 0.1); }
.icon-box.orange { background: rgba(255, 138, 101, 0.1); }
.icon-box.green { background: rgba(76, 175, 80, 0.1); }
.icon-box.purple { background: rgba(156, 39, 176, 0.1); }

.menu-icon { font-size: 32rpx; }

.menu-text {
  font-size: 28rpx;
  font-weight: 500;
  color: $color-text-main;
}

.arrow {
  color: #CFD8DC;
  font-size: 28rpx;
  font-family: monospace;
}

.logout-item { justify-content: center; }
.logout-text { color: #FF5252; font-weight: 600; }

.footer-version {
  text-align: center;
  font-size: 22rpx;
  color: $color-text-sub;
  margin-bottom: 40rpx;
}

/* 4. 弹窗样式 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  width: 560rpx;
  background: $color-card;
  border-radius: 24rpx;
  padding: 40rpx;
  box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $color-text-main;
}

.close-icon {
  color: $color-text-sub;
  font-size: 36rpx;
  padding: 10rpx;
}

.modal-body {
  margin-bottom: 40rpx;
}

.input-field {
  margin-bottom: 30rpx;
}

.field-label {
  display: block;
  font-size: 24rpx;
  color: $color-text-sub;
  margin-bottom: 12rpx;
}

.field-input {
  background: #F5F5F5;
  height: 80rpx;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: $color-text-main;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.modal-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-btn.cancel {
  background: #F5F5F5;
  color: $color-text-sub;
}

.modal-btn.confirm {
  background: $color-primary;
  color: #FFF;
}

/* 动画 */
.fade-in { animation: fadeIn 0.6s ease-out; }
.slide-up { animation: slideUp 0.6s ease-out; }
.scale-in { animation: scaleIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(40rpx); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>