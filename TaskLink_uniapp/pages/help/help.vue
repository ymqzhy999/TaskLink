<template>
  <view class="container">
    <view class="header-section">
      <view class="header-content">
        <text class="page-title">User Guide</text>
        <text class="page-subtitle">TaskLink System v1.5 使用手册</text>
      </view>
      <view class="logo-box">
        <text class="logo-text">?</text>
      </view>
    </view>

    <scroll-view scroll-y class="content-scroll">
      
      <view class="section-header">
        <view class="section-dot"></view>
        <text class="section-title">CORE MODULE: TRAINING</text>
      </view>
      
      <view class="faq-list">
        <view class="faq-card" :class="{ 'expanded': openIndex === 0 }" @click="toggle(0)">
          <view class="card-header">
            <view class="q-badge">Q1</view>
            <text class="q-title">如何开始每日单词训练？</text>
            <view class="arrow-icon">▼</view>
          </view>
          <view class="card-body" v-if="openIndex === 0">
            <text class="answer-text">
              点击首页的 <text class="highlight">每日单词</text> 卡片即可进入训练模式。系统会基于 SM-2 记忆算法，自动为您生成 **15个** 待复习或新学习的单词组合。
            </text>
          </view>
        </view>

        <view class="faq-card" :class="{ 'expanded': openIndex === 1 }" @click="toggle(1)">
          <view class="card-header">
            <view class="q-badge">Q2</view>
            <text class="q-title">0/3/4/5 评分标准是什么？</text>
            <view class="arrow-icon">▼</view>
          </view>
          <view class="card-body" v-if="openIndex === 1">
            <view class="rating-guide">
              <view class="rate-row">
                <view class="rate-tag rate-0">0 忘记</view>
                <text class="rate-desc">完全没印象，需要立即重学。</text>
              </view>
              <view class="rate-row">
                <view class="rate-tag rate-3">3 模糊</view>
                <text class="rate-desc">记得一点，但不确定拼写。</text>
              </view>
              <view class="rate-row">
                <view class="rate-tag rate-4">4 认识</view>
                <text class="rate-desc">能认出，但需要思考一下。</text>
              </view>
              <view class="rate-row">
                <view class="rate-tag rate-5">5 精通</view>
                <text class="rate-desc">秒杀，完全掌握。</text>
              </view>
              <text class="tip-text">* 评分将直接影响下次复习时间的算法安排，请诚实选择。</text>
            </view>
          </view>
        </view>

        <view class="faq-card" :class="{ 'expanded': openIndex === 2 }" @click="toggle(2)">
          <view class="card-header">
            <view class="q-badge">Q3</view>
            <text class="q-title">没背完可以中途退出吗？</text>
            <view class="arrow-icon">▼</view>
          </view>
          <view class="card-body" v-if="openIndex === 2">
            <text class="answer-text">
              可以。点击顶部的 <text class="highlight">保存进度</text> 按钮即可。\n\n系统会自动将当前进度存入历史记录。下次进入时，您可以选择继续上次未完成的训练。
            </text>
          </view>
        </view>
      </view>

      <view class="section-header">
        <view class="section-dot purple"></view>
        <text class="section-title">TOOLS & DATA</text>
      </view>

      <view class="faq-list">
        <view class="faq-card" :class="{ 'expanded': openIndex === 3 }" @click="toggle(3)">
          <view class="card-header">
            <view class="q-badge">Q4</view>
            <text class="q-title">如何使用词库 (Vocabulary)？</text>
            <view class="arrow-icon">▼</view>
          </view>
          <view class="card-body" v-if="openIndex === 3">
            <text class="answer-text">
              • **搜索**：支持中英文模糊搜索。\n• **发音**：点击单词即可播放真人发音。\n• **筛选**：支持按等级 (Level) 和首字母筛选。
            </text>
          </view>
        </view>
        
        <view class="faq-card" :class="{ 'expanded': openIndex === 4 }" @click="toggle(4)">
          <view class="card-header">
            <view class="q-badge">Q5</view>
            <text class="q-title">历史记录有什么用？</text>
            <view class="arrow-icon">▼</view>
          </view>
          <view class="card-body" v-if="openIndex === 4">
            <text class="answer-text">
              历史记录是您的学习日志：\n1. **查看**：回顾过去的打卡情况。\n2. **恢复**：对于未完成的记录，点击可恢复进度。\n3. **删除**：长按记录可永久删除。
            </text>
          </view>
        </view>
      </view>

      <view class="footer-info">
        <text>System Status: Online</text>
        <text class="footer-sub">Designed by TaskLink Team</text>
      </view>
      
      <view style="height: 40rpx;"></view>

    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue';

