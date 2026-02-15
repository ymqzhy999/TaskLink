<template>
  <view class="container">
    <view class="nav-header">
      <view class="back-btn" @click="goBack">←</view>
      <text class="nav-title">学习分析报告</text>
      <view style="width: 40rpx;"></view>
    </view>

    <scroll-view scroll-y class="content-scroll">
      <view class="user-summary-card fade-in">
        <view class="user-row">
          <image class="u-avatar" :src="formatAvatar(currentStats.avatar)" mode="aspectFill"></image>
          <view class="u-info">
            <text class="u-name">{{ currentStats.username || '加载中...' }}</text>
            <view class="u-tags">
              <text class="u-badge" :class="isMe ? 'bg-blue' : 'bg-gray'">{{ isMe ? '我' : '查看中' }}</text>
              <text class="u-level">Lv.{{ calculateLevel(currentStats.total_learned) }}</text>
            </view>
          </view>
          <view class="u-total">
            <text class="t-num">{{ currentStats.total_learned || 0 }}</text>
            <text class="t-label">Words Learned</text>
          </view>
        </view>
      </view>

      <view class="charts-container slide-up">
        <view class="chart-box">
          <view class="chart-header">
            <text class="c-title">记忆质量分布</text>
          </view>
          <view class="canvas-wrap">
            <canvas 
              canvas-id="roseCanvas" 
              id="roseCanvas" 
              class="charts"
              :style="{ width: cWidth + 'px', height: cHeight + 'px' }"
              @touchstart="touchRose"
            ></canvas>
          </view>
        </view>

        <view class="chart-box">
          <view class="chart-header">
            <text class="c-title">近七日学习趋势</text>
          </view>
          <view class="canvas-wrap">
            <canvas 
              canvas-id="trendCanvas" 
              id="trendCanvas" 
              class="charts"
              :style="{ width: cWidth + 'px', height: cHeight + 'px' }"
              @touchstart="touchTrend"
            ></canvas>
          </view>
        </view>
      </view>

      <view class="rank-section slide-up">
        <view class="rank-header">
          <text class="rh-title">学习排行榜</text>
          <text class="rh-sub">点击用户切换视图</text>
        </view>
        
        <view class="rank-list">
          <view 
            class="rank-item" 
            v-for="(item, index) in leaderboard" 
            :key="index"
            :class="{ 'active': item.user_id === selectedUserId }"
            @click="selectUser(item)"
          >
            <view class="r-left">
              <view class="r-idx-box">
                <view v-if="index === 0" class="medal-badge gold">1</view>
                <view v-else-if="index === 1" class="medal-badge silver">2</view>
                <view v-else-if="index === 2" class="medal-badge bronze">3</view>
                <text v-else class="r-idx">{{ index + 1 }}</text>
              </view>
              <image class="r-avatar" :src="formatAvatar(item.avatar)" mode="aspectFill"></image>
              <text class="r-name text-truncate">{{ item.username }}</text>
            </view>
            <text class="r-val">{{ item.total_learned }}</text>
          </view>
          
          <view class="load-more-box" v-if="hasMore" @click="loadMoreRank">
             <text class="load-text">点击加载更多排名 ↓</text>
          </view>
          <view class="loading-text" v-else>
             --- 仅展示前 {{ leaderboard.length }} 名 ---
          </view>
        </view>
      </view>
      
      <view style="height: 60rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted, computed, getCurrentInstance } from 'vue';
import uCharts from '@qiun/ucharts';

const API_BASE = `http://101.35.132.175:5000`;
const myId = ref(uni.getStorageSync('userInfo')?.id);
const selectedUserId = ref(myId.value); 
const { proxy } = getCurrentInstance();

const currentStats = ref({});
const leaderboard = ref([]);
const page = ref(1);
const hasMore = ref(true);
const loading = ref(false);

let canvaRose = null;
let canvaTrend = null;

// 像素比配置
const pixelRatio = 1; 
const cWidth = uni.upx2px(610);
const cHeight = uni.upx2px(400);

const goBack = () => uni.navigateBack();
const formatAvatar = (path) => path ? (path.startsWith('http') ? path : `${API_BASE}${path}`) : '/static/logo.png';
const isMe = computed(() => selectedUserId.value === myId.value);

const calculateLevel = (count) => {
  if (!count) return 1;
  return Math.floor(Math.sqrt(count) / 2) + 1;
};

