<template>
  <view class="container">
    <view class="nav-header">
      <view class="nav-content">
        <block v-if="!isSelectionMode">
          <view class="header-left">
            <text class="page-title">Community</text>
            <view class="online-badge">
              <view class="dot"></view>
              <text>{{ onlineCount }} Online</text>
            </view>
          </view>
        </block>
        
        <block v-else>
          <view class="selection-header">
            <text class="selection-count">已选择 {{ selectedIds.length }} 条消息</text>
            <view class="cancel-btn" @click="exitSelectionMode">取消</view>
          </view>
        </block>
      </view>
    </view>

    <scroll-view 
      scroll-y 
      class="chat-area" 
      :scroll-into-view="scrollTarget"
      scroll-with-animation
      :enable-back-to-top="true"
      @click="closeEmojiPanel"
    >
      <view class="system-msg">
        <text class="system-text">—— 欢迎来到 TaskLink 公共频道 ——</text>
      </view>

      <view 
        v-for="(msg, index) in messages" 
        :key="msg.id || index" 
        class="msg-row"
        :class="{ 
          'self': msg.user_id === myInfo.id,
          'selecting': isSelectionMode 
        }"
        :id="'msg-' + index"
      >
        <view v-if="isSelectionMode" class="checkbox-wrapper" @click.stop="onSelectMessage(msg)">
          <view class="checkbox" :class="{ 'checked': selectedIds.includes(msg.id) }">
            <text v-if="selectedIds.includes(msg.id)" class="check-icon">✓</text>
          </view>
        </view>

        <image 
          v-if="msg.user_id !== myInfo.id" 
          class="avatar" 
          :src="formatAvatar(msg.avatar)" 
          mode="aspectFill"
          @longpress.stop="onLongPressMessage(msg)"
        ></image>

        <view class="content-box">
          <text class="sender-name" v-if="msg.user_id !== myInfo.id">{{ msg.username }}</text>
          
          <view 
            class="bubble" 
            @longpress.stop="onLongPressMessage(msg)"
            @click.stop="onSelectMessage(msg)"
            :class="{ 'image-bubble': msg.type === 'image' }"
          >
            <image 
              v-if="msg.type === 'image'"
              :src="formatAvatar(msg.content)" 
              mode="widthFix" 
              class="msg-image"
              @click.stop="previewImage(msg.content)"
            ></image>

            <rich-text 
              v-else
              :nodes="parseEmoji(msg.content)" 
              class="msg-text"
            ></rich-text>
          </view>
        </view>

        <image 
          v-if="msg.user_id === myInfo.id" 
          class="avatar right" 
          :src="formatAvatar(msg.avatar)" 
          mode="aspectFill"
          @longpress.stop="onLongPressMessage(msg)"
        ></image>
      </view>

      <view id="bottom-anchor" style="height: 20px;"></view>
    </scroll-view>

    <view v-if="!isSelectionMode" class="input-area-wrapper">
      <view class="input-bar">
        <view class="icon-btn" @click.stop="toggleEmojiPanel">
          <text class="iconfont">☺</text>
        </view>

        <view class="icon-btn" @click="chooseImage">
          <text class="iconfont">📷</text>
        </view>

        <input 
          class="minimal-input" 
          v-model="inputText" 
          placeholder="说点什么..." 
          placeholder-class="ph-style"
          confirm-type="send"
          @confirm="sendMessage"
          @focus="closeEmojiPanel"
        />
        
        <view class="send-btn" @click="sendMessage">
          <text>发送</text>
        </view>
      </view>

      <view class="emoji-panel" v-if="showEmojiPanel">
        <scroll-view scroll-y style="height: 200px;">
          <view class="emoji-grid">
            <view v-for="i in 135" :key="i" class="emoji-item" @click="selectEmoji(i-1)">
              <image 
                :src="`${FLASK_URL}/static/emoji/${(i-1).toString().padStart(2, '0')}.gif`" 
                class="emoji-icon"
              ></image>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>

    <view v-else class="delete-bar">
      <view class="delete-btn" @click="confirmDelete">
        <text>删除选中 ({{ selectedIds.length }})</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue';
