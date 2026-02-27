# 原生宠物系统使用指南

## 概述

这是一个完全原生的宠物系统，使用纯 CSS 动画和 SVG 绘制，无需任何第三方库。系统设计模块化，易于扩展和升级。

## 核心特性

- ✅ **纯原生实现**：使用 CSS 动画 + SVG，无第三方依赖
- ✅ **模块化设计**：状态管理和组件分离，易于维护
- ✅ **多种状态**：支持 idle、happy、sad、eating、sleeping、working、celebrating
- ✅ **情绪系统**：normal、excited、tired、sad
- ✅ **经验值系统**：完成任务可获得经验，升级有庆祝动画
- ✅ **事件响应**：自动响应应用内事件（完成任务、创建计划等）

## 文件结构

```
composables/
  └── usePet.ts          # 宠物状态管理 Composable

components/
  └── NativePet.vue       # 宠物组件（SVG + CSS 动画）
```

## 快速开始

### 1. 在页面中使用宠物组件

```vue
<template>
  <view class="container">
    <!-- 添加宠物组件 -->
    <NativePet :show-exp-bar="true" :show-status="false" />
    
    <!-- 其他内容 -->
  </view>
</template>

<script setup>
import NativePet from '@/components/NativePet.vue'
</script>
```

### 2. 在事件中触发宠物响应

```vue
<script setup>
import { usePet } from '@/composables/usePet'

const { onTaskCompleted, onPlanCreated, onVocabLearned } = usePet()

// 完成任务时
const completeTask = () => {
  // ... 你的业务逻辑
  onTaskCompleted() // 触发宠物响应
}

// 创建计划时
const createPlan = () => {
  // ... 你的业务逻辑
  onPlanCreated() // 触发宠物响应
}
</script>
```

## API 文档

### usePet() Composable

#### 状态

- `petConfig`: 宠物配置对象（响应式）
  - `name`: 宠物名称
  - `level`: 等级
  - `exp`: 当前经验值
  - `mood`: 情绪（normal | excited | tired | sad）
  - `state`: 状态（idle | happy | sad | eating | sleeping | working | celebrating）

- `expToNextLevel`: 升级所需经验值（计算属性）
- `expProgress`: 经验值进度百分比（计算属性）

#### 方法

- `addExp(amount: number)`: 添加经验值
- `triggerState(state: PetState, duration?: number)`: 触发临时状态
- `setMood(mood: PetMood)`: 设置情绪
- `setName(name: string)`: 设置宠物名称

#### 事件响应方法

- `onTaskCompleted()`: 任务完成时调用（+10 经验，触发 happy 状态）
- `onPlanCreated()`: 创建计划时调用（+5 经验，触发 happy 状态）
- `onPlanArchived()`: 计划归档时调用（+20 经验，触发 celebrating 状态）
- `onVocabLearned()`: 学习单词时调用（+3 经验，触发 happy 状态）

### NativePet 组件

#### Props

- `size?: 'small' | 'medium' | 'large'` - 宠物大小（默认：medium）
- `showExpBar?: boolean` - 是否显示经验条（默认：true）
- `showStatus?: boolean` - 是否显示状态文本（默认：false）

## 状态说明

### 宠物状态 (PetState)

- `idle`: 待机状态，默认呼吸动画
- `happy`: 开心状态，弹跳动画
- `sad`: 难过状态，表情变化
- `eating`: 进食状态，头部移动动画
- `sleeping`: 睡觉状态，呼吸动画，眼睛闭合
- `working`: 工作状态，点头动画
- `celebrating`: 庆祝状态，跳跃和缩放动画

### 情绪 (PetMood)

- `normal`: 正常情绪，默认蓝色
- `excited`: 兴奋情绪，颜色变亮（珊瑚橙）
- `tired`: 疲惫情绪，透明度降低
- `sad`: 悲伤情绪，颜色变灰

## 扩展指南

### 添加新的状态

1. 在 `usePet.ts` 中添加新的状态类型：
```typescript
export type PetState = 'idle' | 'happy' | 'newState'
```

2. 在 `NativePet.vue` 中添加对应的 CSS 动画：
```scss
.pet-newState {
  .pet-head {
    animation: newStateAnimation 1s ease-in-out infinite;
  }
}

@keyframes newStateAnimation {
  // 定义动画
}
```

### 添加新的事件响应

在 `usePet.ts` 中添加新方法：

```typescript
const onNewEvent = () => {
  addExp(15)
  triggerState('happy', 2000)
  petConfig.value.mood = 'excited'
  savePetConfig()
}
```

### 自定义宠物外观

修改 `NativePet.vue` 中的 SVG 部分，可以：
- 改变形状（使用不同的 SVG 元素）
- 改变颜色（通过 `bodyColor` 计算属性）
- 添加装饰元素（如星星、光环等）

## 已集成页面

- ✅ `pages/index/index.vue` - 首页显示宠物
- ✅ `pages/plan/detail.vue` - 完成任务时触发响应
- ✅ `pages/add/add.vue` - 创建计划时触发响应
- ✅ `pages/vocab/training.vue` - 学习单词时触发响应

## 数据持久化

宠物配置会自动保存到本地存储（`uni.setStorageSync('petConfig', ...)`），包括：
- 名称
- 等级
- 经验值
- 情绪

状态（state）是临时的，不会持久化。

## 性能优化

- 使用 CSS 动画而非 JavaScript 动画，性能更好
- SVG 矢量图形，任意缩放不失真
- 状态管理使用 Vue 的响应式系统，自动优化更新

## 后续升级建议

1. **宠物皮肤系统**：添加多种外观选择
2. **宠物对话**：根据状态显示不同的提示文字
3. **成就系统**：完成特定任务解锁成就
4. **宠物商店**：使用经验值购买装饰品
5. **多宠物支持**：允许用户拥有多个宠物
6. **社交功能**：查看好友的宠物状态

## 注意事项

- 宠物状态是全局共享的，所有页面使用同一个宠物实例
- 经验值和等级会持久化保存
- 临时状态（如 celebrating）会在指定时间后自动恢复
- 建议在关键事件处调用响应方法，避免过度触发
