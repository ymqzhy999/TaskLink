<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
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
            <text class="menu-text">安全中心</text> 
          </view>
          <view class="item-right">
             <text class="value-text">修改密码</text>
             <text class="arrow">></text>
          </view>
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

        <view class="menu-item" @click="goToStats">
          <view class="item-left">
            <view class="icon-box blue-deep">
              <text class="menu-icon">📊</text>
            </view>
            <text class="menu-text">学习分析报告</text> 
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

        <view class="menu-item">
          <view class="item-left">
            <view class="icon-box purple">
              <text class="menu-icon">🌙</text>
            </view>
            <text class="menu-text">深色模式</text>
          </view>
          <switch :checked="isDarkMode" @change="toggleTheme" color="#4A6FA5" style="transform:scale(0.8)"/>
        </view>
      </view>

      <view v-if="userInfo.role === 1" class="menu-group">
        <view class="menu-item" @click="goToAdmin">
          <view class="item-left">
            <view class="icon-box purple">
              <text class="menu-icon">🛡️</text>
            </view>
            <text class="menu-text">用户权限管理</text>
          </view>
          <text class="arrow">></text>
        </view>
      </view>

      <view class="menu-group">
        <view class="menu-item logout-item" @click="handleLogout">
          <text class="logout-text">退出当前连接</text>
        </view>
      </view>

    </view>

    <view class="footer-version">Version 1.5.2</view>

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
            <input class="field-input" type="password" v-model="pwdForm.new" placeholder="至少6位新密码" placeholder-class="ph" />
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
import { useTheme } from '@/utils/useTheme';

const SERVICE_HOST = '101.35.132.175';
const API_BASE = `http://${SERVICE_HOST}:5000`;

const userInfo = ref({});
const showPwdModal = ref(false);
const pwdForm = ref({ old: '', new: '' });
const { isDarkMode } = useTheme();

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) userInfo.value = user;
});

const toggleTheme = (e) => {
  const dark = e.detail.value;
  // 触发全局事件，通知 App.vue 和其他页面更新
  uni.$emit('toggleTheme', dark);
  // 为了确保当前页面也立即响应（防止事件延迟），手动再设置一次本地存储
  uni.setStorageSync('theme', dark ? 'dark' : 'light');
  // useTheme 内部的监听会自动更新 isDarkMode
};

const goToHelp = () => uni.navigateTo({ url: '/pages/help/help' });
const goToStats = () => uni.navigateTo({ url: '/pages/profile/data_stats' });
const goToAdmin = () => uni.navigateTo({ url: '/pages/admin/manager' });
const startVocabularyTraining = () => uni.navigateTo({ url: '/pages/vocab/training' });

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
    success: (res) => {
      const tempFilePaths = res.tempFilePaths;
      uni.showLoading({ title: '上传中...' });
      uni.uploadFile({
        url: `${API_BASE}/api/upload_avatar`,
        filePath: tempFilePaths[0],
        name: 'file',
        formData: { 'user_id': userInfo.value.id },
        success: (uploadRes) => {
          uni.hideLoading();
          const resData = JSON.parse(uploadRes.data);
          if (resData.code === 200) {
            userInfo.value.avatar = resData.data.avatar;
            uni.setStorageSync('userInfo', userInfo.value);
            uni.showToast({ title: '头像已更新' });
          }
        }
      });
    }
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    confirmColor: '#FF8A65',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('userInfo');
        uni.reLaunch({ url: '/pages/login/login' });
      }
    }
  });
};

const openPasswordModal = () => { pwdForm.value = { old: '', new: '' }; showPwdModal.value = true; };
const closePasswordModal = () => { showPwdModal.value = false; };
const submitPasswordChange = () => {
  if (!pwdForm.value.old || !pwdForm.value.new) return uni.showToast({ title: '请填写完整', icon: 'none' });
  uni.showLoading({ title: '提交中...' });
  uni.request({
    url: `${API_BASE}/api/user/password`,
    method: 'POST',
    data: { user_id: userInfo.value.id, old_password: pwdForm.value.old, new_password: pwdForm.value.new },
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) {
        uni.showToast({ title: '修改成功' });
        closePasswordModal();
        setTimeout(() => { uni.removeStorageSync('userInfo'); uni.reLaunch({ url: '/pages/login/login' }); }, 1500);
      } else {
        uni.showToast({ title: res.data.msg, icon: 'none' });
      }
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

page { background-color: $color-bg; font-family: 'Inter', sans-serif; transition: background-color 0.3s; }

/* 动态类名绑定 */
.container { min-height: 100vh; padding: 0 30rpx; position: relative; transition: all 0.3s; padding-top: var(--status-bar-height); }
.container.dark { background-color: $dark-bg; }

.profile-header-bg { position: absolute; top: 0; left: 0; width: 100%; height: 300rpx; 
  background: linear-gradient(180deg, rgba(74, 111, 165, 0.12) 0%, rgba(245, 245, 240, 0) 100%); z-index: 0; }
.container.dark .profile-header-bg { background: linear-gradient(180deg, rgba(74, 111, 165, 0.2) 0%, rgba(18, 18, 18, 0) 100%); }

/* 2. 个人信息卡片 */
.profile-card { margin-top: 140rpx; background: $color-card; border-radius: 24rpx; padding: 50rpx 40rpx; 
  display: flex; flex-direction: column; align-items: center; box-shadow: 0 10rpx 40rpx rgba(74, 111, 165, 0.08); position: relative; z-index: 1; margin-bottom: 50rpx; transition: background-color 0.3s; }
.container.dark .profile-card { background-color: $dark-card; box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.3); }

.avatar-section { position: absolute; top: -70rpx; }
.avatar-wrapper { width: 140rpx; height: 140rpx; border-radius: 50%; background: $color-card; padding: 6rpx; box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.05); position: relative; transition: background-color 0.3s; }
.container.dark .avatar-wrapper { background-color: $dark-card; }