import { onUnload, onShow, onHide } from '@dcloudio/uni-app';


const FLASK_URL = `http://101.35.132.175:5000`; 

const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTarget = ref('');
const onlineCount = ref(1);
const isSelectionMode = ref(false); 
const selectedIds = ref([]);  
const showEmojiPanel = ref(false); 

// 页面活跃锁
const isPageActive = ref(true);

const getToken = () => uni.getStorageSync('userInfo')?.token || '';

onShow(() => {
  isPageActive.value = true;
  
  const app = getApp();
  if (app.globalData) app.globalData.isSquareOpen = true; 
  uni.removeTabBarBadge({ index: 1 });
  
  const user = uni.getStorageSync('userInfo');
  if (!user || !user.token) {
    uni.reLaunch({ url: '/pages/login/login' });
    return;
  }
  myInfo.value = user;
  
  fetchHistory();
  
  // 监听消息
  uni.$off('global_new_message'); 
  uni.$on('global_new_message', (msg) => {
      if (!isPageActive.value) return;
      console.log('Square 收到:', msg);
      
      // 前端去重
      if (messages.value.length > 0) {
          const last = messages.value[messages.value.length - 1];
          if (last.id === msg.id || (last.content === msg.content && last.user_id === msg.user_id && Date.now() - new Date(last.created_at || 0).getTime() < 500)) {
              return;
          }
      }
      
      messages.value.push(msg);
      scrollToBottom();
  });
  
  // Socket 连接检查
  if (!app.globalData.socket && app.initSocket) {
      app.initSocket();
  }
  
  const socket = app.globalData.socket;
  
  if (socket && !socket.connected) {
      console.log('检测到 Socket 断开，正在强制重连...');
      socket.connect(); 
  }

  if (socket) {
        socket.off('connect');
        socket.off('connect_error');
        socket.off('disconnect');
        socket.off('update_online_count');

        socket.on('connect', () => {
            console.log('✅ Socket 已连接:', socket.id);
        });
        
        socket.on('connect_error', (error) => {
            console.error('❌ Socket 连接错误:', error);
        });
        
        socket.on('disconnect', (reason) => {
            console.log('⚠️ Socket 断开:', reason);
        });

        socket.on('update_online_count', (count) => { 
            if (isPageActive.value) onlineCount.value = count; 
        });
    }
});

onHide(() => {
  isPageActive.value = false;
  const app = getApp();
  if (app.globalData) app.globalData.isSquareOpen = false;
  uni.$off('global_new_message');
});

onUnmounted(() => {
  isPageActive.value = false;
  uni.$off('global_new_message');
});

const sendSocketMessage = (content, type = 'text') => {
  const app = getApp();
  let socket = app.globalData.socket;
  
  if (!socket || !socket.connected) {
      console.log('发送时发现断开，尝试重连...');
      
      if (!socket && app.initSocket) {
          app.initSocket();
          socket = app.globalData.socket;
      }
      if (socket) socket.connect();

      uni.showToast({ title: '正在连接...', icon: 'loading' });
      
      setTimeout(() => {
          if (socket && socket.connected) {
              socket.emit("send_message", {
                user_id: myInfo.value.id,
                content: content,
                type: type, 
                username: myInfo.value.username, 
                avatar: myInfo.value.avatar
              });
          } else {
              uni.showToast({ title: '连接断开，请检查网络', icon: 'none' });
          }
      }, 1000);
      return;
  }
  
  socket.emit("send_message", {
    user_id: myInfo.value.id,
    content: content,
    type: type, 
    username: myInfo.value.username, 
    avatar: myInfo.value.avatar
  });
};