// --- 绘图逻辑 (保持不变) ---
const drawRose = (data) => {
  const chartData = {
    series: [{
      data: [
        { name: "精通", value: data.count_5 || 0 },
        { name: "认识", value: data.count_4 || 0 },
        { name: "模糊", value: data.count_3 || 0 },
        { name: "忘记", value: data.count_0 || 0 }
      ]
    }]
  };
  const ctx = uni.createCanvasContext('roseCanvas', proxy);
  canvaRose = new uCharts({
    type: "rose",
    context: ctx,
    width: cWidth, height: cHeight, categories: [], series: chartData.series, animation: true, pixelRatio: pixelRatio,
    background: "#FFFFFF", color: ["#4A6FA5","#8DA399","#F9E79F","#EF9A9A"], padding: [5,5,5,5], fontSize: 11,
    legend: { show: true, position: "bottom", lineHeight: 16, fontSize: 11 },
    extra: { rose: { type: "area", minRadius: 40, activeOpacity: 0.5, offsetAngle: 0, labelWidth: 15, border: true, borderWidth: 2, borderColor: "#FFFFFF" } }
  });
};

const drawTrend = (data) => {
  const chartData = { categories: data.dates, series: [{ name: "学习量", data: data.values }] };
  const ctx = uni.createCanvasContext('trendCanvas', proxy);
  canvaTrend = new uCharts({
    type: "area", context: ctx, width: cWidth, height: cHeight, categories: chartData.categories, series: chartData.series, animation: true, pixelRatio: pixelRatio,
    background: "#FFFFFF", color: ["#4A6FA5"], padding: [15,10,0,5], fontSize: 11, enableScroll: false,
    xAxis: { disableGrid: true, fontSize: 10, axisLineColor: "#E0E0E0" },
    yAxis: { gridType: "dash", dashLength: 2, data: [{ min: 0, fontSize: 10, axisLineColor: "#E0E0E0" }] },
    extra: { area: { type: "curve", opacity: 0.2, addLine: true, width: 2, gradient: true } }
  });
};

const touchRose = (e) => canvaRose.showToolTip(e, { format: (item) => `${item.name}: ${item.value}` });
const touchTrend = (e) => canvaTrend.showToolTip(e, { format: (item) => `${item.name}: ${item.data}` });

// --- 数据逻辑 ---

const fetchUserDetail = (userId) => {
  uni.showLoading({ title: '加载中...' });
  Promise.all([
    new Promise(resolve => uni.request({ url: `${API_BASE}/api/stats/user?user_id=${userId}`, success: res => resolve(res.data.code === 200 ? res.data.data : {}) })),
    new Promise(resolve => uni.request({ url: `${API_BASE}/api/stats/trend?user_id=${userId}`, success: res => resolve(res.data.code === 200 ? res.data.data : { dates: [], values: [] }) }))
  ]).then(([stats, trend]) => {
      currentStats.value = stats;
      setTimeout(() => { drawRose(stats); drawTrend(trend); }, 300);
      uni.hideLoading();
  }).catch(() => uni.hideLoading());
};

const fetchLeaderboard = (isLoadMore = false) => {
  if (loading.value || (!isLoadMore && !hasMore.value)) return;
  loading.value = true;
  

  uni.request({
    url: `${API_BASE}/api/stats/leaderboard`,
    data: { page: page.value, per_page: 5 },
    success: (res) => {
      if (res.data.code === 200) {
        if (page.value === 1) leaderboard.value = [];
        leaderboard.value = [...leaderboard.value, ...res.data.data];
        hasMore.value = res.data.has_more;   
        if (page.value === 1 && leaderboard.value.length > 0) {

           if (!currentStats.value.username && myId.value) {
               fetchUserDetail(myId.value);
           }
        }
      }
    },
    complete: () => loading.value = false
  });
};

const selectUser = (user) => {
  if (selectedUserId.value === user.user_id) return;
  selectedUserId.value = user.user_id;
  uni.pageScrollTo({ scrollTop: 0, duration: 300 });
  fetchUserDetail(user.user_id);
};

// 点击按钮加载更多
const loadMoreRank = () => {
  if (hasMore.value) {
      page.value++;
      fetchLeaderboard(true);
  }
};

onMounted(() => {
  // 初始只加载第一页（前5名）
  page.value = 1;
  fetchLeaderboard();
  
  // 默认加载自己的数据
  if (myId.value) fetchUserDetail(myId.value);
});
</script>

<style lang="scss" scoped>
/* 样式保持不变 */
$color-bg: #F5F5F0;
$color-card: #FFFFFF;
$color-primary: #4A6FA5;
$color-text-main: #2C3E50;
$color-text-sub: #95A5A6;

