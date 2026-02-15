
---

# TaskLink | 英语单词记忆与战术规划系统

TaskLink 是一款集成了科学记忆算法与 AI 辅助决策的英语学习工具。项目采用前后端分离架构，通过算法优化复习周期，并利用大语言模型辅助学习规划。(可以直接下载apk文件，后端部署在云服务器上，根据你对单词的掌握程度，动态计算最优复习间隔，帮你在即将遗忘前复习，实现高效、持久的单词记忆。邀请码：ALN6YS,O4H5TG,3W58AP,91UPJG )

## 📸 核心界面展示
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_1.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_2.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_3.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_4.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_5.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_6.png" width="400" height="570" alt="界面截图">
<img src="https://raw.githubusercontent.com/ymqzhy999/TaskLink/main/docs/images/img_7.png" width="400" height="570" alt="界面截图">
## 🏗️ 系统架构 (Architecture)

项目由三个核心模块组成，实现了业务逻辑、实时通信与展现层的解耦：

* **后端大脑 (Python Flask)**：
* **核心逻辑**：实现 SM-2 间隔重复算法，动态计算 `Interval`（间隔）和 `Easiness Factor`（简易度因子）。
* **AI 集成**：对接 DeepSeek API，通过结构化 Prompt 将模糊目标转化为 JSON 格式的任务节点。
* **数据管理**：基于 SQLAlchemy 管理用户进度、20,000+ 词库及训练日志。


* **通信塔 (Node.js)**：
* **实时交互**：基于 Socket.IO 驱动广场聊天，实现毫秒级消息同步。
* **异步解耦**：独立于主业务逻辑，保障通讯的高并发稳定性。


* **客户端 (Vue3 UniApp)**：
* **跨端适配**：全功能移动端体验，包含单词复习、计划生成、数据统计看板。



---

## 🧠 核心技术实现

### 1. SM-2 记忆算法逻辑

系统严格遵循 SuperMemo-2 算法公式：

* 用户对单词掌握度评分（0-5）后，系统自动修正 EF 值。
* **复习梯度**：针对不同评分（忘记、模糊、认识、精通）设定不同的增长系数。
* **遗忘重置**：评分为“忘记”的单词将强制重置复习周期，确保记忆深度。

### 2. AI 战术解构 (AI Planner)

利用 **DeepSeek-Reasoner** 模型进行目标拆解：

* **模式识别**：自动根据天数判定“每日模式”或“阶段 Phase 模式”。
* **清单化输出**：强制 AI 生成包含执行步骤与验收标准的 Markdown 任务清单。

---

## 🚀 部署与运行

### 1. 环境准备

* **Python** 3.9+ / **Node.js** 16+ / **MySQL** 8.0+ / **HBuilderX**

### 2. 启动后端 (Flask)

```bash
cd TaskLink_backend
pip install -r requirements.txt
# 请在 .env 文件中配置 DEEPSEEK_API_KEY
python app.py

```

### 3. 启动聊天服务 (Node.js)

```bash
cd TaskLink_chat
npm install
node index.js

```

### 4. 运行前端

使用 HBuilderX 打开 `TaskLink_uniapp`，修改 API 路径后运行至真机或模拟器。

---

## 📄 更新记录 (Changelog)

* **v1.5**：**SM-2 算法深度实装**。支持困难单词筛选与复习周期动态计算。
* **v1.2**：**通讯协议优化**。新增邀请码注册机制与消息弹窗。
