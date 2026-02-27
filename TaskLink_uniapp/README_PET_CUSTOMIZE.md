# 宠物自定义功能使用指南

## 功能概述

用户可以通过点击宠物进入自定义页面，设计自己的专属宠物。系统支持：
1. **AI智能生成** - 通过描述让AI生成SVG代码
2. **导入SVG代码** - 直接粘贴SVG代码
3. **配置动画** - 为不同状态配置动态效果

## 数据库表结构

已创建 `user_pet_customizations` 表，包含以下字段：
- `id` - 主键
- `user_id` - 用户ID（外键关联users表）
- `pet_name` - 宠物名称
- `svg_content` - SVG代码内容（TEXT类型）
- `animation_config` - 动画配置（JSON格式）
- `is_active` - 是否激活
- `created_at` - 创建时间
- `updated_at` - 更新时间

## 使用流程

### 1. 进入自定义页面
- 在首页点击宠物组件，自动跳转到 `/pages/pet/customize`

### 2. AI生成宠物
1. 点击"AI智能生成"卡片
2. 在弹窗中输入描述，例如："一只可爱的小猫，圆圆的脑袋，大大的眼睛，蓝色的身体"
3. 点击"生成SVG"
4. 系统会自动调用后端AI接口生成SVG代码
5. 生成的SVG会自动添加动画类名

### 3. 导入SVG代码
1. 点击"导入SVG代码"卡片
2. 在文本框中粘贴你的SVG代码
3. 点击"导入并预览"
4. 系统会自动为SVG元素添加 `pet-anim-element` 类名，用于动画控制

### 4. 配置动画
1. 点击"配置动画"卡片
2. 为不同状态（idle、happy、sad、sleeping、working、celebrating）配置动画：
   - **动画类型**：bounce、rotate、scale、fade、slide、pulse、shake
   - **持续时间**：动画持续时间（毫秒）
   - **延迟**：动画延迟时间（毫秒）
3. 点击"应用配置"

### 5. 保存配置
1. 输入宠物名称（可选）
2. 点击"保存自定义宠物"
3. 配置会保存到数据库和本地存储

## 动画系统说明

### 动画类型
- **bounce** - 弹跳动画
- **rotate** - 旋转动画
- **scale** - 缩放动画
- **fade** - 淡入淡出
- **slide** - 滑动动画
- **pulse** - 脉冲动画
- **shake** - 震动动画

### 动画工作原理
1. 导入SVG时，系统会自动为SVG元素添加 `pet-anim-element` 类名
2. 根据宠物当前状态和动画配置，应用对应的CSS动画类
3. 动画通过CSS keyframes实现，性能优秀

### 状态与动画
- **idle** - 待机状态，默认使用bounce动画
- **happy** - 开心状态，默认使用pulse动画
- **sad** - 难过状态，默认使用fade动画
- **sleeping** - 睡觉状态，默认使用fade动画
- **working** - 工作状态，默认使用rotate动画
- **celebrating** - 庆祝状态，默认使用bounce动画

## 后端API接口

需要后端实现以下接口：

### 1. 获取用户自定义配置
```
GET /api/pet/customization
参数: { user_id: number }
返回: { code: 200, data: { svg_content, animation_config, pet_name, ... } }
```

### 2. 保存用户自定义配置
```
POST /api/pet/customization
参数: {
  user_id: number,
  pet_name: string,
  svg_content: string,
  animation_config: string (JSON字符串),
  is_active: number
}
返回: { code: 200, msg: '保存成功' }
```

### 3. 删除用户自定义配置（恢复默认）
```
DELETE /api/pet/customization
参数: { user_id: number }
返回: { code: 200, msg: '删除成功' }
```

### 4. AI生成SVG（可选）
```
POST /api/pet/generate-svg
参数: {
  prompt: string,
  user_id: number
}
返回: { code: 200, data: { svg_code: string } }
```

## 技术实现

### 文件结构
- `sqls/tasklink_user_pet_customizations.sql` - 数据库表结构
- `pages/pet/customize.vue` - 自定义编辑器页面
- `components/NativePet.vue` - 宠物组件（支持自定义SVG）
- `composables/usePet.js` - 宠物状态管理（支持自定义数据）

### 核心功能
1. **SVG渲染** - 使用 `v-html` 渲染自定义SVG
2. **动画系统** - 通过CSS类和keyframes实现动态效果
3. **数据持久化** - 同时保存到数据库和本地存储
4. **自动同步** - 组件挂载时自动从服务器加载最新配置

## 注意事项

1. **SVG格式要求**
   - SVG代码必须包含完整的 `<svg>` 标签
   - 建议使用 `viewBox` 属性而不是固定的宽高
   - SVG元素会自动添加 `pet-anim-element` 类名

2. **动画性能**
   - 使用CSS动画而非JavaScript动画，性能更好
   - 建议动画持续时间不要过长（1-3秒为宜）

3. **安全性**
   - SVG代码通过 `v-html` 渲染，需要注意XSS安全
   - 建议后端对SVG代码进行验证和清理

4. **兼容性**
   - 如果用户没有自定义配置，会显示默认宠物
   - 自定义SVG和默认SVG可以无缝切换

## 示例SVG代码

```svg
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="50" fill="#4A6FA5" />
  <circle cx="85" cy="90" r="8" fill="#2C3E50" />
  <circle cx="115" cy="90" r="8" fill="#2C3E50" />
  <path d="M 80 110 Q 100 130 120 110" stroke="#2C3E50" stroke-width="3" fill="none" />
</svg>
```

导入后，系统会自动添加类名：
```svg
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle class="pet-anim-element" cx="100" cy="100" r="50" fill="#4A6FA5" />
  <circle class="pet-anim-element" cx="85" cy="90" r="8" fill="#2C3E50" />
  <circle class="pet-anim-element" cx="115" cy="90" r="8" fill="#2C3E50" />
  <path class="pet-anim-element" d="M 80 110 Q 100 130 120 110" stroke="#2C3E50" stroke-width="3" fill="none" />
</svg>
```

## 未来扩展

1. **宠物商店** - 使用经验值购买预设宠物皮肤
2. **动画编辑器** - 可视化编辑动画参数
3. **多宠物支持** - 允许用户拥有多个宠物并切换
4. **宠物互动** - 宠物之间的互动动画
5. **表情系统** - 根据情绪自动切换表情
