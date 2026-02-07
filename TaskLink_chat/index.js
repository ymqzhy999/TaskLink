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

    // 监听：发送消息
    socket.on('send_message', async (data) => {
        console.log(`📩 收到消息:`, data); // 收到消息必须看到这行！

        // 1. 广播
        io.emit('new_message', {
            id: Date.now(),
            user_id: data.user_id,
            content: data.content,
            username: data.username,
            avatar: data.avatar,
            created_at: new Date()
        });

        // 2. 存库
        try {
            const sql = 'INSERT INTO chat_messages (user_id, content, msg_type, created_at) VALUES (?, ?, ?, NOW())';
            await pool.execute(sql, [data.user_id, data.content, 'text']);
            console.log('✅ 消息已存库');
        } catch (err) {
            console.error('❌ 消息存库失败:', err);
        }
    });

    socket.on('disconnect', () => {
        console.log('🔴 用户断开:', socket.id);
    });
    io.emit('update_online_count', io.engine.clientsCount);
});

// --- 6. 启动服务器 ---
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`🚀 聊天服务器运行在: http://localhost:${PORT}`);
});