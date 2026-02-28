<template>
  <view class="container" :class="{ 'dark': isDarkMode }">
    <view class="nav-header">
      <view class="nav-content">
        <view class="header-left">
          <text class="page-title">Community</text>
          <view class="online-badge">
            <view class="dot"></view>
            <text>{{ onlineCount }} Online</text>
          </view>
        </view>
      </view>
    </view>

    <scroll-view 
      scroll-y 
      class="chat-area" 
      :scroll-top="scrollTop"
      scroll-with-animation
      :enable-back-to-top="true"
      :lower-threshold="100"
      @scrolltoupper="loadMoreHistory"
      @scrolltolower="onScrollToLower"
      @click="closeEmojiPanel"
    >
      <view class="system-msg">
        <text class="system-text">—— 欢迎来到 TaskLink 公共频道 ——</text>
      </view>

      <!-- 加载更多提示 -->
      <view v-if="isLoadingMore" class="loading-more">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="!hasMoreHistory && messages.length > 0" class="loading-more">
        <text class="loading-text">没有更多消息了</text>
      </view>

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
          :src="formatAvatar(msg.avatar, msg)" 
          mode="aspectFill"
        ></image>

        <view class="content-box">
          <view class="name-time-bar">
            <text class="sender-name" v-if="msg.user_id !== myInfo.id">{{ msg.username }}</text>
            <text class="msg-time">{{ formatMsgTime(msg.created_at) }}</text>
          </view>
          
          <view 
            class="bubble" 
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
              :nodes="parseEmoji(msg.content, msg)" 
              class="msg-text"
            ></rich-text>
          </view>
        </view>

        <image 
          v-if="msg.user_id === myInfo.id" 
          class="avatar right" 
          :src="formatAvatar(msg.avatar)" 
          mode="aspectFill"
        ></image>
      </view>
    </scroll-view>

    <view class="input-area-wrapper">
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
                :src="`${API_BASE}/static/emoji/${(i-1).toString().padStart(2, '0')}.gif`" 
                class="emoji-icon"
              ></image>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, onUnmounted } from 'vue';
import { onUnload, onShow, onHide } from '@dcloudio/uni-app';
import { useTheme } from '@/utils/useTheme';
import { get, post } from '@/utils/request.js';
import { API_BASE } from '@/utils/api.js';
import useSocket from '@/composables/useSocket.js';

const { initSocket, emit, on, off, socket } = useSocket();

const myInfo = ref({});
const messages = ref([]);
const inputText = ref('');
const scrollTop = ref(0);
const onlineCount = ref(1);
const showEmojiPanel = ref(false); 
const isLoadingMore = ref(false);  // 加载更多中
const hasMoreHistory = ref(true);  // 是否还有更多历史
const historyOffset = ref(0);      // 当前偏移量
const { isDarkMode } = useTheme();

// 页面活跃锁
const isPageActive = ref(true);