.avatar { width: 100%; height: 100%; border-radius: 50%; background: #E0E0E0; }
.camera-icon { position: absolute; bottom: 0; right: 0; background: $color-primary; width: 44rpx; height: 44rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4rpx solid $color-card; font-size: 22rpx; color: #FFF; transition: border-color 0.3s; }
.container.dark .camera-icon { border-color: $dark-card; }

.info-section { margin-top: 80rpx; text-align: center; }
.username { font-size: 36rpx; font-weight: 700; color: $color-text-main; display: block; transition: color 0.3s; }
.container.dark .username { color: $dark-text-main; }

.user-id { font-size: 24rpx; color: $color-text-sub; margin: 10rpx 0 20rpx; display: block; transition: color 0.3s; }
.container.dark .user-id { color: $dark-text-sub; }

.role-badge { background: #F0F2F5; padding: 6rpx 20rpx; border-radius: 30rpx; font-size: 20rpx; color: $color-text-sub; font-weight: 600; letter-spacing: 1px; transition: all 0.3s; }
.container.dark .role-badge { background: #2C2C2C; color: $dark-text-sub; }

.role-badge.admin { background: rgba(74, 111, 165, 0.1); color: $color-primary; }
.container.dark .role-badge.admin { background: rgba(74, 111, 165, 0.2); }

/* 3. 菜单列表优化 */
.menu-list { padding-bottom: 60rpx; }
.menu-group { background: $color-card; border-radius: 20rpx; margin-bottom: 30rpx; overflow: hidden; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02); transition: background-color 0.3s; }
.container.dark .menu-group { background-color: $dark-card; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.2); }

.menu-item { display: flex; justify-content: space-between; align-items: center; padding: 34rpx 30rpx; border-bottom: 1px solid #F8F9FA; transition: background 0.2s, border-color 0.3s; }
.container.dark .menu-item { border-bottom: 1px solid #2C2C2C; }
.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #F8F9FA; }
.container.dark .menu-item:active { background: #252525; }

.item-left { display: flex; align-items: center; }
.icon-box { width: 64rpx; height: 64rpx; border-radius: 18rpx; display: flex; align-items: center; justify-content: center; margin-right: 24rpx; }
.icon-box.blue { background: rgba(74, 111, 165, 0.1); }
.icon-box.blue-deep { background: rgba(63, 81, 181, 0.1); }
.icon-box.orange { background: rgba(255, 138, 101, 0.1); }
.icon-box.green { background: rgba(76, 175, 80, 0.1); }
.icon-box.purple { background: rgba(156, 39, 176, 0.1); }
/* 深色模式下图标背景微调，保持可见度 */
.container.dark .icon-box { opacity: 0.8; }

.menu-icon { font-size: 32rpx; }
.menu-text { font-size: 28rpx; font-weight: 500; color: $color-text-main; transition: color 0.3s; }
.container.dark .menu-text { color: $dark-text-main; }

.item-right { display: flex; align-items: center; }
.value-text { font-size: 24rpx; color: $color-text-sub; margin-right: 10rpx; transition: color 0.3s; }
.container.dark .value-text { color: $dark-text-sub; }

.arrow { color: #CFD8DC; font-size: 28rpx; font-family: monospace; transition: color 0.3s; }
.container.dark .arrow { color: #555; }

.logout-item { justify-content: center; }
.logout-text { color: #FF5252; font-weight: 600; font-size: 28rpx; }
.footer-version { text-align: center; font-size: 22rpx; color: $color-text-sub; margin-bottom: 40rpx; opacity: 0.6; transition: color 0.3s; }
.container.dark .footer-version { color: $dark-text-sub; }

/* 4. 弹窗 (保持原风格) */
.modal-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); backdrop-filter: blur(4px); z-index: 999; display: flex; align-items: center; justify-content: center; }
.modal-card { width: 560rpx; background: $color-card; border-radius: 24rpx; padding: 40rpx; box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.1); transition: background-color 0.3s; }
.container.dark .modal-card { background-color: $dark-card; }

.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40rpx; }
.modal-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; transition: color 0.3s; }
.container.dark .modal-title { color: $dark-text-main; }

.close-icon { color: $color-text-sub; font-size: 36rpx; padding: 10rpx; transition: color 0.3s; }
.container.dark .close-icon { color: $dark-text-sub; }

.input-field { margin-bottom: 30rpx; }
.field-label { display: block; font-size: 24rpx; color: $color-text-sub; margin-bottom: 12rpx; transition: color 0.3s; }
.container.dark .field-label { color: $dark-text-sub; }

.field-input { background: #F5F5F5; height: 80rpx; border-radius: 12rpx; padding: 0 24rpx; font-size: 28rpx; color: $color-text-main; transition: all 0.3s; }
.container.dark .field-input { background: #2C2C2C; color: $dark-text-main; }

.modal-footer { display: flex; gap: 20rpx; }
.modal-btn { flex: 1; height: 84rpx; border-radius: 42rpx; font-size: 28rpx; font-weight: 600; display: flex; align-items: center; justify-content: center; }
.modal-btn.cancel { background: #F5F5F5; color: $color-text-sub; transition: all 0.3s; }
.container.dark .modal-btn.cancel { background: #2C2C2C; color: $dark-text-sub; }

.modal-btn.confirm { background: $color-primary; color: #FFF; }

.fade-in { animation: fadeIn 0.6s ease-out; }
.slide-up { animation: slideUp 0.6s ease-out; }
.scale-in { animation: scaleIn 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(40rpx); } to { opacity: 1; transform: translateY(0); } }
@keyframes scaleIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>