<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="profile-card">
      <view class="avatar-box" @click="uploadAvatar">
        <image 
          class="avatar" 
          :src="getAvatarUrl()" 
          mode="aspectFill"
        ></image>
        <view class="scan-line"></view> <view class="edit-icon">📷</view>
      </view>
      
      <view class="info-box">
        <text class="username">{{ userInfo.username || t.unknown }}</text>
        <text class="user-id">ID: {{ userInfo.id ? '#' + String(userInfo.id).padStart(4, '0') : 'NULL' }}</text>
        <view class="status-badge">
            {{ userInfo.role === 1 ? 'ADMINISTRATOR' : t.status }}
        </view>
      </view>
    </view>

    <view class="menu-group">
      <view class="menu-item" @click="switchLanguage">
        <view class="item-left">
          <text class="menu-icon">🌐</text>
          <text class="menu-text">{{ t.menu_lang }}</text>
        </view>
        <view class="item-right">
          <text class="value-text">{{ currentLang === 'zh' ? '中文' : 'ENG' }}</text>
          <text class="arrow">></text>
        </view>
      </view>

      <view class="menu-item" @click="openPasswordModal">
        <view class="item-left">
          <text class="menu-icon">🔐</text>
          <text class="menu-text">修改密码</text> </view>
        <text class="arrow">></text>
      </view>

      <view class="menu-item" @click="startVocabularyTraining">
        <view class="item-left">
          <text class="menu-icon">📚</text>
          <text class="menu-text">每日单词</text>
        </view>
        <text class="arrow">></text>
      </view>

      <view class="menu-item">
        <view class="item-left">
          <text class="menu-icon">📂</text>
          <text class="menu-text">{{ t.menu_help }}</text>
        </view>
        <text class="arrow">></text>
      </view>

      <view v-if="userInfo.role === 1" class="menu-item admin-entry" @click="goToAdmin">
        <view class="item-left">
          <text class="menu-icon">🛡️</text>
          <text class="menu-text">用户管理 // ADMIN CONSOLE</text>
        </view>
        <text class="arrow">></text>
      </view>

      <view class="menu-item logout" @click="handleLogout">
        <view class="item-left">
          <text class="menu-icon">⚠️</text>
          <text class="menu-text warn">{{ t.menu_logout }}</text>
        </view>
        <text class="arrow warn">></text>
      </view>

    </view>

    <view class="footer-version">{{ t.version }}</view>

    <view class="modal-mask" v-if="showPwdModal">
      <view class="cyber-modal">
        <view class="modal-header">
          <text class="modal-title">SECURITY UPDATE</text>
          <text class="close-btn" @click="closePasswordModal">✕</text>
        </view>
        
        <view class="modal-body">
          <view class="input-group">
            <text class="label">OLD PASSWORD</text>
            <input class="cyber-input" type="password" v-model="pwdForm.old" placeholder="******" placeholder-class="ph" />
          </view>
          <view class="input-group">
            <text class="label">NEW PASSWORD</text>
            <input class="cyber-input" type="password" v-model="pwdForm.new" placeholder="******" placeholder-class="ph" />
          </view>
        </view>

        <view class="modal-footer">
          <button class="modal-btn cancel" @click="closePasswordModal">CANCEL</button>
          <button class="modal-btn confirm" @click="submitPasswordChange">CONFIRM</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import messages from '@/utils/language.js';

// 获取环境配置
const SERVICE_HOST = '101.35.132.175'; // 确保这里是你的公网 IP
const API_BASE = `http://${SERVICE_HOST}:5000`;

const userInfo = ref({});
const currentLang = ref('zh');
const t = ref(messages.zh.profile);

// 修改密码相关状态
const showPwdModal = ref(false);
const pwdForm = ref({ old: '', new: '' });

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) userInfo.value = user;
  
  const savedLang = uni.getStorageSync('lang') || 'zh';
  currentLang.value = savedLang;
  t.value = messages[savedLang].profile;
});



const goToAdmin = () => {
  uni.navigateTo({ url: '/pages/admin/manager' });
};

const startVocabularyTraining = () => {
  // 跳转到新建的训练页面
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
      uni.showLoading({ title: 'UPLOADING...' });
      
      uni.uploadFile({
        url: `${API_BASE}/api/upload_avatar`,
        filePath: tempFilePaths[0],
        name: 'file',
        formData: { 'user_id': userInfo.value.id },
        success: (uploadFileRes) => {
          uni.hideLoading();
          const res = JSON.parse(uploadFileRes.data);
          if (res.code === 200) {
            userInfo.value.avatar = res.data.avatar;
            uni.setStorageSync('userInfo', userInfo.value);
            uni.showToast({ title: 'AVATAR UPDATED', icon: 'none' });
          } else {
            uni.showToast({ title: 'UPLOAD FAILED', icon: 'none' });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({ title: 'NET ERR', icon: 'none' });
        }
      });
    }
  });
};

const switchLanguage = () => {
  const newLang = currentLang.value === 'zh' ? 'en' : 'zh';
  currentLang.value = newLang;
  uni.setStorageSync('lang', newLang);
  t.value = messages[newLang].profile;
  uni.showToast({ title: newLang === 'zh' ? '已切换中文' : 'SWITCHED TO ENG', icon: 'none' });
};