const sendMessage = () => {
  if (!inputText.value.trim()) return;
  const content = inputText.value;
  inputText.value = ''; 
  showEmojiPanel.value = false;
  sendSocketMessage(content, 'text');
};

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: (res) => {
      uploadImage(res.tempFilePaths[0]);
    }
  });
};

const uploadImage = (filePath) => {
  uni.showLoading({ title: '发送中...' });
  uni.uploadFile({
    url: `${FLASK_URL}/api/chat/upload`,
    filePath: filePath,
    name: 'file',
    header: { 'Authorization': getToken() },
    success: (res) => {
      uni.hideLoading();
      try {
        const data = JSON.parse(res.data);
        if (data.code === 200) {
          sendSocketMessage(data.data.url, 'image');
        } else if (data.code === 401 || data.code === 403) {
             uni.showToast({ title: '认证失败', icon: 'none' });
             setTimeout(() => {
                 uni.removeStorageSync('userInfo');
                 uni.reLaunch({ url: '/pages/login/login' });
             }, 1000);
        }
      } catch (e) {}
    },
    fail: () => uni.hideLoading()
  });
};

const previewImage = (url) => {
  const fullUrl = formatAvatar(url);
  uni.previewImage({ urls: [fullUrl], current: fullUrl });
};

const toggleEmojiPanel = () => {
  showEmojiPanel.value = !showEmojiPanel.value;
  if(showEmojiPanel.value) {
    uni.hideKeyboard(); 
    scrollToBottom();
  }
};
const closeEmojiPanel = () => showEmojiPanel.value = false;
const selectEmoji = (i) => inputText.value += `[face:${i}]`;
const parseEmoji = (c) => {
  if (!c) return '';
  return c.replace(/\[face:(\d+)\]/g, (m, id) => {
    const f = id.toString().padStart(2, '0');
    return `<img style="width:24px; height:24px; vertical-align:middle; display:inline-block;" src="${FLASK_URL}/static/emoji/${f}.gif" />`;
  });
};

const onLongPressMessage = (msg) => { isSelectionMode.value = true; selectedIds.value = [msg.id]; uni.vibrateShort(); };
const onSelectMessage = (msg) => {
  if (!isSelectionMode.value) return;
  const idx = selectedIds.value.indexOf(msg.id);
  idx > -1 ? selectedIds.value.splice(idx, 1) : selectedIds.value.push(msg.id);
};
const exitSelectionMode = () => { isSelectionMode.value = false; selectedIds.value = []; };
const confirmDelete = () => {
  if(selectedIds.value.length) uni.showModal({ title:'删除', content:'仅本地删除', success: res => { if(res.confirm) doLocalDelete(); } });
};
const doLocalDelete = () => {
  const key = `deleted_msgs_${myInfo.value.id}`;
  const old = uni.getStorageSync(key) || [];
  uni.setStorageSync(key, [...new Set([...old, ...selectedIds.value])]);
  messages.value = messages.value.filter(m => !selectedIds.value.includes(m.id));
  exitSelectionMode();
};

const formatAvatar = (path) => {
  if (!path) return '/static/logo.png';
  return path.startsWith('http') ? path : `${FLASK_URL}${path}`;
};

const fetchHistory = () => {
    uni.request({
        url: `${FLASK_URL}/api/square/history`, 
        header: { 'Authorization': getToken() },
        data: { user_id: myInfo.value.id },
        success: (res) => {
            if (res.statusCode === 401 || res.data.code === 401 || res.data.code === 403) {
                 uni.showToast({ title: '会话过期或账号禁用', icon: 'none' });
                 setTimeout(() => {
                     uni.removeStorageSync('userInfo');
                     uni.reLaunch({ url: '/pages/login/login' });
                 }, 1000);
                 return;
            }
            if (res.data.code === 200 && isPageActive.value) {
                const key = `deleted_msgs_${myInfo.value.id}`;
                const deletedIds = uni.getStorageSync(key) || [];
                messages.value = res.data.data.filter(m => !deletedIds.includes(m.id));
                scrollToBottom();
            }
        },
        fail: (err) => console.error('History fetch failed', err)
    });
};

