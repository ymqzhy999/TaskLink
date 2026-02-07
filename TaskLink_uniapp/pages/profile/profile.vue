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
        <view class="status-badge">{{ t.status }}</view>
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

      <view class="menu-item">
        <view class="item-left">
          <text class="menu-icon">📂</text>
          <text class="menu-text">{{ t.menu_help }}</text>
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
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import messages from '@/utils/language.js';

const API_BASE = 'http://192.168.10.26:5000'; // ⚠️ 确认你的 IP
const userInfo = ref({});
const currentLang = ref('zh');
const t = ref(messages.zh.profile);

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (user) userInfo.value = user;
  
  const savedLang = uni.getStorageSync('lang') || 'zh';
  currentLang.value = savedLang;
  t.value = messages[savedLang].profile;
});

// ✅ 核心逻辑：获取头像地址
const getAvatarUrl = () => {
  if (userInfo.value.avatar) {
    // 如果是 http 开头（虽然不太可能），直接用
    if (userInfo.value.avatar.startsWith('http')) {
      return userInfo.value.avatar;
    }
    // 否则拼接后端地址（因为后端存的是 /static/uploads/...）
    return `${API_BASE}${userInfo.value.avatar}`;
  }
  // 默认头像
  return '/static/logo.png';
};

// ✅ 核心逻辑：上传头像
const uploadAvatar = () => {
  uni.chooseImage({
    count: 1, // 只选一张
    sizeType: ['compressed'], // 压缩图，减轻服务器压力
    sourceType: ['album', 'camera'],
    success: (chooseImageRes) => {
      const tempFilePaths = chooseImageRes.tempFilePaths;
      
      uni.showLoading({ title: 'UPLOADING...' });
      
      uni.uploadFile({
        url: `${API_BASE}/api/upload_avatar`,
        filePath: tempFilePaths[0],
        name: 'file', // 这里的 key 必须和后端 request.files['file'] 对应
        formData: {
          'user_id': userInfo.value.id
        },
        success: (uploadFileRes) => {
          uni.hideLoading();
          // uni.uploadFile 返回的 data 是字符串，需要 JSON.parse
          const res = JSON.parse(uploadFileRes.data);
          
          if (res.code === 200) {
            // 1. 更新本地显示的 userInfo
            userInfo.value.avatar = res.data.avatar;
            // 2. 更新本地缓存，保证下次进来还在
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
</script>

<style>
page { background-color: #050505; color: #ccc; font-family: 'Courier New', monospace; }
.container { padding: 20px; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, #111 0%, #000 100%); z-index: -1; }

/* 1. 用户卡片 - 赛博风格 */
.profile-card {
  background: #0a0a0a; 
  border: 1px solid #333; 
  padding: 20px; 
  display: flex; align-items: center; 
  margin-bottom: 40px; 
  box-shadow: 0 0 20px rgba(0,0,0,0.5); 
  position: relative; overflow: hidden;
}
.profile-card::before { content: ''; position: absolute; top: 0; left: 0; width: 20px; height: 20px; border-top: 2px solid #00f3ff; border-left: 2px solid #00f3ff; }
.profile-card::after { content: ''; position: absolute; bottom: 0; right: 0; width: 20px; height: 20px; border-bottom: 2px solid #00f3ff; border-right: 2px solid #00f3ff; }

/* 头像 & 扫描动画 */
.avatar-box { 
  position: relative; 
  margin-right: 20px; 
  width: 70px; height: 70px; 
  border: 2px solid #333; 
  border-radius: 50%; 
  overflow: hidden; 
}
/* 给头像加点击反馈 */
.avatar-box:active { border-color: #00f3ff; opacity: 0.8; }

.avatar { width: 100%; height: 100%; background: #000; }
.scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: #00f3ff; box-shadow: 0 0 5px #00f3ff; animation: scan 2s infinite linear; }
@keyframes scan { 0% {top:0} 100% {top:100%} }

/* 相机小图标 */
.edit-icon {
  position: absolute; bottom: 0; left: 0; width: 100%; 
  background: rgba(0,0,0,0.7); color: #fff; font-size: 10px; 
  text-align: center; height: 20px; line-height: 20px;
}

.username { font-size: 20px; font-weight: 900; color: #fff; display: block; letter-spacing: 1px; }
.user-id { font-size: 12px; color: #666; display: block; margin-top: 5px; font-family: monospace; }
.status-badge { margin-top: 8px; display: inline-block; background: rgba(0, 243, 255, 0.1); border: 1px solid #00f3ff; color: #00f3ff; font-size: 10px; padding: 2px 6px; }

/* 2. 菜单列表 - 黑科技风 */
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
</style>