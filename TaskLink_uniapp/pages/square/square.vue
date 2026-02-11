<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="nav-bar-wrapper">
      <view class="status-bar"></view>
      <view class="nav-content">
        <view v-if="!isSelectionMode" class="online-status">
          <view class="status-dot"></view>
          <text class="status-text">在线: {{ onlineCount }}</text>
        </view>
        <view v-else class="selection-header">
          <text class="selection-title">已选择 {{ selectedIds.length }} 项</text>
          <text class="cancel-btn" @click="exitSelectionMode">取消</text>
        </view>
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
      <view class="system-msg">--- 已连接到公共频道 ---</view>

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
            <text v-if="selectedIds.includes(msg.id)">✓</text>
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
            :style="msg.type === 'image' ? 'background: transparent; border: none; padding: 0;' : ''"
          >
            <image 
              v-if="msg.type === 'image'"
              :src="formatAvatar(msg.content)" 
              mode="widthFix" 
              style="max-width: 200px; border-radius: 8px; display: block;"
              @click.stop="previewImage(msg.content)"
            ></image>

            <rich-text 
              v-else
              :nodes="parseEmoji(msg.content)" 
              style="font-size: 15px; line-height: 24px; color: #e0e0e0;"
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
        <view class="emoji-btn" @click.stop="toggleEmojiPanel">
          <text style="font-size: 24px;">☺</text>
        </view>

        <view class="emoji-btn" @click="chooseImage" style="margin-left: 10px;">
          <text style="font-size: 24px;">📷</text>
        </view>

        <input 
          class="cyber-input" 
          v-model="inputText" 
          placeholder="输入消息..." 
          placeholder-class="ph-style"
          confirm-type="send"
          @confirm="sendMessage"
          @focus="closeEmojiPanel"
          style="margin-left: 10px;"
        />
        <view class="send-btn" @click="sendMessage">➤</view>
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
        <text>删除 ({{ selectedIds.length }})</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue';
import { onUnload, onShow, onHide } from '@dcloudio/uni-app';

// ⚠️ 请确保你的 FLASK_URL 是正确的
const FLASK_URL = `http://101.35.132.175:5000`;

const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTarget = ref('');
const onlineCount = ref(1);
const isSelectionMode = ref(false); 
const selectedIds = ref([]);  
const showEmojiPanel = ref(false); 

// 🔥 新增：页面活跃状态锁
const isPageActive = ref(true);

// --- 辅助函数：获取 Token ---
const getToken = () => {
  const user = uni.getStorageSync('userInfo');
  return user ? user.token : '';
};

// --- 生命周期 ---

onShow(() => {
  isPageActive.value = true; // 页面显示，解锁
  
  const app = getApp();
  if (app.globalData) app.globalData.isSquareOpen = true; 
  uni.removeTabBarBadge({ index: 1 });
  
  const user = uni.getStorageSync('userInfo');
  // 🔥 校验 Token 是否存在，不存在直接踢
  if (!user || !user.token) {
    uni.reLaunch({ url: '/pages/login/login' });
    return;
  }
  myInfo.value = user;
  
  fetchHistory();
  
  // 🔥 监听全局消息
  uni.$off('global_new_message'); // 先移除防止重复
  uni.$on('global_new_message', (msg) => {
      // 🔒 安全检查：如果页面已经隐藏或销毁，不要更新 UI，防止报错
      if (!isPageActive.value) return;

      console.log('Square 收到:', msg);
      
      // 前端去重（双重保险）
      if (messages.value.length > 0) {
          const last = messages.value[messages.value.length - 1];
          // 假设 ID 重复或者是同一时间戳
          if (last.id === msg.id || (last.content === msg.content && last.user_id === msg.user_id && Date.now() - new Date(last.created_at || 0).getTime() < 500)) {
              return;
          }
      }
      
      messages.value.push(msg);
      scrollToBottom();
  });
  
  // 确保 Socket 连接
  if (app.initSocket) app.initSocket();

  const socket = app.globalData.socket;
  if (socket) {
      socket.off('update_online_count');
      socket.on('update_online_count', (count) => { 
          if (isPageActive.value) onlineCount.value = count; 
      });
  }
});

onHide(() => {
  isPageActive.value = false; // 页面隐藏，上锁
  
  const app = getApp();
  if (app.globalData) app.globalData.isSquareOpen = false;
  
  // 移除监听器，防止后台更新 DOM 报错
  uni.$off('global_new_message');
  uni.$off('update_online_count');
});

onUnmounted(() => {
  isPageActive.value = false;
  uni.$off('global_new_message');
});

// --- 发送消息逻辑 ---

