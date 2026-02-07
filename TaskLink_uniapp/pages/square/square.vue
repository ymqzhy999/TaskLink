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
        @longpress="onLongPressMessage(msg)"
        @click="onSelectMessage(msg)"
      >
        <view v-if="isSelectionMode" class="checkbox-wrapper">
          <view class="checkbox" :class="{ 'checked': selectedIds.includes(msg.id) }">
            <text v-if="selectedIds.includes(msg.id)">✓</text>
          </view>
        </view>

        <image 
          v-if="msg.user_id !== myInfo.id" 
          class="avatar" 
          :src="formatAvatar(msg.avatar)" 
          mode="aspectFill"
        ></image>

        <view class="content-box">
          <text class="sender-name" v-if="msg.user_id !== myInfo.id">{{ msg.username }}</text>
          <view class="bubble">
            <text>{{ msg.content }}</text>
          </view>
        </view>

        <image 
          v-if="msg.user_id === myInfo.id" 
          class="avatar right" 
          :src="formatAvatar(msg.avatar)" 
          mode="aspectFill"
        ></image>
      </view>

      <view id="bottom-anchor" style="height: 20px;"></view>
    </scroll-view>

    <view v-if="!isSelectionMode" class="input-bar">
      <input 
        class="cyber-input" 
        v-model="inputText" 
        placeholder="输入消息..." 
        placeholder-class="ph-style"
        confirm-type="send"
        @confirm="sendMessage"
      />
      <view class="send-btn" @click="sendMessage">➤</view>
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
import { onShow } from '@dcloudio/uni-app';
import io from '@hyoga/uni-socket.io'; 

// 记得改成你自己的 IP
const FLASK_URL = 'http://192.168.10.26:5000'; 
const NODE_URL = 'http://192.168.10.26:3000';

const socket = ref(null);
const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTarget = ref('');
const onlineCount = ref(1);

const isSelectionMode = ref(false); 
const selectedIds = ref([]);        

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (!user) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 1000);
    return;
  }
  myInfo.value = user;

  fetchHistory();
  connectSocket();
});

onUnmounted(() => {
  if (socket.value) socket.value.disconnect();
});

// --- 长按逻辑 (修正：允许删除任何人消息) ---
const onLongPressMessage = (msg) => {
  // 🔥 去掉了 user_id 的判断，现在长按谁的都可以删
  isSelectionMode.value = true;
  selectedIds.value = [msg.id]; 
  uni.vibrateShort(); 
};

// --- 选择逻辑 (修正：允许选择任何人消息) ---
const onSelectMessage = (msg) => {
  if (!isSelectionMode.value) return;
  
  const index = selectedIds.value.indexOf(msg.id);
  if (index > -1) {
    selectedIds.value.splice(index, 1); 
  } else {
    selectedIds.value.push(msg.id); 
  }
};

const exitSelectionMode = () => {
  isSelectionMode.value = false;
  selectedIds.value = [];
};

const confirmDelete = () => {
  if (selectedIds.value.length === 0) return;

  uni.showModal({
    title: '删除消息',
    content: '删除后仅自己不可见，确定吗？', // 提示文案也改得更准确了
    success: (res) => {
      if (res.confirm) {
        doLocalDelete();
      }
    }
  });
};

// --- 🔥 核心修正：执行本地删除 🔥 ---
const doLocalDelete = () => {
  const storageKey = `deleted_msgs_${myInfo.value.id}`;
  
  // 1. 获取以前删过的 ID 列表
  let oldDeletedIds = uni.getStorageSync(storageKey) || [];
  
  // 2. 合并这次删的 (去重)
  const newDeletedIds = [...new Set([...oldDeletedIds, ...selectedIds.value])];
  
  // 3. 存回缓存
  uni.setStorageSync(storageKey, newDeletedIds);
  
  // 4. 从当前视图中移除
  messages.value = messages.value.filter(m => !selectedIds.value.includes(m.id));
  
  // 5. 退出模式
  exitSelectionMode();
  uni.showToast({ title: '已清理', icon: 'none' });
};

const formatAvatar = (path) => {
  if (!path) return '/static/logo.png';
  const fullPath = path.startsWith('http') ? path : `${FLASK_URL}${path}`;
  return fullPath; 
};

// --- 🔥 历史记录逻辑修正：过滤掉删过的 ---
const fetchHistory = () => {
  uni.request({
    url: `${FLASK_URL}/api/square/history`,
    success: (res) => {
      if (res.data.code === 200) {
        const allMessages = res.data.data;
        
        // 读取本地“删除黑名单”
        const storageKey = `deleted_msgs_${myInfo.value.id}`;
        const deletedIds = uni.getStorageSync(storageKey) || [];
        
        // 过滤：如果 ID 在黑名单里，就不显示
        messages.value = allMessages.filter(m => !deletedIds.includes(m.id));
        
        scrollToBottom();
      }
    }
  });
};

const connectSocket = () => {
  if (socket.value && socket.value.connected) return;

  socket.value = io(NODE_URL, {
    query: {},
    transports: ['websocket', 'polling'],
    timeout: 5000,
  });

  socket.value.on("connect", () => {
    console.log("🟢 Socket Connected");
  });

  socket.value.on("update_online_count", (count) => {
    onlineCount.value = count;
  });

  // 注意：这里不需要监听 "message_deleted" 了，因为我们现在是“删给自己看”

  socket.value.on("new_message", (msg) => {
    if (msg.user_id === myInfo.value.id) {
        msg.username = myInfo.value.username;
        msg.avatar = myInfo.value.avatar;
    }
    messages.value.push(msg);
    scrollToBottom();
  });
};

const sendMessage = () => {
  if (!inputText.value.trim()) return;
  const content = inputText.value;
  inputText.value = ''; 

  socket.value.emit("send_message", {
    user_id: myInfo.value.id,
    content: content,
    username: myInfo.value.username, 
    avatar: myInfo.value.avatar
  });
};

const scrollToBottom = () => {
  scrollTarget.value = '';
  nextTick(() => {
    scrollTarget.value = 'bottom-anchor';
  });
};
</script>

<style>
/* ... (样式保持之前的不变) ... */
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
.bubble text { font-size: 14px; color: #ddd; line-height: 1.4; word-break: break-all; }
.system-msg { text-align: center; color: #333; font-size: 10px; margin: 20px 0; letter-spacing: 2px; }
.input-bar { flex-shrink: 0; min-height: 60px; background: #080808; border-top: 1px solid #333; display: flex; align-items: center; padding: 10px 15px; padding-bottom: calc(10px + constant(safe-area-inset-bottom)); padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
.cyber-input { flex: 1; background: #111; border: 1px solid #333; height: 36px; padding: 0 10px; color: #fff; font-size: 14px; transition: all 0.3s; }
.cyber-input:focus { border-color: #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }
.ph-style { color: #444; }
.send-btn { width: 40px; height: 36px; background: #00f3ff; color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 10px; clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); }
.delete-bar { flex-shrink: 0; height: 60px; background: #1a0505; border-top: 1px solid #ff003c; display: flex; align-items: center; justify-content: center; padding-bottom: calc(10px + constant(safe-area-inset-bottom)); padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
.delete-btn { color: #ff003c; font-weight: bold; font-size: 16px; padding: 10px 30px; border: 1px solid #ff003c; border-radius: 20px; background: rgba(255, 0, 60, 0.1); }
.delete-btn:active { background: #ff003c; color: #fff; }
@keyframes blink { 0%,100% {opacity:1} 50% {opacity:0.5} }
</style>