const handleLogout = () => {
  uni.showModal({
    title: 'WARNING',
    content: t.value.logout_confirm,
    confirmColor: '#ff003c',
    confirmText: t.value.logout_ok,
    cancelText: t.value.logout_cancel,
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('userInfo');
        uni.reLaunch({ url: '/pages/login/login' });
      }
    }
  });
};

// --- 修改密码逻辑 ---
const openPasswordModal = () => {
  pwdForm.value = { old: '', new: '' };
  showPwdModal.value = true;
};

const closePasswordModal = () => {
  showPwdModal.value = false;
};

const submitPasswordChange = () => {
  if (!pwdForm.value.old || !pwdForm.value.new) {
    uni.showToast({ title: '请输入完整', icon: 'none' });
    return;
  }
  
  if (pwdForm.value.new.length < 6) {
    uni.showToast({ title: '新密码太短', icon: 'none' });
    return;
  }

  uni.showLoading({ title: 'UPDATING...' });

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
        uni.showToast({ title: 'SUCCESS' });
        closePasswordModal();
        setTimeout(() => {
          uni.removeStorageSync('userInfo');
          uni.reLaunch({ url: '/pages/login/login' });
        }, 1500);
      } else {
        uni.showToast({ title: res.data.msg || 'FAILED', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: 'NET ERR', icon: 'none' });
    }
  });
};
</script>

<style>
/* 保持原有样式 */
page { background-color: #050505; color: #ccc; font-family: 'Courier New', monospace; }
.container { padding: 20px; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, #111 0%, #000 100%); z-index: -1; }

.profile-card {
  background: #0a0a0a; border: 1px solid #333; padding: 20px; 
  display: flex; align-items: center; margin-bottom: 40px; 
  box-shadow: 0 0 20px rgba(0,0,0,0.5); position: relative; overflow: hidden;
}
.profile-card::before { content: ''; position: absolute; top: 0; left: 0; width: 20px; height: 20px; border-top: 2px solid #00f3ff; border-left: 2px solid #00f3ff; }
.profile-card::after { content: ''; position: absolute; bottom: 0; right: 0; width: 20px; height: 20px; border-bottom: 2px solid #00f3ff; border-right: 2px solid #00f3ff; }

.avatar-box { position: relative; margin-right: 20px; width: 70px; height: 70px; border: 2px solid #333; border-radius: 50%; overflow: hidden; }
.avatar-box:active { border-color: #00f3ff; opacity: 0.8; }
.avatar { width: 100%; height: 100%; background: #000; }
.scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: #00f3ff; box-shadow: 0 0 5px #00f3ff; animation: scan 2s infinite linear; }
@keyframes scan { 0% {top:0} 100% {top:100%} }
.edit-icon { position: absolute; bottom: 0; left: 0; width: 100%; background: rgba(0,0,0,0.7); color: #fff; font-size: 10px; text-align: center; height: 20px; line-height: 20px; }

.username { font-size: 20px; font-weight: 900; color: #fff; display: block; letter-spacing: 1px; }
.user-id { font-size: 12px; color: #666; display: block; margin-top: 5px; font-family: monospace; }
.status-badge { margin-top: 8px; display: inline-block; background: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff; color: #00f3ff; font-size: 10px; padding: 2px 6px; }

.menu-group { border-top: 1px solid #222; }
.menu-item { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid #222; }
.menu-item:active { opacity: 0.7; background: rgba(255,255,255,0.05); }
.menu-icon { margin-right: 15px; font-size: 16px; }
.menu-text { font-size: 14px; color: #ddd; font-weight: bold; }
.menu-text.warn { color: #ff003c; }
.value-text { font-size: 12px; color: #00f3ff; margin-right: 10px; }
.arrow { color: #444; font-family: monospace; }
.arrow.warn { color: #ff003c; }
.footer-version { text-align: center; color: #333; font-size: 10px; margin-top: 50px; }

.admin-entry .menu-icon { text-shadow: 0 0 5px #ff003c; }

/* 模态框样式 */
.modal-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(3px); }
.cyber-modal { width: 80%; background: #0a0a0a; border: 1px solid #00f3ff; box-shadow: 0 0 20px rgba(0, 243, 255, 0.2); padding: 0; display: flex; flex-direction: column; }
.modal-header { background: rgba(0, 243, 255, 0.1); padding: 10px 15px; border-bottom: 1px solid #00f3ff; display: flex; justify-content: space-between; align-items: center; }
.modal-title { color: #00f3ff; font-weight: bold; font-size: 14px; letter-spacing: 1px; }
.close-btn { color: #fff; font-size: 18px; padding: 5px; }

.modal-body { padding: 20px; }
.input-group { margin-bottom: 15px; }
.label { display: block; color: #666; font-size: 10px; margin-bottom: 5px; font-weight: bold; }
.cyber-input { background: #111; border: 1px solid #333; color: #fff; padding: 10px; font-size: 14px; border-radius: 2px; }
.cyber-input:focus { border-color: #00f3ff; box-shadow: 0 0 5px rgba(0,243,255,0.3); }
.ph { color: #444; }

.modal-footer { display: flex; border-top: 1px solid #333; }
.modal-btn { flex: 1; background: transparent; border: none; color: #fff; border-radius: 0; padding: 15px 0; font-size: 14px; font-weight: bold; }
.modal-btn:active { background: #1a1a1a; }
.modal-btn.confirm { color: #00f3ff; border-left: 1px solid #333; }
.modal-btn.cancel { color: #666; }
</style>