<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="nav-bar">
      <view class="online-status">
        <view class="status-dot"></view>
        <text class="status-text">SQUARE_ONLINE // {{ onlineCount }} USERS</text>
      </view>
    </view>

    <scroll-view 
      scroll-y 
      class="chat-area" 
      :scroll-into-view="scrollTarget"
      scroll-with-animation
    >
      <view class="system-msg">--- CONNECTION ESTABLISHED ---</view>

      <view 
        v-for="(msg, index) in messages" 
        :key="msg.id || index" 
        class="msg-row"
        :class="{ 'self': msg.user_id === myInfo.id }"
        :id="'msg-' + index"
      >
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

    <view class="input-bar">
      <input 
        class="cyber-input" 
        v-model="inputText" 
        placeholder="BROADCAST MESSAGE..." 
        placeholder-class="ph-style"
        confirm-type="send"
        @confirm="sendMessage"
      />
      <view class="send-btn" @click="sendMessage">➤</view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { io } from "socket.io-client";

const FLASK_URL = 'http://192.168.10.26:5000'; // Flask 地址
const NODE_URL = 'http://192.168.10.26:3000';  // Node.js 地址

const socket = ref(null);
const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTarget = ref('');
const onlineCount = ref(0); // 模拟在线人数

onShow(() => {
  const user = uni.getStorageSync('userInfo');
  if (!user) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 1000);
    return;
  }
  myInfo.value = user;

  // 1. 加载历史消息 (Flask)
  fetchHistory();

  // 2. 连接 WebSocket (Node.js)
  connectSocket();
});

onUnmounted(() => {
  if (socket.value) socket.value.disconnect();
});

// 获取头像的完整路径
const formatAvatar = (path) => {
  if (!path) return '/static/logo.png';
  if (path.startsWith('http')) return path;
  return `${FLASK_URL}${path}`;
};

const fetchHistory = () => {
  uni.request({
    url: `${FLASK_URL}/api/square/history`,
    success: (res) => {
      if (res.data.code === 200) {
        messages.value = res.data.data;
        scrollToBottom();
      }
    }
  });
};

const connectSocket = () => {
  // 如果已经连接，先断开
  if (socket.value && socket.value.connected) return;

  socket.value = io(NODE_URL, {
    transports: ['websocket'], // 强制使用 websocket
    reconnection: true
  });

  socket.value.on("connect", () => {
    console.log("🟢 Socket Connected:", socket.value.id);
    // 加入广场频道 (后端代码里我们是 join('user_id')，其实广播是用 io.emit 的，所以连上就能收)
    onlineCount.value = Math.floor(Math.random() * 20) + 5; // 假装有人
  });

  // 监听新消息
  socket.value.on("new_message", (msg) => {
    console.log("📩 收到消息:", msg);
    
    // Node.js 传回来的 msg 只有 user_id，我们需要补全头像和名字以便显示
    // 实际生产中，Node.js 应该查库或者 Redis 带回用户信息。
    // 这里为了简化，如果收到的是自己发的，就直接显示；如果是别人的，暂时可能缺头像(除非后端改一下)。
    // 💡 聪明做法：Node.js 转发时 data 里面其实可以带上用户信息。
    // 我们先按现有逻辑处理：
    
    // 如果消息里没有 username (Node.js 那个代码里确实没查库返回 username)，
    // 我们暂时显示 "UNKNOWN" 或者让后端改一下。
    // 为了不改后端，我们在前端做一个小补丁：
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
  inputText.value = ''; // 清空输入框

  // 发送给 Node.js
  // 注意：我们在 index.js 里监听的是 'send_message'
  // 并且存库时只存了 content。为了让广播出来时能带头像，我们把用户信息也发过去
  // (虽然这是不安全的做法，正式环境应该由后端通过 Token 获取，但这里用于演示完全 OK)
  socket.value.emit("send_message", {
    user_id: myInfo.value.id,
    content: content,
    // 🔥 把头像和名字“夹带”在消息里发给服务器，服务器广播回来时大家就都有头像了
    // 你需要修改一下 Node.js 的 index.js 里的广播逻辑 (io.emit) 把整个 data 转发出去
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
/* 赛博风格样式 */
page { background-color: #050505; height: 100vh; overflow: hidden; font-family: 'Courier New', monospace; }
.container { height: 100vh; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 50%, #111 0%, #000 90%); z-index: -1; }

.nav-bar { height: 44px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #333; background: rgba(0,0,0,0.8); backdrop-filter: blur(5px); }
.online-status { display: flex; align-items: center; }
.status-dot { width: 8px; height: 8px; background: #00ff9d; border-radius: 50%; box-shadow: 0 0 5px #00ff9d; margin-right: 8px; animation: blink 2s infinite; }
.status-text { color: #00ff9d; font-size: 12px; letter-spacing: 1px; }

.chat-area { flex: 1; padding: 15px; box-sizing: border-box; }
.system-msg { text-align: center; color: #333; font-size: 10px; margin: 20px 0; letter-spacing: 2px; }

.msg-row { display: flex; margin-bottom: 20px; align-items: flex-start; }
.msg-row.self { flex-direction: row-reverse; }

.avatar { width: 40px; height: 40px; border-radius: 4px; border: 1px solid #333; background: #111; }
.content-box { max-width: 70%; margin: 0 10px; display: flex; flex-direction: column; }
.self .content-box { align-items: flex-end; }

.sender-name { font-size: 10px; color: #666; margin-bottom: 4px; }
.bubble { background: #1a1a1a; border: 1px solid #333; padding: 10px 15px; border-radius: 4px; position: relative; }
.self .bubble { background: rgba(0, 243, 255, 0.15); border-color: #00f3ff; color: #fff; }
.bubble text { font-size: 14px; color: #ddd; line-height: 1.4; word-break: break-all; }

/* 底部输入栏 */
.input-bar { height: 60px; background: #080808; border-top: 1px solid #333; display: flex; align-items: center; padding: 0 15px; }
.cyber-input { flex: 1; background: #111; border: 1px solid #333; height: 36px; padding: 0 10px; color: #fff; font-size: 14px; transition: all 0.3s; }
.cyber-input:focus { border-color: #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }
.ph-style { color: #444; }
.send-btn { width: 40px; height: 36px; background: #00f3ff; color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 10px; clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); }
.send-btn:active { opacity: 0.8; }

@keyframes blink { 0%,100% {opacity:1} 50% {opacity:0.5} }
</style>