const scrollToBottom = () => {
  if (!isPageActive.value) return;
  scrollTarget.value = '';
  nextTick(() => { 
      if (isPageActive.value) scrollTarget.value = 'bottom-anchor'; 
  });
};
</script>

<style lang="scss" scoped>
/* 1. 色彩与字体变量 */
$color-bg: #F5F5F0;        /* 浅米色背景 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-accent: #FF8A65;    /* 珊瑚橙 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */
$color-white: #FFFFFF;
$color-bubble-other: #FFFFFF;
$color-bubble-self: #4A6FA5;

page { 
  background-color: $color-bg; 
  height: 100vh; 
  overflow: hidden; 
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
}

.container { 
  height: 100vh; 
  display: flex; 
  flex-direction: column; 
  background-color: $color-bg;
}

/* 2. 顶部导航栏 */
.nav-header {
  background: rgba(245, 245, 240, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0,0,0,0.03);
  padding-top: var(--status-bar-height);
  flex-shrink: 0;
  z-index: 100;
}

.nav-content {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30rpx;
}

.page-title {
  font-size: 34rpx;
  font-weight: 700;
  color: $color-text-main;
  letter-spacing: -0.5px;
}

.online-badge {
  display: flex;
  align-items: center;
  background: rgba(74, 111, 165, 0.1);
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  margin-left: 16rpx;
}

.online-badge text {
  font-size: 20rpx;
  color: $color-primary;
  font-weight: 600;
}

.dot {
  width: 10rpx;
  height: 10rpx;
  background: $color-primary;
  border-radius: 50%;
  margin-right: 8rpx;
  animation: breathe 2s infinite ease-in-out;
}

@keyframes breathe {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.selection-header {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
}
.selection-count { font-size: 30rpx; font-weight: 600; color: $color-text-main; }
.cancel-btn { font-size: 28rpx; color: $color-primary; padding: 10rpx 20rpx; }

/* 3. 聊天区域 */
.chat-area { 
  flex: 1; 
  height: 0; 
  width: 100%; 
  background: $color-bg;
  padding: 30rpx; 
  box-sizing: border-box; 
}

.system-msg { 
  text-align: center; 
  margin: 30rpx 0; 
}

.system-text {
  font-size: 20rpx;
  color: $color-text-sub;
  background: rgba(0,0,0,0.03);
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  letter-spacing: 1px;
}

/* 消息行 */
.msg-row { 
  display: flex; 
  margin-bottom: 40rpx; 
  align-items: flex-start; 
}

.msg-row.self { flex-direction: row-reverse; }
.msg-row.selecting { opacity: 0.6; }

/* 头像 */
.avatar { 
  width: 80rpx; 
  height: 80rpx; 
  border-radius: 20rpx; /* 微圆角，比圆形更现代 */
  background: #E0E0E0;
  flex-shrink: 0;
  box-shadow: 0 4rpx 8rpx rgba(0,0,0,0.05);
}

.avatar.right { margin-left: 20rpx; }

/* 多选框 */
.checkbox-wrapper { display: flex; align-items: center; padding-right: 20rpx; }
.self .checkbox-wrapper { padding-right: 0; padding-left: 20rpx; }

.checkbox { 
  width: 40rpx; 
  height: 40rpx; 
  border-radius: 50%; 
  border: 2rpx solid #CFD8DC; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  background: $color-white;
}

.checkbox.checked { 
  background: $color-accent; 
  border-color: $color-accent; 
}

.check-icon { font-size: 24rpx; color: #FFF; }

/* 气泡内容容器 */
.content-box { 
  max-width: 70%; 
  margin: 0 20rpx; 
  display: flex; 
  flex-direction: column; 
}

.self .content-box { align-items: flex-end; }

.sender-name { 
  font-size: 20rpx; 
  color: $color-text-sub; 
  margin-bottom: 8rpx; 
  margin-left: 4rpx;
}
.self .sender-name { margin-right: 4rpx; }

/* --- 核心修改：气泡样式修正 --- */
.bubble { 
  padding: 18rpx 24rpx; 
  border-radius: 16rpx; /* 统一圆角，不再有奇怪的尖角 */
  position: relative; 
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); /* 阴影更淡更自然 */
  background: $color-bubble-other;
  min-height: 40rpx;
  display: flex;
  align-items: center;
}

.self .bubble { 
  background: $color-bubble-self; 
  color: $color-white; 
  box-shadow: 0 4rpx 12rpx rgba(74, 111, 165, 0.2);
}

/* 消除图片气泡的背景和内边距 */
.image-bubble {
  padding: 0;
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 12rpx;
  overflow: hidden;
}

/* --- 核心修改：图片尺寸限制 --- */
.msg-image {
  max-width: 200rpx;  /* 限制最大宽度，原来的300rpx太大 */
  max-height: 240rpx; /* 限制最大高度，防止长图刷屏 */
  border-radius: 12rpx;
  display: block;
  /* 保持比例填充 */
  object-fit: cover; 
}

/* 文本内容 */
.msg-text {
  font-size: 28rpx;
  line-height: 1.5;
  color: $color-text-main;
  word-break: break-all;
}

.self .msg-text {
  color: $color-white;
}

/* 4. 底部输入区 */
.input-area-wrapper { 
  flex-shrink: 0; 
  background: $color-white;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.02);
  padding-bottom: calc(constant(safe-area-inset-bottom)); 
  padding-bottom: calc(env(safe-area-inset-bottom)); 
  z-index: 100;
}

