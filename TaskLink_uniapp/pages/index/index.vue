<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="welcome-box minimal">
      <view class="header-actions">
        <text class="manage-btn" @click="toggleEditMode">
          {{ isEditMode ? t.btn_done : t.btn_manage }}
        </text>
      </view>
    </view>

    <view class="status-panel" :class="{ active: isScanning }" v-if="!isEditMode">
      <view class="panel-info">
        <text class="panel-title">{{ t.status_title }}</text>
        <text class="panel-desc">{{ isScanning ? t.status_run : t.status_stop }}</text>
      </view>
      <switch color="#00ff9d" :checked="isScanning" @change="toggleScan" style="transform:scale(0.7)"/>
    </view>

    <view class="section-header">
      <text class="section-title">{{ t.list_title }}</text>
      <text class="action-text" @click="manualRefresh" v-if="!isEditMode">{{ t.btn_refresh }}</text>
      <text class="action-text warn" @click="toggleSelectAll" v-if="isEditMode">
        {{ selectedIds.length === tasks.length && tasks.length > 0 ? t.btn_deselect : t.btn_select }}
      </text>
    </view>

    <scroll-view 
      scroll-y 
      class="task-list hide-scrollbar"
      :show-scrollbar="false"
    >
      <view v-if="tasks.length === 0" class="empty-state">
        <text class="glitch-text">{{ t.empty }}</text>
      </view>

      <block v-for="(task, index) in tasks" :key="task.id">
        <view 
          class="cyber-task-item" 
          :class="{ selected: selectedIds.includes(task.id) }"
          @click="onItemClick(task)" 
          @longpress="onLongPress(task)"
        >
          <view class="corner tl"></view><view class="corner br"></view>
          <view class="checkbox-area" v-if="isEditMode">
            <view class="cyber-checkbox" :class="{ checked: selectedIds.includes(task.id) }"></view>
          </view>
          <view class="time-col">
            <text class="cyber-time">{{ task.time }}</text>
          </view>
          <view class="info-col">
            <text class="cyber-title">{{ task.title }}</text>
            <view class="tag-box">
              <text class="cyber-tag">{{ task.type }}</text>
              <text class="cyber-tag desc" v-if="task.is_loop">LOOP</text>
            </view>
          </view>
          <view class="action-col" v-if="!isEditMode">
             <view class="play-btn" @click.stop="executeTask(task)">▶</view>
          </view>
        </view>
      </block>
    </scroll-view>

    <view class="bottom-bar-cyber" v-if="isEditMode">
      <view class="delete-btn-cyber" @click="batchDelete">
        {{ t.btn_delete }} ({{ selectedIds.length }})
      </view>
    </view>

    <view class="ai-fab" @click="openChat" v-if="!isEditMode && !showChat">
      <text class="ai-icon">🤖</text>
    </view>

    <view class="chat-overlay" v-if="showChat">
      <view class="chat-window">
        <view class="chat-header">
          <text class="chat-title">{{ t.ai_title }}</text>
          <text class="close-btn" @click="showChat = false">✕</text>
        </view>
        
        <scroll-view 
          scroll-y 
          class="chat-body hide-scrollbar" 
          :scroll-into-view="scrollTarget"
          scroll-with-animation
          :show-scrollbar="false"
        >
          <view v-for="(msg, idx) in chatHistory" :key="idx" class="msg-row" :class="msg.role">
            <view class="msg-bubble">
              <text class="msg-text">{{ msg.content }}</text>
              <text v-if="msg.role === 'ai' && idx === chatHistory.length - 1 && isTyping" class="cursor">_</text>
            </view>
          </view>
          
          <view v-if="isThinking && !isTyping" class="msg-row ai">
            <view class="msg-bubble thinking">
              <text class="dot">.</text><text class="dot">.</text><text class="dot">.</text>
            </view>
          </view>

          <view id="chat-bottom" style="height: 10px;"></view>
        </scroll-view>

        <view class="chat-footer">
          <input 
            class="chat-input" 
            v-model="inputMsg" 
            :placeholder="t.ai_input" 
            confirm-type="send"
            @confirm="sendMessage" 
          />
          <view class="send-btn" @click="sendMessage">
             {{ (isThinking || isTyping) ? 'STOP' : t.ai_send }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app';
import messages from '@/utils/language.js';

const API_BASE = 'http://192.168.10.26:5000';
const userInfo = ref({});
const tasks = ref([]);
const t = ref(messages.zh.index);

const isScanning = ref(true);
const timer = ref(null);
const lastExecutedTime = ref('');
const isEditMode = ref(false);
const selectedIds = ref([]);
const showChat = ref(false);
const inputMsg = ref('');
const chatHistory = ref([{ role: 'ai', content: 'Greeting. Systems operational.' }]);
const scrollTarget = ref('');

// AI 状态控制
const isThinking = ref(false);
const isTyping = ref(false);
const currentRequestId = ref(0); // 🔥 新增：用于版本控制，防止旧请求打断新对话
const typewriterTimer = ref(null); // 🔥 新增：用于存储打字机定时器，方便随时掐断

onShow(() => {
  const lang = uni.getStorageSync('lang') || 'zh';
  t.value = messages[lang].index;
  const user = uni.getStorageSync('userInfo');
  if (user) { userInfo.value = user; fetchTasks(); }
  else { uni.reLaunch({ url: '/pages/login/login' }); }
});

onPullDownRefresh(() => {
  fetchTasks();
  setTimeout(() => {
    uni.stopPullDownRefresh();
    uni.showToast({ title: 'REFRESHED', icon: 'none' });
  }, 1000);
});

const manualRefresh = () => { uni.startPullDownRefresh(); }

const fetchTasks = () => {
  uni.request({
    url: `${API_BASE}/api/tasks?user_id=${userInfo.value.id}`,
    success: (res) => { if (res.data.code === 200) { tasks.value = res.data.data; selectedIds.value = []; }}
  });
};

const onItemClick = (task) => {
  if (isEditMode.value) {
    const index = selectedIds.value.indexOf(task.id);
    index > -1 ? selectedIds.value.splice(index, 1) : selectedIds.value.push(task.id);
    return;
  }
  uni.setStorageSync('edit_task_data', task);
  uni.switchTab({ url: '/pages/add/add' });
};

const onLongPress = (task) => {
  if (isEditMode.value) return;
  uni.vibrateShort();
  uni.showModal({ title: t.value.del_confirm, content: task.title, confirmColor: '#ff003c', success: (res) => { if (res.confirm) deleteTaskApi(task.id); } });
};

const toggleSelectAll = () => { selectedIds.value = selectedIds.value.length === tasks.value.length ? [] : tasks.value.map(t => t.id); };
const toggleEditMode = () => { isEditMode.value = !isEditMode.value; selectedIds.value = []; };
const executeTask = (task) => { uni.showToast({ title: `EXEC: ${task.title}`, icon: 'none' }); reportLog(task, 'SUCCESS'); };
const reportLog = (task, status) => { uni.request({ url: `${API_BASE}/api/logs`, method: 'POST', data: { user_id: userInfo.value.id, title: task.title, type: task.type, status: status } }); };
const batchDelete = () => {
    if (selectedIds.value.length === 0) return;
    uni.showModal({
        title: 'DELETE',
        content: `Delete ${selectedIds.value.length} items?`,
        confirmColor: '#ff003c',
        success: async (res) => {
            if (res.confirm) {
                for (let id of selectedIds.value) {
                    await new Promise(r => uni.request({ url: `${API_BASE}/api/tasks/${id}`, method: 'DELETE', complete: r }));
                }
                fetchTasks();
                isEditMode.value = false;
            }
        }
    })
};
const deleteTaskApi = (id) => { uni.request({ url: `${API_BASE}/api/tasks/${id}`, method: 'DELETE', success: () => fetchTasks() }); };
const toggleScan = (e) => { isScanning.value = e.detail.value; };
const openChat = () => { showChat.value = true; scrollToBottom(); };

// --- 🔥 核心修复：停止打字机 ---
const stopTypewriter = () => {
  if (typewriterTimer.value) {
    clearInterval(typewriterTimer.value);
    typewriterTimer.value = null;
  }
  isTyping.value = false;
  isThinking.value = false;
};

// --- 🔥 核心修复：支持打断的消息发送 ---
const sendMessage = () => {
  // 1. 如果有文字在输入，这是普通发送
  if (inputMsg.value.trim()) {
    
    // 如果正在打字或思考，先强制停止它（打断）
    if (isTyping.value || isThinking.value) {
        stopTypewriter();
    }

    // 生成新的请求ID
    currentRequestId.value++;
    const thisRequestId = currentRequestId.value;
    
    const userText = inputMsg.value;
    chatHistory.value.push({ role: 'user', content: userText });
    inputMsg.value = '';
    
    isThinking.value = true;
    scrollToBottom();

    uni.request({
      url: `${API_BASE}/api/chat`,
      method: 'POST',
      data: { message: userText },
      success: (res) => {
        // 关键：如果请求回来时，ID已经变了（说明用户又发了新消息），则丢弃这个旧结果
        if (thisRequestId !== currentRequestId.value) return;

        isThinking.value = false;
        if (res.data.code === 200) {
          startTypewriter(res.data.data);
        } else {
          chatHistory.value.push({ role: 'ai', content: 'Error: Connection lost.' });
          scrollToBottom();
        }
      },
      fail: () => {
        if (thisRequestId !== currentRequestId.value) return;
        isThinking.value = false;
        chatHistory.value.push({ role: 'ai', content: 'Network Error.' });
        scrollToBottom();
      }
    });
  } 
  // 2. 如果输入框没字，但正在输出，点击按钮则是“手动停止”
  else if (isTyping.value || isThinking.value) {
      stopTypewriter();
  }
};

const startTypewriter = (fullText) => {
  isTyping.value = true;
  chatHistory.value.push({ role: 'ai', content: '' });
  const targetIndex = chatHistory.value.length - 1;
  let i = 0;
  
  // 保存定时器ID，以便可以被停止
  typewriterTimer.value = setInterval(() => {
    if (i < fullText.length) {
      chatHistory.value[targetIndex].content += fullText.charAt(i);
      i++;
      if (i % 2 === 0) scrollToBottom();
    } else {
      stopTypewriter(); // 打完了自动停止
      scrollToBottom();
    }
  }, 30);
};

const scrollToBottom = () => {
    scrollTarget.value = '';
    nextTick(() => { scrollTarget.value = 'chat-bottom'; });
};

const startScanner = () => {
  timer.value = setInterval(() => {
    if (!isScanning.value) return;
    const now = new Date();
    const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    if (currentTime === lastExecutedTime.value) return;
    tasks.value.forEach(task => { if (task.time === currentTime) { executeTask(task); lastExecutedTime.value = currentTime; }});
  }, 3000);
};
onMounted(() => { startScanner(); });
onUnmounted(() => { if (timer.value) clearInterval(timer.value); });
</script>

<style>
/* 1. 隐藏滚动条 */
::-webkit-scrollbar { display: none; width: 0 !important; height: 0 !important; -webkit-appearance: none; background: transparent; }
.hide-scrollbar { scrollbar-width: none; -ms-overflow-style: none; }

/* 全局样式 */
page { background-color: #050505; color: #ccc; font-family: 'Courier New', monospace; }
.container { padding: 20px; min-height: 100vh; padding-bottom: 100px; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 10%, #111 0%, #000 80%); z-index: -1; }

/* 顶部样式 */
.welcome-box.minimal { display: flex; justify-content: flex-end; margin-bottom: 20px; height: 30px; }
.manage-btn { color: #00f3ff; font-size: 12px; border: 1px solid #00f3ff; padding: 4px 10px; border-radius: 2px; }

/* 状态面板 */
.status-panel { background: #0a0a0a; border: 1px solid #333; padding: 15px; display: flex; align-items: center; margin-bottom: 25px; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
.status-panel.active { border-color: #00ff9d; box-shadow: 0 0 10px rgba(0, 255, 157, 0.2); }
.panel-info { flex: 1; margin-left: 10px; }
.panel-title { color: #fff; font-size: 14px; font-weight: bold; display: block; }
.panel-desc { color: #666; font-size: 10px; }

/* 列表头 */
.section-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
.section-title { color: #888; font-size: 12px; font-weight: bold; letter-spacing: 2px; }
.action-text { color: #00f3ff; font-size: 12px; }
.action-text.warn { color: #ff003c; }

/* 任务列表 */
.cyber-task-item { background: #0e0e0e; margin-bottom: 15px; padding: 15px; display: flex; align-items: center; position: relative; border: 1px solid #222; transition: all 0.2s; }
.cyber-task-item.selected { border-color: #ff003c; background: rgba(255, 0, 60, 0.05); }
.corner { position: absolute; width: 6px; height: 6px; border: 1px solid #444; }
.tl { top: -1px; left: -1px; border-right: none; border-bottom: none; }
.br { bottom: -1px; right: -1px; border-left: none; border-top: none; }
.time-col { margin-right: 15px; }
.cyber-time { font-size: 20px; color: #fff; font-weight: bold; text-shadow: 0 0 5px rgba(255,255,255,0.3); }
.info-col { flex: 1; }
.cyber-title { color: #ddd; font-size: 14px; font-weight: bold; display: block; }
.cyber-tag { font-size: 10px; color: #666; background: #1a1a1a; padding: 2px 4px; border-radius: 2px; margin-right: 5px; }
.cyber-tag.desc { color: #bc13fe; border: 1px solid #bc13fe; background: transparent; }
.play-btn { color: #00ff9d; font-size: 20px; padding: 5px; }
.checkbox-area { margin-right: 12px; }
.cyber-checkbox { width: 16px; height: 16px; border: 1px solid #666; }
.cyber-checkbox.checked { background: #00f3ff; border-color: #00f3ff; box-shadow: 0 0 8px #00f3ff; }

/* 底部栏 */
.bottom-bar-cyber { position: fixed; bottom: 0; left: 0; right: 0; padding: 20px; background: #111; border-top: 1px solid #ff003c; z-index: 100; display: flex; justify-content: center; }
.delete-btn-cyber { background: #ff003c; color: #fff; padding: 10px 30px; font-weight: bold; font-size: 14px; clip-path: polygon(10% 0, 100% 0, 100% 100%, 0% 100%); }

/* AI 样式 */
.ai-fab { position: fixed; right: 20px; bottom: 100px; width: 50px; height: 50px; background: rgba(0, 243, 255, 0.2); border: 1px solid #00f3ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); box-shadow: 0 0 15px rgba(0, 243, 255, 0.4); z-index: 50; animation: float 3s ease-in-out infinite; }
@keyframes float { 0% {transform: translateY(0px);} 50% {transform: translateY(-10px);} 100% {transform: translateY(0px);} }
.ai-icon { font-size: 24px; }

.chat-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
.chat-window { width: 90%; height: 60%; background: #050505; border: 1px solid #00f3ff; box-shadow: 0 0 20px rgba(0, 243, 255, 0.2); display: flex; flex-direction: column; }
.chat-header { height: 40px; background: rgba(0, 243, 255, 0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 10px; border-bottom: 1px solid #00f3ff; }
.chat-title { color: #00f3ff; font-size: 12px; font-weight: bold; letter-spacing: 1px; }
.close-btn { color: #fff; font-size: 18px; padding: 5px; }

/* 聊天内容区 */
.chat-body { 
  flex: 1; 
  padding: 15px; /* 增加内边距 */
  overflow-y: scroll; 
  box-sizing: border-box; 
}
.msg-row { 
  margin-bottom: 15px; 
  display: flex; 
  width: 100%; 
  box-sizing: border-box; 
}
.msg-row.user { justify-content: flex-end; }
.msg-row.ai { justify-content: flex-start; }

/* 气泡样式 */
.msg-bubble { 
  max-width: 70%; 
  padding: 10px 14px; 
  font-size: 13px; 
  line-height: 1.5; 
  border-radius: 4px; 
  position: relative;
  word-break: break-all; /* 强制换行 */
  white-space: pre-wrap; 
}
.user .msg-bubble { background: #00f3ff; color: #000; font-weight: bold; border-bottom-right-radius: 0; }
.ai .msg-bubble { background: #111; color: #00ff9d; border: 1px solid #00ff9d; border-top-left-radius: 0; }

.cursor { animation: blink 1s infinite; font-weight: bold; }
@keyframes blink { 0%, 100% {opacity: 1;} 50% {opacity: 0;} }
.thinking .dot { animation: jump 1.5s infinite ease-in-out; display: inline-block; margin: 0 1px; color: #00ff9d; }
.thinking .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes jump { 0%, 100% {transform: translateY(0);} 50% {transform: translateY(-5px);} }

.chat-footer { height: 50px; border-top: 1px solid #333; display: flex; align-items: center; padding: 0 10px; background: #080808; }
.chat-input { flex: 1; background: #111; border: none; color: #fff; padding: 5px 10px; font-size: 12px; margin-right: 10px; }
.send-btn { color: #00f3ff; font-size: 12px; font-weight: bold; }
.empty-state { text-align: center; margin-top: 50px; }
.glitch-text { color: #333; font-size: 20px; font-weight: bold; letter-spacing: 5px; }
</style>	