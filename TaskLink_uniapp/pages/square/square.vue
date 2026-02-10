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
// 🔥 必须引入 onHide，这是修复连接问题的关键
import { onUnload, onLoad, onShow, onHide } from '@dcloudio/uni-app';
import io from '@hyoga/uni-socket.io'; 

// --- 1. 配置服务器地址 ---
const SERVICE_HOST = import.meta.env.VITE_SERVICE_HOST || '127.0.0.1'; // 如果在真机运行，请确保这里是你的局域网IP
const FLASK_URL = `http://${SERVICE_HOST}:5000`;
const NODE_URL = `http://${SERVICE_HOST}:3000`;

// --- 2. 状态变量 ---
const socket = ref(null);
const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTarget = ref('');
const onlineCount = ref(1);
const isSelectionMode = ref(false); 
const selectedIds = ref([]);  
const showEmojiPanel = ref(false); 

// --- 3. 生命周期管理 (修复核心) ---

onShow(() => {
  // 隐藏 TabBar 数字（可选）
  uni.removeTabBarBadge({ index: 1 });
  
  // 检查登录状态
  const user = uni.getStorageSync('userInfo');
  if (!user) {
    uni.showToast({ title: '请先登录', icon: 'none' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 1000);
    return;
  }
  myInfo.value = user;
  
  // 拉取历史消息
  fetchHistory();
  
  // 🔥 页面显示时：建立连接
  connectSocket();
});

// 🔥 页面隐藏时（切换Tab）：断开连接
onHide(() => {
  closeSocket();
});

// 页面卸载时：断开连接
onUnload(() => {
  closeSocket();
});

onUnmounted(() => {
  closeSocket();
});

// --- 4. Socket 连接逻辑 (修复核心) ---

const closeSocket = () => {
  if (socket.value) {
    socket.value.disconnect(); // 断开链接
    socket.value = null;       // 清空对象
    console.log("🔴 Socket 已断开 (页面隐藏/卸载)");
  }
};

const connectSocket = () => {
  // 🔥 防御性编程：如果当前有连接，先强制断开，防止重复绑定监听器
  if (socket.value) {
     closeSocket();
  }

  console.log("🟡 正在连接 Socket...");
  socket.value = io(NODE_URL, {
    query: {},
    transports: ['websocket', 'polling'],
    timeout: 5000,
    forceNew: true // 强制创建新连接
  });

  // 监听连接成功
  socket.value.on("connect", () => { 
      console.log("🟢 Socket 连接成功 ID:", socket.value.id); 
      // 连接成功后，可以发一个 join 事件（如果后端需要）
      socket.value.emit('join', myInfo.value.id);
  });
  
  // 监听在线人数
  socket.value.on("update_online_count", (count) => { 
      onlineCount.value = count; 
  });
  
  // 监听新消息
  socket.value.on("new_message", (msg) => {
    // 简单防重（可选）：防止极短时间内收到重复ID
    // if (messages.value.length > 0 && messages.value[messages.value.length - 1].id === msg.id) return;

    // 修正当前用户的头像和昵称显示（如果是自己发的）
    if (msg.user_id === myInfo.value.id) {
        msg.username = myInfo.value.username;
        msg.avatar = myInfo.value.avatar;
    }
    
    messages.value.push(msg);
    scrollToBottom();
  });
};

// --- 5. 发送消息逻辑 ---

// 通用发送函数
const sendSocketMessage = (content, type = 'text') => {
  if (!socket.value) {
      uni.showToast({ title: '连接已断开，正在重连...', icon: 'none' });
      connectSocket();
      return;
  }
  
  socket.value.emit("send_message", {
    user_id: myInfo.value.id,
    content: content,
    type: type, // text 或 image
    username: myInfo.value.username, 
    avatar: myInfo.value.avatar
  });
};

// 点击发送按钮
const sendMessage = () => {
  if (!inputText.value.trim()) return;
  const content = inputText.value;
  
  // 清空输入框和面板
  inputText.value = ''; 
  showEmojiPanel.value = false;
  
  sendSocketMessage(content, 'text');
};

// --- 6. 图片发送功能 ---

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const filePath = res.tempFilePaths[0];
      uploadImage(filePath);
    }
  });
};

const uploadImage = (filePath) => {
  uni.showLoading({ title: '发送中...' });
  uni.uploadFile({
    url: `${FLASK_URL}/api/chat/upload`,
    filePath: filePath,
    name: 'file',
    success: (uploadFileRes) => {
      uni.hideLoading();
      try {
        const data = JSON.parse(uploadFileRes.data);
        if (data.code === 200) {
          // 上传成功，发送 Socket 消息
          const imageUrl = data.data.url;
          sendSocketMessage(imageUrl, 'image');
        } else {
          uni.showToast({ title: '上传失败: ' + data.msg, icon: 'none' });
        }
      } catch (e) {
        console.error(e);
        uni.showToast({ title: '图片解析失败', icon: 'none' });
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: '网络错误', icon: 'none' });
    }
  });
};

const previewImage = (url) => {
  const fullUrl = formatAvatar(url);
  uni.previewImage({
    urls: [fullUrl],
    current: fullUrl
  });
};

// --- 7. 表情包功能 ---