const openIndex = ref(0);

const toggle = (index) => {
  if (openIndex.value === index) {
    openIndex.value = -1;
  } else {
    openIndex.value = index;
  }
};
</script>

<style lang="scss" scoped>
/* 1. 色彩变量 */
$color-bg: #F5F5F0;        /* 浅米色 */
$color-card: #FFFFFF;      /* 纯白 */
$color-primary: #4A6FA5;   /* 莫兰迪蓝 */
$color-text-main: #2C3E50; /* 深灰 */
$color-text-sub: #95A5A6;  /* 浅灰 */
$color-line: #E0E0E0;

page { 
  background-color: $color-bg; 
  height: 100vh;
  font-family: 'Inter', -apple-system, Helvetica, sans-serif;
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 2. 头部 */
.header-section {
  padding: 100rpx 40rpx 60rpx;
  background: $color-bg;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 48rpx;
  font-weight: 700;
  color: $color-text-main;
  display: block;
  margin-bottom: 8rpx;
}

.page-subtitle {
  font-size: 24rpx;
  color: $color-text-sub;
  letter-spacing: 1px;
}

.logo-box {
  width: 80rpx;
  height: 80rpx;
  background: $color-card;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.05);
}

.logo-text {
  font-size: 40rpx;
  font-weight: 700;
  color: $color-primary;
}

/* 3. 内容区 */
.content-scroll {
  flex: 1;
  height: 0;
  padding: 0 40rpx;
  box-sizing: border-box;
}

.section-header {
  display: flex;
  align-items: center;
  margin: 40rpx 0 24rpx;
}

.section-dot {
  width: 8rpx;
  height: 24rpx;
  background: $color-primary;
  border-radius: 4rpx;
  margin-right: 16rpx;
}
.section-dot.purple { background: #9FA8DA; }

.section-title {
  font-size: 24rpx;
  font-weight: 700;
  color: $color-text-sub;
  letter-spacing: 1px;
}

/* FAQ 列表 */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.faq-card {
  background: $color-card;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.02);
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.faq-card.expanded {
  box-shadow: 0 10rpx 30rpx rgba(74, 111, 165, 0.08);
  border-color: rgba(74, 111, 165, 0.1);
}

.card-header {
  padding: 30rpx;
  display: flex;
  align-items: center;
}

.q-badge {
  background: #F0F2F5;
  color: $color-text-sub;
  font-size: 20rpx;
  font-weight: 700;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  margin-right: 20rpx;
}

.faq-card.expanded .q-badge {
  background: rgba(74, 111, 165, 0.1);
  color: $color-primary;
}

.q-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: 600;
  color: $color-text-main;
}

.arrow-icon {
  font-size: 20rpx;
  color: #CFD8DC;
  transition: transform 0.3s;
}

.faq-card.expanded .arrow-icon {
  transform: rotate(180deg);
  color: $color-primary;
}

.card-body {
  padding: 0 30rpx 40rpx 30rpx;
  /* 增加淡入动画 */
  animation: fadeIn 0.4s ease-out;
}

.answer-text {
  font-size: 26rpx;
  color: #546E7A;
  line-height: 1.8; /* 优化中文行高 */
}

.highlight {
  color: $color-primary;
  font-weight: 600;
  margin: 0 4rpx;
}

/* 评分指南说明 */
.rating-guide {
  background: #FAFAFA;
  padding: 24rpx;
  border-radius: 12rpx;
}

.rate-row {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.rate-tag {
  font-size: 20rpx;
  font-weight: 700;
  color: #FFF;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  width: 80rpx;
  text-align: center;
  margin-right: 20rpx;
}

.rate-0 { background: #EF5350; } 
.rate-3 { background: #FFCA28; } 
.rate-4 { background: #42A5F5; } 
.rate-5 { background: #66BB6A; } 

.rate-desc {
  font-size: 24rpx;
  color: $color-text-main;
}

.tip-text {
  font-size: 20rpx;
  color: $color-text-sub;
  margin-top: 10rpx;
  display: block;
}

/* 底部脚注补全 */
.footer-info {
  padding: 80rpx 0 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.footer-info text {
  font-size: 22rpx;
  color: #B0BEC5;
  font-weight: 500;
  letter-spacing: 1px;
}

.footer-sub {
  margin-top: 8rpx;
  opacity: 0.7;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10rpx); }
  to { opacity: 1; transform: translateY(0); }
}
</style>