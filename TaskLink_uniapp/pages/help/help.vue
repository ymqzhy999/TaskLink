<template>
  <view class="container dark-theme">
    <view class="cyber-bg"></view>

    <view class="header">
      <text class="title">OPERATIONAL GUIDE</text>
      <text class="subtitle">TaskLink System v1.5</text>
    </view>

    <scroll-view scroll-y class="content-area">
      
      <view class="section-title">CORE MODULE: NEURAL TRAINING</view>
      
      <view class="faq-item" :class="{ open: openIndex === 0 }" @click="toggle(0)">
        <view class="faq-question">
          <text class="q-icon">Q1</text>
          <text class="q-text">如何开始每日单词训练？</text>
          <text class="arrow">▼</text>
        </view>
        <view class="faq-answer">
          <text>点击首页的 [NEURAL TRAINING] 卡片即可接入神经连接。系统会根据 SM-2 记忆算法，自动为您推送 **15个** 待复习或新学习的单词。</text>
        </view>
      </view>

      <view class="faq-item" :class="{ open: openIndex === 1 }" @click="toggle(1)">
        <view class="faq-question">
          <text class="q-icon">Q2</text>
          <text class="q-text">0/3/4/5 四个评分代表什么？</text>
          <text class="arrow">▼</text>
        </view>
        <view class="faq-answer">
          <view class="rating-explain">
            <text class="r-row"><text class="r-tag r0">0 忘记</text> 完全没印象，需要立即重新学习。</text>
            <text class="r-row"><text class="r-tag r3">3 模糊</text> 记得一点，但不确定或拼写错误。</text>
            <text class="r-row"><text class="r-tag r4">4 认识</text> 看到能认出，但需要思考一下。</text>
            <text class="r-row"><text class="r-tag r5">5 精通</text> 看到瞬间反应出意思，秒杀。</text>
            <text class="r-tip">* 评分直接影响算法对下次复习时间的安排，请诚实选择。</text>
          </view>
        </view>
      </view>

      <view class="faq-item" :class="{ open: openIndex === 2 }" @click="toggle(2)">
        <view class="faq-question">
          <text class="q-icon">Q3</text>
          <text class="q-text">没背完可以中途退出吗？(保存功能)</text>
          <text class="arrow">▼</text>
        </view>
        <view class="faq-answer">
          <text>当然。如果 15 个单词没背完需要离开，请点击顶部导航栏中间的 <text class="highlight">💾 SAVE</text> 按钮。\n\n系统会将您当前已完成的进度保存到 **历史球 (History Log)** 中。下次回来时，您可以恢复进度继续训练。</text>
        </view>
      </view>

      <view class="faq-item" :class="{ open: openIndex === 3 }" @click="toggle(3)">
        <view class="faq-question">
          <text class="q-icon">Q4</text>
          <text class="q-text">右下角的“历史球”是做什么的？</text>
          <text class="arrow">▼</text>
        </view>
        <view class="faq-answer">
          <text>历史球 (📜) 是您的训练日志中心：\n\n1. **查看记录**：点击展开，查看过去所有的打卡记录。\n2. **恢复进度**：点击某条 "SAVED" 状态的记录，可以进入详情页查看那次背了哪些词。\n3. **删除记录**：长按某条记录，可以将其从数据库中永久抹除。</text>
        </view>
      </view>

      <view class="section-title">DATABASE & TOOLS</view>

      <view class="faq-item" :class="{ open: openIndex === 4 }" @click="toggle(4)">
        <view class="faq-question">
          <text class="q-icon">Q5</text>
          <text class="q-text">如何使用词库 (Vocabulary)？</text>
          <text class="arrow">▼</text>
        </view>
        <view class="faq-answer">
          <text>词库包含所有等级的单词数据。\n\n• **搜索**：顶部输入框支持中/英文模糊搜索。\n• **发音**：点击任意单词行，即可播放真人发音。\n• **筛选**：支持按等级 (Level)、首字母 (A-Z) 和 困难模式 (Hard Mode) 筛选。</text>
        </view>
      </view>

      

      <view class="footer-note">
        SYSTEM STATUS: ONLINE
        <br>Designed by Administrator
      </view>

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

<style scoped>
page { background-color: #050505; color: #00f3ff; font-family: 'Courier New', monospace; height: 100vh; overflow: hidden; }
.container { height: 100%; display: flex; flex-direction: column; }
.cyber-bg { position: fixed; width: 100%; height: 100%; background: radial-gradient(circle, #111 0%, #000 100%); z-index: -1; }
.header { padding: 60rpx 40rpx; border-bottom: 2px solid #00f3ff; background: rgba(0, 243, 255, 0.05); }
.title { font-size: 40rpx; font-weight: bold; color: #fff; letter-spacing: 4rpx; display: block; }
.subtitle { font-size: 24rpx; color: #00f3ff; opacity: 0.7; margin-top: 10rpx; display: block; }
.content-area { flex: 1; padding: 30rpx; box-sizing: border-box; }
.section-title { font-size: 24rpx; color: #666; margin: 40rpx 0 20rpx; font-weight: bold; padding-left: 10rpx; border-left: 4rpx solid #666; }
.faq-item { background: #111; margin-bottom: 20rpx; border: 1px solid #333; border-radius: 8rpx; overflow: hidden; transition: all 0.3s; }
.faq-item.open { border-color: #00f3ff; box-shadow: 0 0 15rpx rgba(0, 243, 255, 0.1); }
.faq-question { padding: 30rpx; display: flex; align-items: center; justify-content: space-between; background: #161616; }
.q-icon { background: #333; color: #fff; font-size: 20rpx; padding: 4rpx 10rpx; border-radius: 4rpx; margin-right: 20rpx; }
.faq-item.open .q-icon { background: #00f3ff; color: #000; }
.q-text { flex: 1; font-size: 28rpx; color: #eee; font-weight: bold; }
.arrow { color: #666; font-size: 24rpx; transition: transform 0.3s; }
.faq-item.open .arrow { transform: rotate(180deg); color: #00f3ff; }
.faq-answer { height: 0; overflow: hidden; background: #0a0a0a; transition: height 0.3s; }
.faq-item.open .faq-answer { height: auto; padding: 30rpx; border-top: 1px dashed #333; }
.faq-answer text { font-size: 26rpx; color: #aaa; line-height: 1.6; display: block; }
.rating-explain { display: flex; flex-direction: column; gap: 15rpx; margin-top: 10rpx; }
.r-row { font-size: 24rpx; color: #ccc; }
.r-tag { font-size: 20rpx; padding: 2rpx 8rpx; border-radius: 4rpx; color: #000; font-weight: bold; margin-right: 10rpx; }
.r0 { background: #ff003c; }
.r3 { background: #ffaa00; }
.r4 { background: #00f3ff; }
.r5 { background: #00ff9d; }
.r-tip { font-size: 20rpx; color: #666; margin-top: 10rpx; font-style: italic; }
.highlight { color: #ffaa00; font-weight: bold; }
.footer-note { text-align: center; color: #333; font-size: 20rpx; margin: 60rpx 0; line-height: 1.5; }
</style>