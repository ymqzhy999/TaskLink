<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="header-section">
      <text class="page-title">{{ isEdit ? t.title_edit : t.title_new }}</text>
      <text class="page-desc">{{ t.subtitle }}</text>
    </view>

    <view class="form-container">
      
      <view class="cyber-card">
        <view class="card-header">
          <view class="decor-line"></view>
          <text class="section-label">{{ t.sec_basic }}</text>
        </view>
        <view class="form-row">
          <text class="label">{{ t.label_name }}</text>
          <input class="cyber-input" v-model="form.title" :placeholder="t.ph_name" placeholder-class="cyber-placeholder" />
        </view>
        <view class="form-row no-border">
          <text class="label">{{ t.label_desc }}</text>
          <input class="cyber-input" v-model="form.desc" :placeholder="t.ph_desc" placeholder-class="cyber-placeholder" :maxlength="100" />
        </view>
      </view>

      <view class="cyber-card">
        <view class="card-header">
          <view class="decor-line bg-purple"></view>
          <text class="section-label">{{ t.sec_trigger }}</text>
        </view>
        <view class="form-row">
          <text class="label">{{ t.label_time }}</text>
          <picker mode="time" :value="form.time" @change="onTimeChange">
            <view class="picker-value neon-text">{{ form.time || '--:--' }}</view>
          </picker>
        </view>
        <view class="form-row no-border">
          <text class="label">{{ t.label_loop }}</text>
          <switch color="#00f3ff" style="transform:scale(0.8)" :checked="form.is_loop" @change="onLoopChange"/>
        </view>
      </view>

      <view class="cyber-card action-card">
        <view class="card-header">
          <view class="decor-line bg-green"></view>
          <text class="section-label">{{ t.sec_action }}</text>
        </view>
        
        <view class="type-grid">
          <view class="cyber-btn" :class="{ active: form.type === 'APP' }" @click="form.type = 'APP'">📱 APP</view>
          <view class="cyber-btn" :class="{ active: form.type === 'LINK' }" @click="form.type = 'LINK'">🔗 LINK</view>
          <view class="cyber-btn" :class="{ active: form.type === 'SCRIPT' }" @click="form.type = 'SCRIPT'">💻 CODE</view>
        </view>

        <view class="dynamic-input">
          <text class="input-helper">{{ getInputHelper() }}</text>
          
          <view class="input-wrapper">
            <input 
              class="big-input cyber-input-box" 
              v-model="form.target" 
              :placeholder="getPlaceholder()" 
              placeholder-class="cyber-placeholder"
            />
            
            <view 
              v-if="form.type === 'APP'" 
              class="match-btn" 
              @click="autoMatchPackage"
            >
              🔍 匹配
            </view>
          </view>
          
          <text v-if="matchResult" class="match-tip">Found: {{ matchResult }}</text>
        </view>
      </view>

    </view>

    <view class="footer-normal">
      <button class="submit-btn cyber-glitch" @click="submitTask">
        {{ isEdit ? t.btn_save : t.btn_create }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import messages from '@/utils/language.js';

const API_BASE = 'http://192.168.10.26:5000';
const isEdit = ref(false);
const form = ref({ id: null, title: '', desc: '', time: '', is_loop: false, type: 'APP', target: '' });
const t = ref(messages.zh.add);
const matchResult = ref(''); // 存储匹配到的应用名

onShow(() => {
  const lang = uni.getStorageSync('lang') || 'zh';
  t.value = messages[lang].add;

  const editTask = uni.getStorageSync('edit_task_data');
  if (editTask) {
    isEdit.value = true;
    form.value = { 
      id: editTask.id, 
      title: editTask.title, 
      desc: editTask.description || '', 
      time: editTask.time || editTask.trigger_time, 
      is_loop: editTask.is_loop || false, 
      type: editTask.type || editTask.action_type, 
      target: editTask.target || editTask.target_value 
    };
    uni.removeStorageSync('edit_task_data');
    uni.setNavigationBarTitle({ title: t.value.title_edit });
  } else {
    resetForm();
    uni.setNavigationBarTitle({ title: t.value.title_new });
  }
});
// --- 🔥 核心功能：自动匹配包名 (修复版) ---
const autoMatchPackage = () => {
  // 1. 检查输入
  const keyword = form.value.target.trim();
  if (!keyword) {
    uni.showToast({ title: '请输入应用名称(如:微信)', icon: 'none' });
    return;
  }

  // 2. 检查环境
  // #ifdef H5
  uni.showToast({ title: '网页端不支持扫描本地应用', icon: 'none' });
  return;
  // #endif

  // #ifdef APP-PLUS
  if (uni.getSystemInfoSync().platform !== 'android') {
    uni.showToast({ title: '仅支持 Android 自动匹配', icon: 'none' });
    return;
  }

  uni.showLoading({ title: 'SCANNING...' });

  // 3. 使用 Native.js 调用 Android API (使用 invoke 避免报错)
  try {
    const main = plus.android.runtimeMainActivity();
    const pManager = plus.android.invoke(main, 'getPackageManager'); // 稳妥获取 pManager
    
    // 🔥 修复点：使用 invoke 调用 getInstalledPackages
    // 参数 0 代表 GET_ACTIVITIES 等默认标志
    const pInfo = plus.android.invoke(pManager, 'getInstalledPackages', 0);
    
    // 获取 List 大小
    const total = plus.android.invoke(pInfo, 'size');
    
    let found = false;
    let matchedPkg = '';
    let matchedLabel = '';

    // 遍历所有应用
    for (let i = 0; i < total; i++) {
      // 获取第 i 个 PackageInfo
      const p = plus.android.invoke(pInfo, 'get', i);
      
      // 获取 ApplicationInfo
      const appInfo = plus.android.getAttribute(p, 'applicationInfo');
      
      // 获取应用名 (Label) - 同样使用 invoke 调用 loadLabel
      const labelObj = plus.android.invoke(appInfo, 'loadLabel', pManager);
      const label = labelObj ? labelObj.toString() : '';
      
      // 获取包名
      const pname = plus.android.getAttribute(p, 'packageName');
      
      // 模糊匹配：如果应用名包含关键字 (忽略大小写)
      if (label && label.toLowerCase().includes(keyword.toLowerCase())) {
        matchedPkg = pname;
        matchedLabel = label;
        found = true;
        break; 
      }
    }

    uni.hideLoading();

    if (found) {
      // 匹配成功，自动填入
      form.value.target = matchedPkg;
      matchResult.value = `匹配成功: ${matchedLabel}`;
      uni.showToast({ title: 'MATCHED!', icon: 'success' });
    } else {
      uni.showToast({ title: '未找到该应用', icon: 'none' });
      matchResult.value = '';
    }

  } catch (e) {
    uni.hideLoading();
    console.error(e); // 在控制台打印详细错误
    uni.showToast({ title: '扫描失败: 权限或兼容性问题', icon: 'none' });
  }
  // #endif
};
const resetForm = () => { 
  isEdit.value = false; 
  form.value = { id: null, title: '', desc: '', time: '', is_loop: false, type: 'APP', target: '' }; 
  matchResult.value = '';
};
const onTimeChange = (e) => { form.value.time = e.detail.value; };
const onLoopChange = (e) => { form.value.is_loop = e.detail.value; }

// --- 🔥 核心功能：自动匹配包名 (仅限 Android) ---

const getInputHelper = () => {
    if (form.value.type === 'APP') return t.value.helper_app;
    if (form.value.type === 'LINK') return t.value.helper_link;
    return t.value.helper_script;
}

const getPlaceholder = () => {
  if (form.value.type === 'APP') return "输入名称(如:微信) 点击匹配 ->";
  if (form.value.type === 'LINK') return t.value.ph_target_link;
  return t.value.ph_target_script;
};

const submitTask = () => {
  if (!form.value.title || !form.value.time || !form.value.target) { 
    uni.showToast({ title: t.value.toast_err, icon: 'none' }); 
    return; 
  }
  
  const userInfo = uni.getStorageSync('userInfo');
  uni.showLoading({ title: 'PROCESSING...' });

  const method = isEdit.value ? 'PUT' : 'POST';
  const url = isEdit.value ? `${API_BASE}/api/tasks/${form.value.id}` : `${API_BASE}/api/tasks`;

  uni.request({
    url: url, 
    method: method,
    data: { 
      user_id: userInfo.id, 
      title: form.value.title, 
      description: form.value.desc, 
      is_loop: form.value.is_loop, 
      time: form.value.time, 
      type: form.value.type, 
      target: form.value.target 
    },
    success: (res) => {
      uni.hideLoading();
      if (res.data.code === 200) { 
        uni.showToast({ title: t.value.toast_succ }); 
        setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 800); 
      } else { 
        uni.showToast({ title: 'ERROR', icon: 'none' }); 
      }
    },
    fail: () => {
      uni.hideLoading();
      uni.showToast({ title: 'NET_ERR', icon: 'none' });
    }
  });
};
</script>