// onShow 时初始化 Socket 连接并监听消息
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
  
  // 拉取聊天历史
  fetchHistory();
  
  // 监听全局新消息
  uni.$off('global_new_message'); 
  uni.$on('global_new_message', (msg) => {
    if (!isPageActive.value) return;
    console.log('Square 收到:', msg);
    
    // 清理损坏的 HTML 格式
    if (msg.content) {
      if (msg.content.includes('<<span') || msg.content.includes('<<strong') || msg.content.includes('<<code')) {
        msg.content = msg.content.replace(/<</g, '');
      }
    }
    
    // 简单去重：检查数组中是否已存在相同 id 的消息
    if (msg.id && messages.value.some(m => m.id === msg.id)) {
      return;
    }
    
    messages.value.push(msg);
    scrollToBottom();
  });
  
  // 监听在线人数变化
  uni.$off('global_online_count');
  uni.$on('global_online_count', (count) => {
    if (isPageActive.value) onlineCount.value = count;
  });
  
  // 用抽离出去的 useSocket 来初始化连接
  const socketInstance = initSocket();
  
  // 监听在线人数
  if (socketInstance) {
    socketInstance.on('update_online_count', (count) => { 
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

// 💡 时间格式化函数
const formatMsgTime = (timeStr) => {
  if (!timeStr) return '';
  
  // 如果已经是 Date 对象，转为字符串
  let str = timeStr;
  if (timeStr instanceof Date) {
    str = timeStr.toISOString();
  } else if (typeof timeStr === 'object') {
    // 处理其他对象格式
    str = JSON.stringify(timeStr);
  }
  
  // 兼容 iOS 日期格式问题
  const validTimeStr = str.replace(/-/g, '/').replace('T', ' ').split('.')[0];
  const date = new Date(validTimeStr);
  
  if (isNaN(date.getTime())) {
    // 降级处理：尝试直接解析原始字符串
    const fallbackDate = new Date(timeStr);
    if (isNaN(fallbackDate.getTime())) return '';
    const pad = (n) => (n < 10 ? '0' + n : n);
    return `${pad(fallbackDate.getHours())}:${pad(fallbackDate.getMinutes())}`;
  }
  
  const pad = (n) => (n < 10 ? '0' + n : n);
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

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
                avatar: myInfo.value.avatar,
                created_at: new Date().toISOString() // 💡 手动补一个发送时间，防止发送瞬间没时间
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
    avatar: myInfo.value.avatar,
    created_at: new Date().toISOString() // 💡 手动补时间
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
    url: `${API_BASE}/api/chat/upload`,
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

const parseEmoji = (content, msg) => {
  if (!content) return '';
  
  // 1. 强制转为字符串，并先将所有 HTML 敏感字符转义！(绝对防御)
  let html = String(content)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
    
  // 2. 统一处理所有人的换行符
  html = html.replace(/\n/g, '<br>');
  
  const isBot = msg && (msg.is_bot || msg.user_id === 0 || msg.username === '波比');
  
  if (isBot) {
    // 恢复 DeepSeek 的 <think> 标签为一个可视化浅色框框
    html = html.replace(/&lt;think&gt;/g, '<div style="color:#95A5A6; font-size:22rpx; background:rgba(0,0,0,0.04); padding:16rpx; border-radius:12rpx; margin-bottom:12rpx; border-left: 6rpx solid #4A6FA5;">💡 思考过程：<br>')
               .replace(/&lt;\/think&gt;/g, '</div>');
    
    // 处理加粗 **文字** -> 用 span 包裹
    html = html.replace(/\*\*(.+?)\*\*/g, '<span class="bot-bold">$1</span>');
    
    // ✅ 【关键修复】：处理斜杠命令 /xxx 
    // 增加 (^|\\s) 边界限制，确保 / 前面是空格或行首，绝对不会误伤 </span> 等 HTML 标签！
    html = html.replace(/(^|\s)(\/[a-zA-Z][a-zA-Z0-9]*)/g, '$1<span class="bot-cmd">$2</span>');
    
    // 处理代码 `code`
    html = html.replace(/`([^`]+)`/g, '<span class="bot-code">$1</span>');
  }
  
  // 3. 处理 emoji 表情 [face:00] -> <img>
  html = html.replace(/\[face:(\d+)\]/g, (m, id) => {
    const f = id.toString().padStart(2, '0');
    return `<img style="width:24px; height:24px; vertical-align:middle; display:inline-block;" src="${API_BASE}/static/emoji/${f}.gif" />`;
  });
  
  return html;
};

const formatAvatar = (path, msg) => {
  // 机器人头像使用本地静态资源
  if (msg && (msg.is_bot || msg.user_id === 0 || msg.username === '波比')) {
    return '/static/bot.jpg';
  }
  if (!path) return '/static/logo.png';
  return path.startsWith('http') ? path : `${API_BASE}${path}`;
};

const fetchHistory = async (isLoadMore = false) => {
    const offset = isLoadMore ? historyOffset.value : 0;
    const limit = 50;  // 一次加载50条，减少请求次数
    
    try {
        // 使用封装好的 get 请求
        const newMessages = await get('/api/square/history', { 
            user_id: myInfo.value.id,
            offset: offset,
            limit: limit
        });
        
        // 清理损坏的 HTML 格式（修复双重标签问题）
        const cleanMessages = newMessages.map(msg => {
            if (msg.content) {
                // 检查是否有 << 开头的问题（损坏的 HTML）
                if (msg.content.includes('<<span') || msg.content.includes('<<strong') || msg.content.includes('<<code')) {
                    // 直接把所有 << 开头的标签问题修复
                    // 模式1: <<span class="xxx">yyy</span>> -> 移除外部 <>
                    msg.content = msg.content.replace(/<</g, '');
                }
            }
            return msg;
        });
        
        // 过滤掉已删除的消息
        const key = `deleted_msgs_${myInfo.value.id}`;
        const deletedIds = uni.getStorageSync(key) || [];
        const filteredMessages = cleanMessages.filter(m => !deletedIds.includes(m.id));
        
        if (isLoadMore) {
            // 加载更多：追加到数组开头
            messages.value = [...filteredMessages, ...messages.value];
            // 更新偏移量
            historyOffset.value += filteredMessages.length;
            // 如果返回数据少于 limit，说明没有更多了
            if (filteredMessages.length < limit) {
                hasMoreHistory.value = false;
            }
            // 加载更多时不自动滚动，保持当前位置
        } else {
            // 首次加载：替换数组
            messages.value = filteredMessages;
            historyOffset.value = filteredMessages.length;
            // 如果返回数据少于 limit，说明没有更多了
            if (filteredMessages.length < limit) {
                hasMoreHistory.value = false;
            }
            // 首次加载时滚动到底部
            scrollToBottom();
        }
    } catch (err) {
        console.error('History fetch failed', err);
        // 错误已经在 request.js 中处理了，这里不用再弹toast
    }
};

// 加载更多历史消息
const loadMoreHistory = () => {
    // 防止重复触发
    if (isLoadingMore.value || !hasMoreHistory.value) return;
    
    isLoadingMore.value = true;
    
    fetchHistory(true).finally(() => {
        isLoadingMore.value = false;
    });
};

// 滚动到底部
const scrollToBottom = () => {
  if (!isPageActive.value) return;
  // 使用 scroll-top 设置为很大的值来滚动到底部
  const temp = scrollTop.value;
  scrollTop.value = 0;
  nextTick(() => {
    if (isPageActive.value) {
      scrollTop.value = 999999;
    }
  });
};

// 滚动到顶部（加载更多后使用）
const scrollToTop = () => {
  if (!isPageActive.value) return;
  const temp = scrollTop.value;
  scrollTop.value = 999999;
  nextTick(() => {
    if (isPageActive.value) {
      scrollTop.value = 0;
    }
  });
};

// 监听滚动到底部（用于判断是否需要自动滚动）
const onScrollToLower = () => {
  // 用户滚动到底部时，可以做一些处理
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

/* 深色模式变量 */
$dark-bg: #121212;
$dark-card: #1E1E1E;
$dark-text-main: #E0E0E0;
$dark-text-sub: #A0A0A0;
$dark-bubble-other: #2C2C2C;
$dark-input-bg: #2C2C2C;

page { 
  background-color: $color-bg; 
  height: 100vh; 
  overflow: hidden; 
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
  transition: background-color 0.3s;
}

.container { 
  display: flex; 
  flex-direction: column; 
  height: 100vh; 
  background-color: $color-bg; 
  transition: background-color 0.3s; 
}
.container.dark { 
  background-color: $dark-bg !important; 
}

/* 2. 顶部导航 */
.nav-header { 
  height: 88rpx; 
  padding: 0 30rpx; 
  display: flex; 
  align-items: center; 
  background: rgba(245, 245, 240, 0.95); 
  backdrop-filter: blur(10px); 
  position: fixed; 
  top: 0; 
  left: 0; 
  width: 100%; 
  z-index: 100;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  transition: background-color 0.3s, border-color 0.3s;
  /* 适配不同端的顶部安全区 */
  padding-top: var(--status-bar-height);
  box-sizing: content-box; 
}
.container.dark .nav-header { 
  background: rgba(18, 18, 18, 0.95) !important; 
  border-bottom: 1px solid rgba(255,255,255,0.05); 
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
  transition: color 0.3s;
}
.container.dark .page-title { color: $dark-text-main; }

.online-badge {
  display: flex;
  align-items: center;
  background: rgba(74, 111, 165, 0.1);
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  margin-left: 16rpx;
  transition: background-color 0.3s;
}
.container.dark .online-badge { background: rgba(74, 111, 165, 0.2); }

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
  
  /* 🔥 核心修改：将上下内边距分开写 */
  /* 顶部 padding = 原本的 30rpx + 导航栏高度(88rpx) + 状态栏高度 */
  padding-top: calc(118rpx + var(--status-bar-height)); 
  padding-bottom: 30rpx;
  padding-left: 30rpx;
  padding-right: 30rpx;
  
  box-sizing: border-box; 
  transition: background-color 0.3s;
}
.container.dark .chat-area {
  background: $dark-bg;
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
  transition: color 0.3s, background-color 0.3s;
}
.container.dark .system-text { color: $dark-text-sub; background: rgba(255,255,255,0.05); }

.loading-more {
  text-align: center;
  padding: 20rpx;
}
.loading-text {
  font-size: 22rpx;
  color: $color-text-sub;
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
  /* 关键修改：去掉 70% 限制，改成更宽松的最大宽度，并让子元素不拉伸 */
  max-width: 80%; 
  margin: 0 20rpx; 
  display: flex; 
  flex-direction: column; 
  /* 关键：让气泡列不从父容器拉伸，默认 flex-start 即可 */
  align-items: flex-start; 
}

.self .content-box { 
  align-items: flex-end; 
}

/* 💡 新增：名字与时间栏 */
.name-time-bar {
  display: flex;
  align-items: baseline;
  margin-bottom: 8rpx;
  margin-left: 4rpx;
}

.self .name-time-bar {
  justify-content: flex-end;
  margin-right: 4rpx;
  margin-left: 0;
}

.sender-name { 
  font-size: 18rpx;  /* QQ风格：小一点 */
  color: $color-text-sub; 
  margin-right: 10rpx; /* 名字和时间隔开一点 */
  transition: color 0.3s; 
}
.container.dark .sender-name { color: $dark-text-sub; }

.msg-time {
  font-size: 18rpx;
  color: #B0BEC5; /* 淡淡的灰色，不抢视觉焦点 */
  font-family: monospace;
}
.container.dark .msg-time { color: #555; }

/* --- 核心修改：气泡样式修正 --- */
.bubble { 
  padding: 10rpx 16rpx; 
  border-radius: 12rpx; /* 统一圆角，不再有奇怪的尖角 */
  position: relative; 
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04); /* 阴影更淡更自然 */
  background: $color-bubble-other;
  /* min-height 移除，让气泡根据内容自动调整高度 */
  display: flex;
  align-items: center;
  /* 关键：允许气泡收缩到内容实际高度 */
  min-height: auto; 
  /* 单行文本时限制最大宽度，防止气泡过宽 */
  max-width: 480rpx;
  transition: background-color 0.3s, box-shadow 0.3s;
}
.container.dark .bubble { background: $dark-bubble-other; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.2); }

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
  /* 关键：防止单行 emoji/文本时 line-height 撑开气泡 */
  display: inline-block;
  vertical-align: middle;
  transition: color 0.3s;
}
.container.dark .msg-text { color: $dark-text-main; }

.self .msg-text {
  color: $color-white;
}

/* 波比机器人消息样式 */
.msg-text :global(br) {
  display: block;
  content: "";
  margin: 4rpx 0;
}

.msg-text :global(.bot-bold) {
  font-weight: 600;
  color: #4A6FA5;
  background: rgba(74, 111, 165, 0.1);
  padding: 0 4rpx;
  border-radius: 4rpx;
}

.msg-text :global(.bot-cmd) {
  background: rgba(74, 111, 165, 0.15);
  color: #4A6FA5;
  padding: 2rpx 8rpx;
  border-radius: 6rpx;
  font-family: monospace;
  font-size: 26rpx;
}

.msg-text :global(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2rpx 6rpx;
  border-radius: 4rpx;
  font-family: monospace;
  font-size: 26rpx;
  color: #E91E63;
}

/* 4. 底部输入区 */
.input-area-wrapper { 
  flex-shrink: 0; 
  background: $color-white;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.02);
  padding-bottom: calc(constant(safe-area-inset-bottom)); 
  padding-bottom: calc(env(safe-area-inset-bottom)); 
  z-index: 100;
  transition: background-color 0.3s, border-color 0.3s;
}
.container.dark .input-area-wrapper { 
  background: $dark-card; 
  border-top: 1px solid rgba(255,255,255,0.05); 
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

.iconfont { font-size: 40rpx; color: #78909C; transition: color 0.3s; }
.container.dark .iconfont { color: $dark-text-sub; }

.minimal-input { 
  flex: 1; 
  background: #F0F2F5; 
  height: 72rpx; 
  padding: 0 24rpx; 
  border-radius: 12rpx; /* 输入框也方一点 */
  font-size: 28rpx; 
  color: $color-text-main; 
  margin-right: 20rpx;
  transition: background-color 0.3s, color 0.3s;
}
.container.dark .minimal-input { background: $dark-input-bg; color: $dark-text-main; }

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
  transition: background-color 0.3s, border-color 0.3s;
}
.container.dark .emoji-panel { 
  background: #1A1A1A; 
  border-top: 1px solid rgba(255,255,255,0.05); 
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
  transition: background-color 0.3s;
}
.container.dark .delete-bar { background: $dark-card; }

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