const sendSocketMessage = (content, type = 'text') => {
  const app = getApp();
  const socket = app.globalData.socket;
  
  if (!socket || !socket.connected) {
      uni.showToast({ title: '连接断开', icon: 'none' });
      if(app.initSocket) app.initSocket();
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

// ... (chooseImage, uploadImage 等逻辑保持不变，略) ...

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
    // 🔥🔥🔥 上传图片也要带 Token (如果后端有鉴权) 🔥🔥🔥
    header: {
        'Authorization': getToken() 
    },
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
    return `<img style="width:24px; height:24px; vertical-align:middle;" src="${FLASK_URL}/static/emoji/${f}.gif" />`;
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

// 🔥🔥🔥 核心修改：获取历史记录 🔥🔥🔥
const fetchHistory = () => {
    uni.request({
        // ❌ 不再传 user_id 参数，靠 Token 识别
        url: `${FLASK_URL}/api/square/history`, 
        // ✅ 必须带 Header
        header: {
            'Authorization': getToken()
        },
        success: (res) => {
            // 🔥 401/403 封号或过期处理
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
        fail: (err) => {
            console.error('History fetch failed', err);
        }
    });
};

const scrollToBottom = () => {
  // 🔒 加锁：防止页面销毁后操作 DOM
  if (!isPageActive.value) return;
  
  scrollTarget.value = '';
  nextTick(() => { 
      if (isPageActive.value) scrollTarget.value = 'bottom-anchor'; 
  });
};
</script>

<style>
/* 保持原有样式 */
page { background-color: #050505; height: 100vh; overflow: hidden; font-family: 'Courier New', monospace; }
.container { height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 50%, #111 0%, #000 90%); z-index: -1; }
.nav-bar-wrapper { background: rgba(0,0,0,0.8); backdrop-filter: blur(5px); border-bottom: 1px solid #333; width: 100%; flex-shrink: 0; z-index: 999; }
.status-bar { height: var(--status-bar-height); width: 100%; }
.nav-content { height: 44px; display: flex; align-items: center; padding: 0 15px; justify-content: space-between; }
.online-status { display: flex; align-items: center; }
.status-dot { width: 8px; height: 8px; background: #00ff9d; border-radius: 50%; box-shadow: 0 0 5px #00ff9d; margin-right: 8px; animation: blink 2s infinite; }
.status-text { color: #00ff9d; font-size: 14px; font-weight: bold; }
.selection-header { display: flex; width: 100%; justify-content: space-between; align-items: center; }
.selection-title { color: #fff; font-size: 16px; font-weight: bold; }
.cancel-btn { color: #888; font-size: 14px; padding: 5px 10px; }
.chat-area { flex: 1; height: 0; width: 100%; padding: 15px; box-sizing: border-box; }
.msg-row { display: flex; margin-bottom: 20px; align-items: flex-start; transition: all 0.3s; }
.msg-row.self { flex-direction: row-reverse; }
.msg-row.selecting { opacity: 0.5; } 
.checkbox-wrapper { display: flex; align-items: center; padding: 0 10px; }
.checkbox-wrapper + .avatar, .checkbox-wrapper + .content-box { opacity: 1; }
.checkbox { width: 20px; height: 20px; border-radius: 50%; border: 2px solid #555; display: flex; align-items: center; justify-content: center; margin-right: 10px; }
.checkbox.checked { background: #00f3ff; border-color: #00f3ff; }
.checkbox text { font-size: 12px; color: #000; font-weight: bold; }
.avatar { width: 40px; height: 40px; border-radius: 4px; border: 1px solid #333; background: #111; }
.content-box { max-width: 70%; margin: 0 10px; display: flex; flex-direction: column; }
.self .content-box { align-items: flex-end; }
.sender-name { font-size: 10px; color: #666; margin-bottom: 4px; }
.bubble { background: #1a1a1a; border: 1px solid #333; padding: 10px 15px; border-radius: 4px; position: relative; }
.self .bubble { background: rgba(0, 243, 255, 0.15); border-color: #00f3ff; color: #fff; }
.system-msg { text-align: center; color: #333; font-size: 10px; margin: 20px 0; letter-spacing: 2px; }
.input-area-wrapper { flex-shrink: 0; background: #080808; border-top: 1px solid #333; display: flex; flex-direction: column; padding-bottom: calc(constant(safe-area-inset-bottom)); padding-bottom: calc(env(safe-area-inset-bottom)); }
.input-bar { display: flex; align-items: center; padding: 10px 15px; height: 60px; box-sizing: border-box; }
.emoji-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; margin-right: 10px; color: #888; border: 1px solid #333; border-radius: 4px; background: #111; line-height: 1; padding-bottom: 4px; }
.emoji-btn:active { background: #222; color: #00f3ff; border-color: #00f3ff; }
.emoji-btn text { font-size: 22px; }
.cyber-input { flex: 1; background: #111; border: 1px solid #333; height: 36px; padding: 0 10px; color: #fff; font-size: 14px; transition: all 0.3s; }
.cyber-input:focus { border-color: #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }
.ph-style { color: #444; }
.send-btn { width: 40px; height: 36px; background: #00f3ff; color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 10px; clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); }
.emoji-panel { height: 200px; background: #111; border-top: 1px solid #333; transition: all 0.3s; }
.emoji-grid { display: flex; flex-wrap: wrap; padding: 10px; }
.emoji-item { width: 12.5%; height: 40px; display: flex; align-items: center; justify-content: center; } 
.emoji-icon { width: 28px; height: 28px; }
.delete-bar { flex-shrink: 0; height: 60px; background: #1a0505; border-top: 1px solid #ff003c; display: flex; align-items: center; justify-content: center; padding-bottom: calc(10px + constant(safe-area-inset-bottom)); padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
.delete-btn { color: #ff003c; font-weight: bold; font-size: 16px; padding: 10px 30px; border: 1px solid #ff003c; border-radius: 20px; background: rgba(255, 0, 60, 0.1); }
.delete-btn:active { background: #ff003c; color: #fff; }
@keyframes blink { 0%,100% {opacity:1} 50% {opacity:0.5} }
</style>