page { background-color: $color-bg; font-family: 'Inter', sans-serif; }
.container { min-height: 100vh; display: flex; flex-direction: column; }
.nav-header { padding: 100rpx 40rpx 20rpx; display: flex; justify-content: space-between; align-items: center; }
.back-btn { font-size: 40rpx; color: $color-primary; padding: 10rpx; }
.nav-title { font-size: 32rpx; font-weight: 700; color: $color-text-main; }
.content-scroll { flex: 1; padding: 0 40rpx; box-sizing: border-box; }

.user-summary-card { margin: 20rpx 0 40rpx; background: $color-card; border-radius: 24rpx; padding: 30rpx; box-shadow: 0 4rpx 16rpx rgba(74, 111, 165, 0.08); }
.user-row { display: flex; align-items: center; }
.u-avatar { width: 90rpx; height: 90rpx; border-radius: 50%; margin-right: 24rpx; background: #eee; border: 2rpx solid #F0F0F0; }
.u-info { flex: 1; display: flex; flex-direction: column; }
.u-name { font-size: 32rpx; font-weight: 700; color: $color-text-main; margin-bottom: 8rpx; }
.u-tags { display: flex; gap: 10rpx; }
.u-badge, .u-level { font-size: 18rpx; padding: 4rpx 12rpx; border-radius: 8rpx; font-weight: 600; }
.bg-blue { background: rgba(74, 111, 165, 0.1); color: $color-primary; }
.bg-gray { background: #F5F5F5; color: $color-text-sub; }
.u-level { background: #FFF3E0; color: #FF9800; }
.u-total { text-align: right; }
.t-num { font-size: 44rpx; font-weight: 800; color: $color-primary; display: block; line-height: 1; margin-bottom: 6rpx; }
.t-label { font-size: 18rpx; color: $color-text-sub; letter-spacing: 1px; text-transform: uppercase; }

.charts-container { display: flex; flex-direction: column; gap: 30rpx; margin-bottom: 40rpx; }
.chart-box { background: $color-card; border-radius: 24rpx; padding: 30rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.03); }
.chart-header { margin-bottom: 20rpx; display: flex; align-items: center; }
.c-title { font-size: 26rpx; font-weight: 700; color: $color-text-main; padding-left: 16rpx; border-left: 6rpx solid $color-primary; }
.canvas-wrap { width: 100%; display: flex; justify-content: center; align-items: center; } 
.charts { background-color: #FFFFFF; }

.rank-section { background: $color-card; border-radius: 24rpx; padding: 30rpx 0; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.03); margin-bottom: 40rpx; }
.rank-header { padding: 0 30rpx 20rpx; display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #F5F5F5; }
.rh-title { font-size: 28rpx; font-weight: 700; color: $color-text-main; }
.rh-sub { font-size: 20rpx; color: $color-text-sub; }
.rank-item { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 30rpx; border-bottom: 1px solid #F9F9F9; transition: all 0.2s; }
.rank-item:active { background-color: #F8F9FA; }
.rank-item.active { background: rgba(74, 111, 165, 0.08); border-left: 6rpx solid $color-primary; }
.r-left { display: flex; align-items: center; flex: 1; overflow: hidden; }
.r-idx-box { width: 60rpx; display: flex; justify-content: center; margin-right: 10rpx; }
.r-idx { font-size: 24rpx; font-weight: 700; color: #CCC; }
.medal-badge { width: 36rpx; height: 36rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20rpx; font-weight: 800; color: #FFF; box-shadow: 0 4rpx 8rpx rgba(0,0,0,0.15); text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.gold { background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); border: 2rpx solid #FFF; }
.silver { background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%); border: 2rpx solid #FFF; }
.bronze { background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%); border: 2rpx solid #FFF; }
.r-avatar { width: 70rpx; height: 70rpx; border-radius: 50%; background: #eee; margin-right: 20rpx; }
.r-name { font-size: 26rpx; color: $color-text-main; font-weight: 600; }
.text-truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240rpx; }
.r-val { font-size: 30rpx; font-weight: 700; color: $color-primary; font-family: monospace; }

/* 🔥 加载更多按钮样式 */
.load-more-box {
  padding: 30rpx 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
.load-text {
  font-size: 24rpx;
  color: $color-primary;
  background: rgba(74, 111, 165, 0.1);
  padding: 12rpx 30rpx;
  border-radius: 30rpx;
}
.loading-text { text-align: center; padding: 30rpx; font-size: 22rpx; color: #CCC; }

.fade-in { animation: fadeIn 0.6s ease; }
.slide-up { animation: slideUp 0.6s ease-out backwards; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20rpx); } to { opacity: 1; transform: translateY(0); } }
</style>