<style>
/* ... (保留之前的样式) ... */
page { background-color: #050505; color: #e0e0e0; font-family: 'Courier New', monospace; }
.container { padding: 20px; padding-bottom: 40px; min-height: 100vh; }
.cyber-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 50% 30%, #1a1a2e 0%, #000000 70%); z-index: -1; pointer-events: none; }

.header-section { margin-bottom: 30px; border-left: 4px solid #00f3ff; padding-left: 15px; }
.page-title { font-size: 28px; font-weight: 900; color: #fff; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0, 243, 255, 0.5); display: block; }
.page-desc { font-size: 12px; color: #00f3ff; margin-top: 5px; opacity: 0.8; display: block; }

.cyber-card { 
  background: #141419; 
  border: 1px solid rgba(0, 243, 255, 0.2); 
  border-radius: 4px; 
  padding: 20px; 
  margin-bottom: 20px; 
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5); 
}

.card-header { display: flex; align-items: center; margin-bottom: 15px; }
.decor-line { width: 4px; height: 16px; background: #00f3ff; margin-right: 10px; box-shadow: 0 0 8px #00f3ff; }
.decor-line.bg-purple { background: #bc13fe; box-shadow: 0 0 8px #bc13fe; }
.decor-line.bg-green { background: #00ff9d; box-shadow: 0 0 8px #00ff9d; }
.section-label { font-size: 14px; color: #fff; font-weight: bold; letter-spacing: 1px; }

.form-row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 15px 0; }
.form-row.no-border { border-bottom: none; }
.label { color: #888; font-size: 12px; font-weight: bold; }

.cyber-input { flex: 1; text-align: right; color: #00f3ff; font-size: 16px; font-weight: bold; height: 24px; min-height: 24px; }
.cyber-placeholder { color: #444; font-weight: normal; }
.picker-value { font-size: 20px; color: #bc13fe; font-weight: bold; text-shadow: 0 0 5px rgba(188, 19, 254, 0.5); }

.type-grid { display: flex; gap: 10px; margin-bottom: 20px; }
.cyber-btn { flex: 1; text-align: center; padding: 12px 0; background: #0a0a0a; border: 1px solid #333; color: #666; font-size: 12px; clip-path: polygon(10% 0, 100% 0, 100% 90%, 90% 100%, 0 100%, 0 10%); transition: all 0.3s; }
.cyber-btn.active { background: rgba(0, 243, 255, 0.1); border-color: #00f3ff; color: #00f3ff; text-shadow: 0 0 8px #00f3ff; }

.dynamic-input { margin-top: 10px; }
.input-helper { font-size: 10px; color: #555; display: block; margin-bottom: 8px; }

/* 🔥 修改：输入框 + 按钮的容器 */
.input-wrapper { display: flex; align-items: center; position: relative; }

.cyber-input-box { 
  background: #111; 
  border: 1px solid #333; 
  color: #fff; 
  padding: 0 15px; 
  width: 100%; 
  border-radius: 4px; 
  box-sizing: border-box;
  height: 50px;
  caret-color: #00f3ff;
}
.cyber-input-box:focus { border-color: #00ff9d; box-shadow: 0 0 10px rgba(0, 255, 157, 0.2); }

/* 🔥 新增：匹配按钮样式 */
.match-btn {
  position: absolute;
  right: 5px;
  top: 5px;
  bottom: 5px;
  background: #00f3ff;
  color: #000;
  font-weight: bold;
  font-size: 12px;
  padding: 0 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  z-index: 1000; /* 确保在最上层 */
}
.match-btn:active { opacity: 0.8; }

.match-tip { display: block; color: #00ff9d; font-size: 12px; margin-top: 5px; text-align: right; }

.footer-normal { margin-top: 40px; width: 100%; }
.submit-btn { background: #00f3ff; color: #000; font-weight: 900; font-size: 18px; letter-spacing: 2px; border-radius: 2px; height: 50px; line-height: 50px; border: none; box-shadow: 0 0 15px #00f3ff; clip-path: polygon(5% 0, 100% 0, 100% 80%, 95% 100%, 0 100%, 0 20%); }
.submit-btn:active { opacity: 0.8; transform: scale(0.98); }
</style>