const toggleEmojiPanel = () => {
  showEmojiPanel.value = !showEmojiPanel.value;
  if(showEmojiPanel.value) {
    uni.hideKeyboard(); 
    scrollToBottom();
  }
};

const closeEmojiPanel = () => {
  showEmojiPanel.value = false;
};

const selectEmoji = (index) => {
  // 插入表情代码
  inputText.value += `[face:${index}]`;
};

const parseEmoji = (content) => {
  if (!content) return '';
  // 解析 [face:1] -> <img src="...">
  return content.replace(/\[face:(\d+)\]/g, (match, id) => {
    const filename = id.toString().padStart(2, '0');
    const serverUrl = `${FLASK_URL}/static/emoji/${filename}.gif`;
    return `<img style="width:24px; height:24px; vertical-align:middle; margin:0 2px;" src="${serverUrl}" />`;
  });
};

// --- 8. 消息删除与多选功能 ---

const onLongPressMessage = (msg) => {
  isSelectionMode.value = true;
  selectedIds.value = [msg.id]; 
  uni.vibrateShort(); 
};

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
    content: '删除后仅自己不可见，确定吗？',
    success: (res) => {
      if (res.confirm) {
        doLocalDelete();
      }
    }
  });
};

const doLocalDelete = () => {
  const storageKey = `deleted_msgs_${myInfo.value.id}`;
  let oldDeletedIds = uni.getStorageSync(storageKey) || [];
  // 合并并去重
  const newDeletedIds = [...new Set([...oldDeletedIds, ...selectedIds.value])];
  uni.setStorageSync(storageKey, newDeletedIds);
  
  // 更新视图
  messages.value = messages.value.filter(m => !selectedIds.value.includes(m.id));
  exitSelectionMode();
  uni.showToast({ title: '已清理', icon: 'none' });
};

// --- 9. 辅助功能 ---

const formatAvatar = (path) => {
  if (!path) return '/static/logo.png';
  const fullPath = path.startsWith('http') ? path : `${FLASK_URL}${path}`;
  return fullPath; 
};

const fetchHistory = () => {
  uni.request({
    url: `${FLASK_URL}/api/square/history`,
    success: (res) => {
      if (res.data.code === 200) {
        const allMessages = res.data.data;
        // 过滤掉本地已删除的消息
        const storageKey = `deleted_msgs_${myInfo.value.id}`;
        const deletedIds = uni.getStorageSync(storageKey) || [];
        messages.value = allMessages.filter(m => !deletedIds.includes(m.id));
        scrollToBottom();
      }
    }
  });
};

const scrollToBottom = () => {
  scrollTarget.value = '';
  nextTick(() => { scrollTarget.value = 'bottom-anchor'; });
};
</script>

<style>
/* 保持原有基础样式 */
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

/* --- 底部输入区域 (新) --- */
.input-area-wrapper { flex-shrink: 0; background: #080808; border-top: 1px solid #333; display: flex; flex-direction: column; padding-bottom: calc(constant(safe-area-inset-bottom)); padding-bottom: calc(env(safe-area-inset-bottom)); }

.input-bar { display: flex; align-items: center; padding: 10px 15px; height: 60px; box-sizing: border-box; }

.emoji-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; margin-right: 10px; color: #888; border: 1px solid #333; border-radius: 4px; background: #111; }
.emoji-btn:active { background: #222; color: #00f3ff; border-color: #00f3ff; }

.cyber-input { flex: 1; background: #111; border: 1px solid #333; height: 36px; padding: 0 10px; color: #fff; font-size: 14px; transition: all 0.3s; }
.cyber-input:focus { border-color: #00f3ff; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }
.ph-style { color: #444; }
.send-btn { width: 40px; height: 36px; background: #00f3ff; color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 10px; clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); }

/* --- 表情面板 (新) --- */
.emoji-panel { height: 200px; background: #111; border-top: 1px solid #333; transition: all 0.3s; }
.emoji-grid { display: flex; flex-wrap: wrap; padding: 10px; }
.emoji-item { width: 12.5%; height: 40px; display: flex; align-items: center; justify-content: center; } /* 一行8个 */
.emoji-icon { width: 28px; height: 28px; }

.delete-bar { flex-shrink: 0; height: 60px; background: #1a0505; border-top: 1px solid #ff003c; display: flex; align-items: center; justify-content: center; padding-bottom: calc(10px + constant(safe-area-inset-bottom)); padding-bottom: calc(10px + env(safe-area-inset-bottom)); }
.delete-btn { color: #ff003c; font-weight: bold; font-size: 16px; padding: 10px 30px; border: 1px solid #ff003c; border-radius: 20px; background: rgba(255, 0, 60, 0.1); }
.delete-btn:active { background: #ff003c; color: #fff; }
@keyframes blink { 0%,100% {opacity:1} 50% {opacity:0.5} }
/* 找到这个类，替换为以下代码 */
.emoji-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  color: #888;
  border: 1px solid #333;
  border-radius: 4px;
  background: #111;
  
  /* 🔥 新增这两行：消除字体行高影响，微调垂直位置 */
  line-height: 1; 
  padding-bottom: 4px; /* 向上提一点 */
}

/* 另外，给相机图标单独加个微调（如果你觉得还是歪） */
.emoji-btn text {
    font-size: 22px; /* 稍微改小一点点 */
}
</style>