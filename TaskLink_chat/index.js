require('dotenv').config();

const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const mysql = require('mysql2/promise');

// --- 1. 初始化应用 ---
const app = express();
const server = http.createServer(app);

// --- 2. 数据库连接池 ---
const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'root',
    database: process.env.DB_NAME || 'tasklink',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// --- 3. 配置中间件 ---
app.use(cors());
app.use(express.json());

// --- 4. 配置 Socket.IO ---
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// --- 5. Socket.IO 核心业务 ---
io.on('connection', (socket) => {
    console.log('🟢 新用户连接:', socket.id);

    // io.engine.clientsCount 可以获取当前连接数
    const count = io.engine.clientsCount;
    io.emit('update_online_count', count);

    // 监听：加入聊天
    socket.on('join', (userId) => {
        socket.join(`user_${userId}`);
    });

    // 🔥🔥 核心修复部分开始 🔥🔥
    // 监听：发送消息
    socket.on('send_message', async (data) => {
        console.log(`📩 收到消息:`, data);

        // 获取消息类型，如果没有传则默认为 'text'
        const msgType = data.type || 'text';

        // 1. 广播 (修复：必须把 type 传给对方，否则对方实时看不到图片)
        io.emit('new_message', {
            id: Date.now(),
            user_id: data.user_id,
            content: data.content,
            type: msgType,          // 👈 关键修复：透传类型
            username: data.username,
            avatar: data.avatar,
            created_at: new Date()
        });

        // 2. 存库 (修复：存入真实的 msgType，而不是写死 'text')
        try {
            const sql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
            // 👇 这里把原来的 'text' 改成了 msgType
            await pool.execute(sql, [data.user_id, data.content, msgType]);
            console.log('✅ 消息已存库, 类型:', msgType);
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
        }
    });
    // 🔥🔥 核心修复部分结束 🔥🔥

    socket.on('disconnect', () => {
        console.log('🔴 用户断开:', socket.id);
        io.emit('update_online_count', io.engine.clientsCount);
    });
});

// --- 6. 启动服务器 ---
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🚀 聊天服务器运行在: http://localhost:${PORT}`);
});