.input-bar { 
  display: flex; 
  align-items: center; 
  padding: 16rpx 24rpx; 
  min-height: 100rpx; 
  box-sizing: border-box; 
}

.icon-btn { 
  width: 60rpx; 
  height: 60rpx; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  margin-right: 10rpx; 
}

.iconfont { font-size: 40rpx; color: #78909C; }

.minimal-input { 
  flex: 1; 
  background: #F0F2F5; 
  height: 72rpx; 
  padding: 0 24rpx; 
  border-radius: 12rpx; /* 输入框也方一点 */
  font-size: 28rpx; 
  color: $color-text-main; 
  margin-right: 20rpx;
}

.ph-style { color: #B0BEC5; }

.send-btn { 
  background: $color-primary; 
  color: #FFF; 
  padding: 12rpx 30rpx; 
  border-radius: 12rpx; 
  font-size: 26rpx; 
  font-weight: 600;
  transition: opacity 0.2s;
}

.send-btn:active { opacity: 0.8; }

/* 5. 表情面板 */
.emoji-panel { 
  height: 400rpx; 
  background: #F9FAFB; 
  border-top: 1px solid #EEE; 
}

.emoji-grid { display: flex; flex-wrap: wrap; padding: 20rpx; }

.emoji-item { 
  width: 12.5%; 
  height: 80rpx; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
}

.emoji-icon { width: 48rpx; height: 48rpx; }

/* 6. 删除工具栏 */
.delete-bar { 
  flex-shrink: 0; 
  height: 110rpx; 
  background: $color-white;
  display: flex; 
  align-items: center; 
  justify-content: center; 
  padding-bottom: calc(constant(safe-area-inset-bottom)); 
  padding-bottom: calc(env(safe-area-inset-bottom)); 
}

.delete-btn { 
  color: #FF5252;
  font-weight: 600; 
  font-size: 28rpx; 
  padding: 16rpx 60rpx; 
  border: 1px solid #FFCDD2; 
  border-radius: 40rpx; 
  background: #FFEBEE;
}
</style>