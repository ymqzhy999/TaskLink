# ⚡ TaskLink | 赛博朋克风格任务与社交终端

![Project Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Style](https://img.shields.io/badge/Style-Cyberpunk-ff003c)
![Backend](https://img.shields.io/badge/Python-Flask-yellow)
![RealTime](https://img.shields.io/badge/Node.js-Socket.IO-green)

> **"规划你的数字生活，连接赛博空间。"**

TaskLink 是一款拥有 **极致赛博朋克 UI** 的个人任务管理应用。它集成了任务调度、AI 助手对话以及实时聊天广场功能。采用 **Python (业务)** + **Node.js (实时通信)** 的双塔架构设计。

---

## 🌟 核心功能 (Features)

### 📅 任务管理 (Task Core)
- **赛博 UI**：黑客终端风格界面，霓虹光效与毛玻璃质感。
- **任务调度**：支持设置精确执行时间、循环任务 (Loop Mode)。
- **多样化动作**：
  - `APP`：唤起指定应用。
  - `LINK`：打开 URL 链接。
  - `SCRIPT`：执行本地 Python 脚本（配合后端扩展）。

### 💬 聊天广场 (Chat Square)
- **实时通讯**：基于 **Node.js + Socket.IO** 的高并发聊天室。
- **即时广播**：所有在线用户可实时交流，支持历史消息回溯。
- **无感鉴权**：共享 Flask 登录状态，无需重复登录。

### 🤖 AI 终端 (AI Terminal)
- 内置与本地 LLM (如 Gemma:4b/Llama3) 对话的接口。
- 支持流式打字机效果，模拟与 AI 的即时通讯。

---

## 🏗️ 系统架构 (Architecture)

本项目采用前后端分离 + 微服务雏形架构：

```text
TaskLink/
├── TaskLink_backend/    # 🐍 [Python Flask] 
│   ├── 核心业务 API (登录/注册/任务增删改查)
│   ├── MySQL 数据库 ORM
│   └── Ollama AI 接口转发
│
├── TaskLink_chat/       # 🟢 [Node.js Express] (Coming Soon)
│   ├── Socket.IO 实时通讯服务端
│   └── 消息广播与持久化
│
├── TaskLink_uniapp/     # 📱 [Vue3 UniApp]
│   ├── 跨端前端 (H5/App)
│   └── 赛博朋克 UI 组件库
│
└── .gitignore           # Git 配置


adb tcpip 5555  开启端口 用于无线连接手机
adb shell ime set com.android.adbkeyboard/.AdbIM
adb shell am broadcast -a ADB_INPUT_TEXT --es msg "用qq给老己发送消息:老己你辛苦了"